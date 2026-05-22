import { computed } from 'vue'
import dayjs from 'dayjs'

function dueDateFor(monthNo, start, firstDue) {
  // If firstDue is provided, anchor schedule on it (month 1 = firstDue)
  // Else fall back to start + N months (month 1 = start + 1 month)
  if (firstDue) return dayjs(firstDue).add(monthNo - 1, 'month').format('YYYY-MM-DD')
  return dayjs(start).add(monthNo, 'month').format('YYYY-MM-DD')
}

/**
 * useInterestCalc(refs) — pass reactive refs for principal, ratePerMonth, months, type, startDate, firstDueDate (optional)
 * Returns: { totalInterest, monthlyPayment, totalPayment, schedule } as computed
 */
export function useInterestCalc({ principal, ratePerMonth, months, interestType, startDate, firstDueDate }) {
  const result = computed(() => {
    const p = Math.max(0, Number(principal.value) || 0)
    const rPct = Math.max(0, Number(ratePerMonth.value) || 0)
    const m = Math.max(1, parseInt(months.value || 1))
    const type = interestType.value || 'flat'
    const start = startDate.value ? dayjs(startDate.value) : dayjs()
    const firstDue = firstDueDate?.value || null
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
  })

  return {
    totalInterest: computed(() => result.value.totalInterest),
    monthlyPayment: computed(() => result.value.monthlyPayment),
    totalPayment: computed(() => result.value.totalPayment),
    schedule: computed(() => result.value.schedule),
  }
}

function round(n) { return Math.round(n * 100) / 100 }
