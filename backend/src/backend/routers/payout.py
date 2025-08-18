from __future__ import annotations

from typing import List, Optional

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..routers.auth import verify_token
from ..schemas.payout import (
    AdminMarkPaidRequest,
    PayoutMethodRequest,
    PayoutMethodResponse,
    WithdrawalCreateRequest,
    WithdrawalResponse,
)
from ..services.withdrawal_service import (
    admin_list_withdrawals,
    admin_mark_completed,
    admin_reject_with_refund,
    create_withdrawal_request,
    get_payout_method,
    list_user_withdrawals,
    set_payout_method_once,
)
from fastapi.responses import StreamingResponse
import csv
from io import StringIO


router = APIRouter(prefix="/payout", tags=["payout"])


@router.get("/method", response_model=Optional[PayoutMethodResponse])
async def get_method(payload: dict = Depends(verify_token)):
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid user token")
    method = await get_payout_method(user_id)
    return method


@router.post("/method", response_model=PayoutMethodResponse, status_code=status.HTTP_201_CREATED)
async def set_method_once(body: PayoutMethodRequest, payload: dict = Depends(verify_token)):
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid user token")

    # Field-level validation handled by schema; double-check completeness
    if body.method_type == "bank":
        if not (body.bank_code and body.bank_account_number and body.bank_account_name):
            raise HTTPException(status_code=400, detail="Bank details incomplete")
    else:
        if not (body.ewallet_provider and body.phone_number):
            raise HTTPException(status_code=400, detail="E-wallet details incomplete")

    try:
        saved = await set_payout_method_once(user_id, body.model_dump())
        return saved
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/metadata")
async def payout_metadata():
    from ..core.config import get_settings
    settings = get_settings()
    return {
        "banks": PayoutMethodRequest.ALLOWED_BANKS,
        "ewallets": PayoutMethodRequest.ALLOWED_EWALLETS,
        "min_withdrawal_points": int(getattr(settings, "MIN_WITHDRAWAL_POINTS", 0) or 0),
    }


@router.post("/withdrawals", response_model=WithdrawalResponse, status_code=status.HTTP_201_CREATED)
async def request_withdrawal(body: WithdrawalCreateRequest, payload: dict = Depends(verify_token)):
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid user token")
    try:
        doc = await create_withdrawal_request(user_id, body.amount_points)
        return _to_withdrawal_response(doc)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/withdrawals", response_model=List[WithdrawalResponse])
async def list_withdrawals(limit: int = Query(default=50, ge=1, le=200), offset: int = Query(default=0, ge=0), payload: dict = Depends(verify_token)):
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid user token")
    docs = await list_user_withdrawals(user_id, limit, offset)
    return [_to_withdrawal_response(d) for d in docs]


# --- Admin endpoints ---

def _is_admin(payload: dict) -> bool:
    # naive: treat configured admin email list
    from ..core.config import get_settings
    settings = get_settings()
    admin_emails = getattr(settings, "ADMIN_EMAILS", "")
    email = payload.get("email")
    return bool(email and any(e.strip().lower() == email.lower() for e in admin_emails.split(",") if e.strip()))


@router.get("/admin/withdrawals", response_model=List[WithdrawalResponse])
async def admin_list(status: Optional[str] = Query(default=None), limit: int = Query(default=100, ge=1, le=500), offset: int = Query(default=0, ge=0), payload: dict = Depends(verify_token)):
    if not _is_admin(payload):
        raise HTTPException(status_code=403, detail="Admin only")
    docs = await admin_list_withdrawals(status, limit, offset)
    return [_to_withdrawal_response(d) for d in docs]


@router.post("/admin/withdrawals/{withdrawal_id}/complete", response_model=WithdrawalResponse)
async def admin_complete(withdrawal_id: str, payload: dict = Depends(verify_token)):
    if not _is_admin(payload):
        raise HTTPException(status_code=403, detail="Admin only")
    updated = await admin_mark_completed(withdrawal_id)
    if not updated:
        raise HTTPException(status_code=404, detail="Not found or not pending")
    return _to_withdrawal_response(updated)


@router.post("/admin/withdrawals/{withdrawal_id}/reject", response_model=WithdrawalResponse)
async def admin_reject(withdrawal_id: str, body: AdminMarkPaidRequest, payload: dict = Depends(verify_token)):
    if not _is_admin(payload):
        raise HTTPException(status_code=403, detail="Admin only")
    updated = await admin_reject_with_refund(withdrawal_id, body.admin_note)
    if not updated:
        raise HTTPException(status_code=404, detail="Not found or not pending")
    return _to_withdrawal_response(updated)


@router.get("/admin/withdrawals/export.csv")
async def admin_export_csv(status: Optional[str] = Query(default=None), payload: dict = Depends(verify_token)):
    if not _is_admin(payload):
        raise HTTPException(status_code=403, detail="Admin only")
    docs = await admin_list_withdrawals(status, limit=10000, offset=0)
    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow([
        "id", "user_id", "amount_points", "status", "created_at", "processed_at",
        "method_type", "bank_code", "bank_account_number", "bank_account_name", "ewallet_provider", "phone_number",
    ])
    for d in docs:
        writer.writerow([
            str(d.get("_id")),
            str(d.get("user_id")),
            int(d.get("amount_points", 0)),
            d.get("status"),
            d.get("created_at"),
            d.get("processed_at"),
            d.get("method_type"),
            d.get("bank_code"),
            d.get("bank_account_number"),
            d.get("bank_account_name"),
            d.get("ewallet_provider"),
            d.get("phone_number"),
        ])
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="text/csv", headers={
        "Content-Disposition": "attachment; filename=withdrawals_export.csv"
    })


def _to_withdrawal_response(doc: dict) -> WithdrawalResponse:
    return WithdrawalResponse(
        id=str(doc["_id"]),
        user_id=str(doc["user_id"]),
        amount_points=int(doc["amount_points"]),
        status=doc["status"],
        created_at=doc["created_at"],
        processed_at=doc.get("processed_at"),
        method_type=doc.get("method_type"),
        bank_code=doc.get("bank_code"),
        bank_account_number=doc.get("bank_account_number"),
        bank_account_name=doc.get("bank_account_name"),
        ewallet_provider=doc.get("ewallet_provider"),
        phone_number=doc.get("phone_number"),
    )


