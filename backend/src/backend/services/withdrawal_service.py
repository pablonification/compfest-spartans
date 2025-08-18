from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from bson import ObjectId

from ..db.mongo import ensure_connection
from ..core.config import get_settings


async def get_user_document(user_id: str) -> Optional[Dict[str, Any]]:
    db = await ensure_connection()
    users = db["users"]
    return await users.find_one({"_id": ObjectId(user_id)})


async def get_payout_method(user_id: str) -> Optional[Dict[str, Any]]:
    user = await get_user_document(user_id)
    return user.get("payout_method") if user else None


async def set_payout_method_once(user_id: str, method: Dict[str, Any]) -> Dict[str, Any]:
    db = await ensure_connection()
    users = db["users"]

    # Ensure it's one-time set
    existing = await users.find_one({"_id": ObjectId(user_id), "payout_method": {"$exists": True}})
    if existing:
        raise ValueError("Payout method already set and cannot be changed")

    method_to_set = {**method, "set_at": datetime.now(timezone.utc)}
    await users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"payout_method": method_to_set}},
        upsert=True,
    )
    return method_to_set


async def create_withdrawal_request(user_id: str, amount_points: int) -> Dict[str, Any]:
    settings = get_settings()
    min_points = settings.MIN_WITHDRAWAL_POINTS

    if amount_points < int(min_points):
        raise ValueError(f"Minimum withdrawal is {min_points} points")

    db = await ensure_connection()
    users = db["users"]
    withdrawals = db["withdrawals"]

    # Check payout method exists
    user_doc = await get_user_document(user_id)
    if not user_doc:
        raise ValueError("User not found")
    payout_method = user_doc.get("payout_method")
    if not payout_method:
        raise ValueError("Payout method not set")

    # Atomic-like guard: deduct only if sufficient points
    updated = await users.find_one_and_update(
        {"_id": ObjectId(user_id), "points": {"$gte": amount_points}},
        {"$inc": {"points": -amount_points}},
        return_document=True,
    )
    if not updated:
        raise ValueError("Insufficient points")

    doc = {
        "user_id": ObjectId(user_id),
        "amount_points": int(amount_points),
        "status": "pending",
        "created_at": datetime.now(timezone.utc),
        "processed_at": None,
        # Snapshot payout method for audit
        "method_type": payout_method.get("method_type"),
        "bank_code": payout_method.get("bank_code"),
        "bank_account_number": payout_method.get("bank_account_number"),
        "bank_account_name": payout_method.get("bank_account_name"),
        "ewallet_provider": payout_method.get("ewallet_provider"),
        "phone_number": payout_method.get("phone_number"),
    }
    result = await withdrawals.insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc


async def list_user_withdrawals(user_id: str, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
    db = await ensure_connection()
    withdrawals = db["withdrawals"]
    cursor = (
        withdrawals
        .find({"user_id": ObjectId(user_id)})
        .sort("created_at", -1)
        .skip(offset)
        .limit(limit)
    )
    items: List[Dict[str, Any]] = []
    async for item in cursor:
        items.append(item)
    return items


async def admin_list_withdrawals(status: Optional[str] = None, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
    db = await ensure_connection()
    withdrawals = db["withdrawals"]
    query: Dict[str, Any] = {}
    if status:
        query["status"] = status
    cursor = withdrawals.find(query).sort("created_at", 1).skip(offset).limit(limit)
    items: List[Dict[str, Any]] = []
    async for item in cursor:
        items.append(item)
    return items


async def admin_mark_completed(withdrawal_id: str) -> Optional[Dict[str, Any]]:
    db = await ensure_connection()
    withdrawals = db["withdrawals"]
    updated = await withdrawals.find_one_and_update(
        {"_id": ObjectId(withdrawal_id), "status": "pending"},
        {"$set": {"status": "completed", "processed_at": datetime.now(timezone.utc)}},
        return_document=True,
    )
    return updated


async def admin_reject_with_refund(withdrawal_id: str, admin_note: Optional[str] = None) -> Optional[Dict[str, Any]]:
    db = await ensure_connection()
    withdrawals = db["withdrawals"]
    users = db["users"]

    wd = await withdrawals.find_one({"_id": ObjectId(withdrawal_id)})
    if not wd or wd.get("status") != "pending":
        return None

    # Mark rejected
    await withdrawals.update_one(
        {"_id": ObjectId(withdrawal_id)},
        {"$set": {"status": "rejected", "processed_at": datetime.now(timezone.utc), "admin_note": admin_note}},
    )

    # Refund points
    await users.update_one(
        {"_id": wd["user_id"]},
        {"$inc": {"points": int(wd.get("amount_points", 0))}},
    )

    return await withdrawals.find_one({"_id": ObjectId(withdrawal_id)})


