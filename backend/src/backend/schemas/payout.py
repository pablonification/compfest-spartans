from __future__ import annotations

from datetime import datetime
from typing import ClassVar, Literal, Optional
from pydantic import BaseModel, Field, field_validator, model_validator
import re


class PayoutMethodRequest(BaseModel):
    method_type: Literal["bank", "ewallet"]
    bank_code: Optional[str] = None
    bank_account_number: Optional[str] = None
    bank_account_name: Optional[str] = None
    ewallet_provider: Optional[str] = None
    phone_number: Optional[str] = None

    ALLOWED_BANKS: ClassVar[list[str]] = [
        "BCA", "BNI", "BRI", "MANDIRI", "CIMB", "PERMATA", "BSI", "BTN", "BJB",
        "DANAMON", "OCBC", "MAYBANK", "BTPN", "MEGA", "PANIN", "BNC", "BANKJATIM",
    ]
    ALLOWED_EWALLETS: ClassVar[list[str]] = [
        "OVO", "GOPAY", "DANA", "SHOPEEPAY", "LINKAJA", "ISAKU", "SPAYLATER",
    ]

    @field_validator("bank_code")
    @classmethod
    def validate_bank_code(cls, v, info):
        values = info.data
        if values.get("method_type") == "bank":
            if not v or v.upper() not in cls.ALLOWED_BANKS:
                raise ValueError("Unsupported bank_code")
            return v.upper()
        return v

    @field_validator("bank_account_number")
    @classmethod
    def validate_bank_account_number(cls, v, info):
        if info.data.get("method_type") == "bank":
            if not v:
                raise ValueError("bank_account_number required for bank method")
            if not re.fullmatch(r"\d{8,20}", v):
                raise ValueError("bank_account_number must be 8-20 digits")
        return v

    @field_validator("bank_account_name")
    @classmethod
    def validate_bank_account_name(cls, v, info):
        if info.data.get("method_type") == "bank":
            if not v or not v.strip():
                raise ValueError("bank_account_name required for bank method")
            if len(v.strip()) > 100:
                raise ValueError("bank_account_name too long")
        return v

    @field_validator("ewallet_provider")
    @classmethod
    def validate_ewallet_provider(cls, v, info):
        if info.data.get("method_type") == "ewallet":
            if not v or v.upper() not in cls.ALLOWED_EWALLETS:
                raise ValueError("Unsupported ewallet_provider")
            return v.upper()
        return v

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, v, info):
        if info.data.get("method_type") == "ewallet":
            if not v:
                raise ValueError("phone_number required for ewallet method")
            # Accept +62, 62, or 0 prefix, followed by 8-13 digits
            if not re.fullmatch(r"(\+62|62|0)\d{8,13}", v):
                raise ValueError("Invalid Indonesian phone number format")
        return v

    @model_validator(mode="after")
    def ensure_fields_by_type(self):
        if self.method_type == "bank":
            # ewallet fields should not be set
            if self.ewallet_provider or self.phone_number:
                raise ValueError("Do not supply ewallet fields for bank method")
        if self.method_type == "ewallet":
            # bank fields should not be set
            if self.bank_code or self.bank_account_number or self.bank_account_name:
                raise ValueError("Do not supply bank fields for ewallet method")
        return self


class PayoutMethodResponse(BaseModel):
    method_type: Literal["bank", "ewallet"]
    bank_code: Optional[str] = None
    bank_account_number: Optional[str] = None
    bank_account_name: Optional[str] = None
    ewallet_provider: Optional[str] = None
    phone_number: Optional[str] = None
    set_at: Optional[datetime] = None


class WithdrawalCreateRequest(BaseModel):
    amount_points: int = Field(..., ge=1)


class WithdrawalResponse(BaseModel):
    id: str
    user_id: str
    amount_points: int
    status: Literal["pending", "completed", "rejected"]
    created_at: datetime
    processed_at: Optional[datetime] = None
    method_type: Literal["bank", "ewallet"]
    bank_code: Optional[str] = None
    bank_account_number: Optional[str] = None
    bank_account_name: Optional[str] = None
    ewallet_provider: Optional[str] = None
    phone_number: Optional[str] = None


class AdminMarkPaidRequest(BaseModel):
    admin_note: Optional[str] = None


