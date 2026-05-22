"""Seed demo data: 1 admin user + 10 debtors with varied statuses."""
from datetime import date, timedelta
import random

from sqlmodel import Session, select

from .auth import hash_password
from .db import engine, init_db
from .models import User, Debtor, Payment


THAI_FIRST = ["สมชาย", "มานี", "ปิติ", "ชูใจ", "สุดา", "อนุชา", "พิมพ์", "กิตติ", "ณัฐ", "ปาริชาต"]
THAI_LAST = ["รักไทย", "ใจดี", "ทองคำ", "ศรีสวัสดิ์", "พรหมมา", "เกษมสุข", "วงศ์ใหญ่", "บุญมา", "แสงทอง", "พิทักษ์"]
BANKS = ["SCB", "KBANK", "BBL", "KTB", "TTB"]
FUNDING_SOURCES = ["บัญชีออมทรัพย์ SCB", "เงินสด", "บัญชีธุรกิจ KBANK", "พร้อมเพย์ส่วนตัว"]
INTEREST_TYPES = ["flat", "compound"]
STATUSES_PLAN = ["overdue", "overdue", "near_due", "near_due", "near_due", "active", "active", "active", "closed", "closed"]


def run():
    init_db()
    with Session(engine) as s:
        existing = s.exec(select(User).where(User.email == "admin@debttrack.app")).first()
        if not existing:
            admin = User(
                email="admin@debttrack.app",
                password_hash=hash_password("admin1234"),
                name="ผู้ดูแลระบบ",
            )
            s.add(admin)
            s.commit()
            print("✓ Created admin user: admin@debttrack.app / admin1234")

        if s.exec(select(Debtor)).first():
            print("✓ Debtors already exist, skipping seed")
            return

        today = date.today()
        for i, plan in enumerate(STATUSES_PLAN):
            first = THAI_FIRST[i]
            last = THAI_LAST[i]
            principal = random.choice([5000, 10000, 15000, 20000, 30000, 50000, 100000])
            rate = random.choice([1.0, 1.5, 2.0, 3.0, 5.0])
            months = random.choice([3, 6, 12, 24])

            if plan == "overdue":
                start = today - timedelta(days=months * 30 + 30)
            elif plan == "near_due":
                start = today - timedelta(days=months * 30 - random.randint(1, 7))
            elif plan == "closed":
                start = today - timedelta(days=months * 30 + 60)
            else:
                start = today - timedelta(days=random.randint(30, 120))

            d = Debtor(
                name=f"{first} {last}",
                phone=f"08{random.randint(10000000, 99999999)}",
                national_id="".join(str(random.randint(0, 9)) for _ in range(13)),
                line_id=f"@{first.lower()}",
                address=f"{random.randint(1, 999)}/{random.randint(1, 50)} ถ.สุขุมวิท กรุงเทพฯ",
                principal=float(principal),
                interest_rate=rate,
                interest_type=random.choice(INTEREST_TYPES),
                installments=months,
                start_date=start,
                bank=random.choice(BANKS),
                account_no="".join(str(random.randint(0, 9)) for _ in range(10)),
                funding_source=random.choice(FUNDING_SOURCES),
                status="closed" if plan == "closed" else "active",
                notes=None,
            )
            s.add(d)
            s.commit()
            s.refresh(d)

            # add some payments for active/near_due/closed
            paid_months = 0
            if plan == "closed":
                paid_months = months
            elif plan == "near_due":
                paid_months = max(0, months - 1)
            elif plan == "active":
                paid_months = random.randint(1, max(1, months // 2))

            for k in range(paid_months):
                paid_date = start + timedelta(days=(k + 1) * 30)
                amount = (principal / months) * (1 + rate / 100)
                s.add(Payment(
                    debtor_id=d.id,
                    amount=round(amount, 2),
                    paid_date=paid_date,
                    installment_no=k + 1,
                    status="paid",
                ))
            s.commit()

        print(f"✓ Seeded {len(STATUSES_PLAN)} debtors")


if __name__ == "__main__":
    run()
