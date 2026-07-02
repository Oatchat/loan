from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select

from ..db import get_session
from ..deps import get_current_user
from ..interest import calc_schedule
from ..models import Debtor, Payment, User
from ..schemas import (
    DebtorCreate, DebtorOut, DebtorUpdate, InterestCalcIn, InterestCalcOut,
    PaymentOut, AttachmentOut, RolloverIn,
)


router = APIRouter(prefix="/debtors", tags=["debtors"])


def _enrich(d: Debtor) -> DebtorOut:
    payments = list(d.payments or [])
    total_paid = sum(p.amount for p in payments)
    # Interest-only payments cover accrued interest without reducing principal,
    # so they must NOT count toward the outstanding balance.
    balance_paid = sum(p.amount for p in payments if not getattr(p, "is_interest_only", False))
    today = date.today()
    is_open = bool(getattr(d, "is_open_ended", False))

    if is_open:
        # Open-ended: interest accrues per elapsed month (flat-style).
        months_elapsed = max(0, (today.year - d.start_date.year) * 12 + (today.month - d.start_date.month))
        accrued_interest = d.principal * (d.interest_rate / 100.0) * months_elapsed
        total_payment = d.principal + accrued_interest
        balance = total_payment - balance_paid
        next_due = None
        days_until = None

        derived = d.status
        if d.status != "closed":
            derived = "closed" if balance <= 0 else "active"
    else:
        sched = calc_schedule(
            d.principal, d.interest_rate, d.installments, d.interest_type,
            d.start_date, d.first_due_date,
        )
        balance = sched.total_payment - balance_paid
        next_due = None
        days_until = None
        paid_count = len([p for p in payments if p.status == "paid" and not getattr(p, "is_interest_only", False)])
        if paid_count < d.installments:
            idx = paid_count  # next unpaid
            next_due = sched.schedule[idx].due_date if idx < len(sched.schedule) else None
            if next_due:
                days_until = (next_due - today).days

        # derive status (computed; persisted status used if closed)
        derived = d.status
        if d.status != "closed":
            if balance <= 0:
                derived = "closed"
            elif next_due and (next_due - today).days < 0:
                derived = "overdue"
            elif next_due and (next_due - today).days <= 7:
                derived = "near_due"
            else:
                derived = "active"

    return DebtorOut(
        id=d.id,
        name=d.name,
        phone=d.phone,
        national_id=d.national_id,
        line_id=d.line_id,
        address=d.address,
        principal=d.principal,
        interest_rate=d.interest_rate,
        interest_type=d.interest_type,  # type: ignore
        installments=d.installments,
        start_date=d.start_date,
        first_due_date=d.first_due_date,
        is_open_ended=is_open,
        bank=d.bank,
        account_no=d.account_no,
        funding_source=d.funding_source,
        notes=d.notes,
        status=derived,  # type: ignore
        created_at=d.created_at,
        updated_at=d.updated_at,
        rollover_from_id=d.rollover_from_id,
        rolled_amount=d.rolled_amount,
        total_paid=round(total_paid, 2),
        balance=round(max(balance, 0.0), 2),
        next_due_date=next_due,
        days_until_due=days_until,
        payments=[PaymentOut.model_validate(p) for p in (d.payments or [])],
        attachments=[AttachmentOut.model_validate(a) for a in (d.attachments or [])],
    )


@router.get("", response_model=list[DebtorOut])
def list_debtors(
    q: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    sort: str = "recent",
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
):
    stmt = select(Debtor)
    if q:
        like = f"%{q}%"
        stmt = stmt.where((Debtor.name.like(like)) | (Debtor.phone.like(like)))
    debtors = session.exec(stmt).all()
    out = [_enrich(d) for d in debtors]
    if status_filter and status_filter != "all":
        out = [d for d in out if d.status == status_filter]
    if sort == "name":
        out.sort(key=lambda x: x.name)
    elif sort == "balance":
        out.sort(key=lambda x: -x.balance)
    elif sort == "due":
        out.sort(key=lambda x: x.next_due_date or date.max)
    else:  # recent
        out.sort(key=lambda x: x.created_at, reverse=True)
    return out


@router.post("", response_model=DebtorOut, status_code=status.HTTP_201_CREATED)
def create_debtor(
    payload: DebtorCreate,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
):
    d = Debtor(**payload.model_dump())
    session.add(d)
    session.commit()
    session.refresh(d)
    return _enrich(d)


@router.get("/{debtor_id}", response_model=DebtorOut)
def get_debtor(
    debtor_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
):
    d = session.get(Debtor, debtor_id)
    if not d:
        raise HTTPException(status_code=404, detail="ไม่พบลูกหนี้")
    return _enrich(d)


@router.put("/{debtor_id}", response_model=DebtorOut)
def update_debtor(
    debtor_id: int,
    payload: DebtorUpdate,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
):
    d = session.get(Debtor, debtor_id)
    if not d:
        raise HTTPException(status_code=404, detail="ไม่พบลูกหนี้")
    data = payload.model_dump(exclude_unset=True)
    from datetime import datetime
    for k, v in data.items():
        setattr(d, k, v)
    d.updated_at = datetime.utcnow()
    session.add(d)
    session.commit()
    session.refresh(d)
    return _enrich(d)


@router.delete("/{debtor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_debtor(
    debtor_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
):
    d = session.get(Debtor, debtor_id)
    if not d:
        raise HTTPException(status_code=404, detail="ไม่พบลูกหนี้")
    # cascade payments + attachments
    for p in list(d.payments or []):
        session.delete(p)
    for a in list(d.attachments or []):
        session.delete(a)
    session.delete(d)
    session.commit()
    return None


@router.get("/{debtor_id}/schedule", response_model=InterestCalcOut)
def get_schedule(
    debtor_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
):
    d = session.get(Debtor, debtor_id)
    if not d:
        raise HTTPException(status_code=404, detail="ไม่พบลูกหนี้")
    return calc_schedule(
        d.principal, d.interest_rate, d.installments, d.interest_type,
        d.start_date, d.first_due_date,
    )


@router.post("/{debtor_id}/rollover", response_model=DebtorOut, status_code=status.HTTP_201_CREATED)
def rollover_debtor(
    debtor_id: int,
    payload: RolloverIn,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
):
    orig = session.get(Debtor, debtor_id)
    if not orig:
        raise HTTPException(status_code=404, detail="ไม่พบลูกหนี้")
    # mark original closed
    orig.status = "closed"
    session.add(orig)

    new_d = Debtor(
        name=orig.name,
        phone=orig.phone,
        national_id=orig.national_id,
        line_id=orig.line_id,
        address=orig.address,
        principal=payload.new_principal,
        interest_rate=payload.interest_rate,
        interest_type=orig.interest_type,
        installments=payload.installments,
        start_date=payload.start_date,
        bank=orig.bank,
        account_no=orig.account_no,
        funding_source=orig.funding_source,
        notes=payload.note or f"ทบจาก #{orig.id}",
        rollover_from_id=orig.id,
        rolled_amount=orig.principal,
    )
    session.add(new_d)
    session.commit()
    session.refresh(new_d)
    return _enrich(new_d)


# ── interest calc endpoint (used by AddDebtor live preview) ──
calc_router = APIRouter(prefix="/calc", tags=["calc"])


@calc_router.post("/interest", response_model=InterestCalcOut)
def calc_interest(payload: InterestCalcIn, _: User = Depends(get_current_user)):
    return calc_schedule(
        payload.principal, payload.rate_per_month, payload.months, payload.interest_type,
        first_due_date=payload.first_due_date,
    )
