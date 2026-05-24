import { computed } from 'vue'
import dayjs from 'dayjs'

function dueDateFor(monthNo, start, firstDue) {
  // If firstDue is provided, anchor schedule on it (month 1 = firstDue)
  // Else fall back to start + N months (month 1 = start + 1 month)
  if (firstDue) return dayjs(firstDue).add(monthNo - 1, 'month').format('YYYY-MM-DD')
  return dayjs(start).add(monthNo, 'month').format('YYYY-MM-DD')
}

function round(n) { return Math.round(n * 100) / 100 }

/**
 * Pure (non-reactive) installment calculator — usable inside loops/handlers.
 * Mirrors the server-side `calc_schedule` formula for flat/compound interest.
 */
export function calcInstallments({ principal, ratePerMonth, months, interestType, startDate, firstDueDate }) {
  const p = Math.max(0, Number(principal) || 0)
  const rPct = Math.max(0, Number(ratePerMonth) || 0)
  const m = Math.max(1, parseInt(months || 1))
  const type = interestType || 'flat'
  const start = startDate ? dayjs(startDate) : dayjs()
  const firstDue = firstDueDate || null
  const r = rPct / 100

  if (!p || !m) {
    return { totalInterest: 0, monthlyPayment: 0, totalPayment: 0, schedule: [] }
  }

  const schedule = []

  if (type === 'flat' || type === 'custom') {
    const monthlyInterest = p * r
    const monthlyPrincipal = p / m
    const monthlyPayment = monthlyPrincipal + monthlyInterest
    let balance = p
    for (let i = 1; i <= m; i++) {
      balance = Math.max(0, balance - monthlyPrincipal)
      schedule.push({
        month: i,
        dueDate: dueDateFor(i, start, firstDue),
        payment: round(monthlyPayment),
        principal: round(monthlyPrincipal),
        interest: round(monthlyInterest),
        balance: round(balance),
      })
    }
    return {
      totalInterest: round(monthlyInterest * m),
      monthlyPayment: round(monthlyPayment),
      totalPayment: round(monthlyPayment * m),
      schedule,
    }
  }

  // compound — amortization
  let monthlyPayment
  if (r === 0) monthlyPayment = p / m
  else monthlyPayment = (p * r * Math.pow(1 + r, m)) / (Math.pow(1 + r, m) - 1)
  let balance = p
  let totalInterest = 0
  for (let i = 1; i <= m; i++) {
    const interest = balance * r
    const principalPart = monthlyPayment - interest
    balance = Math.max(0, balance - principalPart)
    totalInterest += interest
    schedule.push({
      month: i,
      dueDate: dueDateFor(i, start, firstDue),
      payment: round(monthlyPayment),
      principal: round(principalPart),
      interest: round(interest),
      balance: round(balance),
    })
  }
  return {
    totalInterest: round(totalInterest),
    monthlyPayment: round(monthlyPayment),
    totalPayment: round(monthlyPayment * m),
    schedule,
  }
}

/** Returns the next unpaid installment row for a debtor (or null if all paid). */
export function nextUnpaidInstallment(debtor) {
  const paidCount = (debtor?.payments || []).length
  const { schedule } = calcInstallments({
    principal: debtor?.principal,
    ratePerMonth: debtor?.interest_rate,
    months: debtor?.installments,
    interestType: debtor?.interest_type,
    startDate: debtor?.start_date,
    firstDueDate: debtor?.first_due_date,
  })
  return schedule[paidCount] || null
}

/**
 * useInterestCalc(refs) — pass reactive refs for principal, ratePerMonth, months, type, startDate, firstDueDate (optional)
 * Returns: { totalInterest, monthlyPayment, totalPayment, schedule } as computed
 */
export function useInterestCalc({ principal, ratePerMonth, months, interestType, startDate, firstDueDate }) {
  const result = computed(() => calcInstallments({
    principal: principal.value,
    ratePerMonth: ratePerMonth.value,
    months: months.value,
    interestType: interestType.value,
    startDate: startDate.value,
    firstDueDate: firstDueDate?.value,
  }))

  return {
    totalInterest: computed(() => result.value.totalInterest),
    monthlyPayment: computed(() => result.value.monthlyPayment),
    totalPayment: computed(() => result.value.totalPayment),
    schedule: computed(() => result.value.schedule),
  }
}
