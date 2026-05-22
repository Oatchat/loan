from datetime import date

from .schemas import InterestCalcIn, InterestCalcOut, ScheduleRow


def _add_months(d: date, months: int) -> date:
    # naive impl: increment month, clamp day
    y = d.year + (d.month - 1 + months) // 12
    m = (d.month - 1 + months) % 12 + 1
    day = min(d.day, [31, 29 if y % 4 == 0 and (y % 100 != 0 or y % 400 == 0) else 28,
                      31, 30, 31, 30, 31, 31, 30, 31, 30, 31][m - 1])
    return date(y, m, day)


def calc_schedule(
    principal: float,
    rate_per_month: float,
    months: int,
    interest_type: str = "flat",
    start_date: date | None = None,
) -> InterestCalcOut:
    start_date = start_date or date.today()
    rate = rate_per_month / 100.0
    rows: list[ScheduleRow] = []

    if interest_type == "flat":
        monthly_interest = principal * rate
        monthly_principal = principal / months
        monthly_payment = monthly_principal + monthly_interest
        balance = principal
        for m in range(1, months + 1):
            balance = max(0.0, balance - monthly_principal)
            rows.append(ScheduleRow(
                month=m,
                due_date=_add_months(start_date, m),
                payment=round(monthly_payment, 2),
                principal=round(monthly_principal, 2),
                interest=round(monthly_interest, 2),
                balance=round(balance, 2),
            ))
        total_interest = monthly_interest * months
        total_payment = monthly_payment * months

    elif interest_type == "compound":
        # standard amortization
        if rate == 0:
            monthly_payment = principal / months
        else:
            monthly_payment = principal * rate * (1 + rate) ** months / ((1 + rate) ** months - 1)
        balance = principal
        total_interest = 0.0
        for m in range(1, months + 1):
            interest = balance * rate
            principal_part = monthly_payment - interest
            balance = max(0.0, balance - principal_part)
            total_interest += interest
            rows.append(ScheduleRow(
                month=m,
                due_date=_add_months(start_date, m),
                payment=round(monthly_payment, 2),
                principal=round(principal_part, 2),
                interest=round(interest, 2),
                balance=round(balance, 2),
            ))
        total_payment = monthly_payment * months

    else:  # custom — treat as flat for now (UI can override per row later)
        return calc_schedule(principal, rate_per_month, months, "flat", start_date)

    return InterestCalcOut(
        total_interest=round(total_interest, 2),
        monthly_payment=round(monthly_payment, 2),
        total_payment=round(total_payment, 2),
        schedule=rows,
    )


def calc_from_dto(dto: InterestCalcIn) -> InterestCalcOut:
    return calc_schedule(
        principal=dto.principal,
        rate_per_month=dto.rate_per_month,
        months=dto.months,
        interest_type=dto.interest_type,
    )
