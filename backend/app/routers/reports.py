from collections import defaultdict
from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select

from ..db import get_session
from ..deps import get_current_user
from ..interest import calc_schedule
from ..models import Debtor, Payment, User
from ..schemas import MonthlyBucket, ReportDetailed, ReportSummary


router = APIRouter(prefix="/reports", tags=["reports"])


def _derived_status(d: Debtor, total_paid: float, total_payment: float) -> str:
    if d.status == "closed":
        return "closed"
    balance = total_payment - total_paid
    if balance <= 0:
        return "closed"
    # naive: rely on schedule next-due check would require more work; use start_date based
    today = date.today()
    months_passed = (today.year - d.start_date.year) * 12 + (today.month - d.start_date.month)
    if months_passed > d.installments:
        return "overdue"
    return "active"


@router.get("/summary", response_model=ReportDetailed)
def summary(
    start: Optional[date] = Query(None),
    end: Optional[date] = Query(None),
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
):
    stmt = select(Debtor)
    if start:
        stmt = stmt.where(Debtor.start_date >= start)
    if end:
        stmt = stmt.where(Debtor.start_date <= end)
    debtors = session.exec(stmt).all()

    total_principal = 0.0
    total_interest = 0.0
    total_paid_all = 0.0
    counts = defaultdict(int)
    monthly: dict[str, MonthlyBucket] = {}

    for d in debtors:
        sched = calc_schedule(d.principal, d.interest_rate, d.installments, d.interest_type, d.start_date)
        paid_sum = sum(p.amount for p in (d.payments or []))
        total_principal += d.principal
        total_interest += sched.total_interest
        total_paid_all += paid_sum
        st = _derived_status(d, paid_sum, sched.total_payment)
        counts[st] += 1

        key = d.start_date.strftime("%Y-%m")
        b = monthly.setdefault(key, MonthlyBucket(month=key, issued=0.0, collected=0.0, interest=0.0))
        b.issued += d.principal
        b.interest += sched.total_interest

        for p in (d.payments or []):
            pk = p.paid_date.strftime("%Y-%m")
            pb = monthly.setdefault(pk, MonthlyBucket(month=pk, issued=0.0, collected=0.0, interest=0.0))
            pb.collected += p.amount

    summary = ReportSummary(
        total_debtors=len(debtors),
        total_principal=round(total_principal, 2),
        total_interest_earned=round(total_interest, 2),
        total_paid=round(total_paid_all, 2),
        overdue_count=counts.get("overdue", 0),
        closed_count=counts.get("closed", 0),
        near_due_count=counts.get("near_due", 0),
        active_count=counts.get("active", 0),
    )
    monthly_sorted = sorted(monthly.values(), key=lambda b: b.month)
    return ReportDetailed(
        summary=summary,
        monthly=monthly_sorted,
        status_breakdown=dict(counts),
    )
