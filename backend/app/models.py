from datetime import datetime, date
from typing import Optional
from sqlmodel import SQLModel, Field, Relationship


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    password_hash: str
    name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Debtor(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    # personal
    name: str = Field(index=True)
    phone: str = Field(index=True)
    national_id: Optional[str] = None
    line_id: Optional[str] = None
    address: Optional[str] = None

    # loan
    principal: float
    interest_rate: float           # percent per month
    interest_type: str = "flat"    # flat | compound | custom
    installments: int = 1
    start_date: date
    first_due_date: Optional[date] = None   # if None, defaults to start_date + 1 month

    # payment channel (เจ้าหนี้รับเงินคืนเข้าบัญชีไหน)
    bank: Optional[str] = None
    account_no: Optional[str] = None

    # source of funds (เจ้าหนี้เอาเงินจากไหนมาปล่อยกู้)
    funding_source: Optional[str] = None

    # state
    status: str = "active"         # active | near_due | overdue | closed
    notes: Optional[str] = None
    rollover_from_id: Optional[int] = Field(default=None, foreign_key="debtor.id")
    rolled_amount: Optional[float] = None  # if this is a rollover, the original principal

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    payments: list["Payment"] = Relationship(back_populates="debtor")
    attachments: list["Attachment"] = Relationship(back_populates="debtor")


class Payment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    debtor_id: int = Field(foreign_key="debtor.id", index=True)
    amount: float
    paid_date: date
    installment_no: Optional[int] = None
    status: str = "paid"   # paid | late
    note: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    debtor: Optional[Debtor] = Relationship(back_populates="payments")


class Attachment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    debtor_id: int = Field(foreign_key="debtor.id", index=True)
    category: str          # contract | id_card | slip | collateral
    filename: str          # stored filename
    original_name: str
    size: int
    mime_type: str
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)

    debtor: Optional[Debtor] = Relationship(back_populates="attachments")
