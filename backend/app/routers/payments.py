from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from ..db import get_session
from ..deps import get_current_user
from ..models import Debtor, Payment, User
from ..schemas import PaymentCreate, PaymentOut


router = APIRouter(prefix="/debtors/{debtor_id}/payments", tags=["payments"])


@router.get("", response_model=list[PaymentOut])
def list_payments(
    debtor_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
):
    d = session.get(Debtor, debtor_id)
    if not d:
        raise HTTPException(status_code=404, detail="ไม่พบลูกหนี้")
    return list(d.payments or [])


@router.post("", response_model=PaymentOut, status_code=status.HTTP_201_CREATED)
def create_payment(
    debtor_id: int,
    payload: PaymentCreate,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
):
    d = session.get(Debtor, debtor_id)
    if not d:
        raise HTTPException(status_code=404, detail="ไม่พบลูกหนี้")
    p = Payment(debtor_id=debtor_id, **payload.model_dump())
    session.add(p)
    session.commit()
    session.refresh(p)
    return p


@router.delete("/{payment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_payment(
    debtor_id: int,
    payment_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
):
    p = session.get(Payment, payment_id)
    if not p or p.debtor_id != debtor_id:
        raise HTTPException(status_code=404, detail="ไม่พบรายการชำระ")
    session.delete(p)
    session.commit()
    return None
