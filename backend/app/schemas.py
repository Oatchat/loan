from datetime import datetime, date
from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator


# ─────────────── Auth ───────────────
class LoginIn(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"


class UserOut(BaseModel):
    id: int
    username: str
    name: str

    class Config:
        from_attributes = True


# ─────────────── Debtor ───────────────
InterestType = Literal["flat", "compound", "custom"]
Status = Literal["active", "near_due", "overdue", "closed"]


class DebtorBase(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    phone: str = Field(pattern=r"^0[6-9]\d{8}$")
    national_id: Optional[str] = Field(default=None, max_length=13)
    line_id: Optional[str] = None
    address: Optional[str] = None

    principal: float = Field(gt=0, le=10_000_000)
    interest_rate: float = Field(ge=0, le=30)
    interest_type: InterestType = "flat"
    installments: int = Field(default=1, ge=1, le=360)
    start_date: date
    first_due_date: Optional[date] = None
    is_open_ended: bool = False

    bank: Optional[str] = None
    account_no: Optional[str] = None
    funding_source: Optional[str] = Field(default=None, max_length=200)

    notes: Optional[str] = Field(default=None, max_length=500)


class DebtorCreate(DebtorBase):
    pass


class DebtorUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = Field(default=None, pattern=r"^0[6-9]\d{8}$")
    national_id: Optional[str] = None
    line_id: Optional[str] = None
    address: Optional[str] = None
    principal: Optional[float] = Field(default=None, gt=0, le=10_000_000)
    interest_rate: Optional[float] = Field(default=None, ge=0, le=30)
    interest_type: Optional[InterestType] = None
    installments: Optional[int] = Field(default=None, ge=1, le=360)
    start_date: Optional[date] = None
    first_due_date: Optional[date] = None
    bank: Optional[str] = None
    account_no: Optional[str] = None
    funding_source: Optional[str] = Field(default=None, max_length=200)
    status: Optional[Status] = None
    notes: Optional[str] = Field(default=None, max_length=500)
    is_open_ended: Optional[bool] = None


class AttachmentOut(BaseModel):
    id: int
    category: str
    filename: str
    original_name: str
    size: int
    mime_type: str
    uploaded_at: datetime

    class Config:
        from_attributes = True


class PaymentOut(BaseModel):
    id: int
    amount: float
    paid_date: date
    installment_no: Optional[int]
    is_interest_only: bool = False
    status: str
    note: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class DebtorOut(DebtorBase):
    id: int
    status: Status
    created_at: datetime
    updated_at: datetime
    rollover_from_id: Optional[int] = None
    rolled_amount: Optional[float] = None

    # computed
    total_paid: float = 0.0
    balance: float = 0.0
    next_due_date: Optional[date] = None
    days_until_due: Optional[int] = None
    payments: list[PaymentOut] = []
    attachments: list[AttachmentOut] = []

    class Config:
        from_attributes = True


# ─────────────── Payment ───────────────
class PaymentCreate(BaseModel):
    amount: float = Field(gt=0)
    paid_date: date
    installment_no: Optional[int] = None
    is_interest_only: bool = False
    note: Optional[str] = None


# ─────────────── Rollover ───────────────
class RolloverIn(BaseModel):
    new_principal: float = Field(gt=0)
    interest_rate: float = Field(ge=0, le=30)
    installments: int = Field(ge=1, le=360)
    start_date: date
    note: Optional[str] = None


# ─────────────── Reports ───────────────
class ReportSummary(BaseModel):
    total_debtors: int
    total_principal: float
    total_interest_earned: float
    total_paid: float
    overdue_count: int
    closed_count: int
    near_due_count: int
    active_count: int


class MonthlyBucket(BaseModel):
    month: str
    issued: float
    collected: float
    interest: float


class ReportDetailed(BaseModel):
    summary: ReportSummary
    monthly: list[MonthlyBucket]
    status_breakdown: dict[str, int]


# ─────────────── Interest Calc ───────────────
class InterestCalcIn(BaseModel):
    principal: float = Field(gt=0)
    rate_per_month: float = Field(ge=0, le=30)
    months: int = Field(ge=1, le=360)
    interest_type: InterestType = "flat"
    first_due_date: Optional[date] = None


class ScheduleRow(BaseModel):
    month: int
    due_date: date
    payment: float
    principal: float
    interest: float
    balance: float


class InterestCalcOut(BaseModel):
    total_interest: float
    monthly_payment: float
    total_payment: float
    schedule: list[ScheduleRow]


# resolve forward refs
TokenOut.model_rebuild()
