import dayjs from 'dayjs'
import 'dayjs/locale/th'
import relativeTime from 'dayjs/plugin/relativeTime'

dayjs.extend(relativeTime)
dayjs.locale('th')

export function formatBaht(n) {
  if (n === null || n === undefined || Number.isNaN(+n)) return '฿0'
  const v = Number(n)
  return '฿' + v.toLocaleString('th-TH', { minimumFractionDigits: 0, maximumFractionDigits: 2 })
}

export function formatNumber(n, digits = 0) {
  if (n === null || n === undefined || Number.isNaN(+n)) return '0'
  return Number(n).toLocaleString('th-TH', { minimumFractionDigits: digits, maximumFractionDigits: digits })
}

export function formatDate(d, fmt = 'D MMM YYYY') {
  if (!d) return ''
  return dayjs(d).format(fmt)
}

export function formatRelative(d) {
  if (!d) return ''
  return dayjs(d).fromNow()
}

export function formatPhone(p) {
  if (!p) return ''
  const s = String(p).replace(/\D/g, '')
  if (s.length === 10) return `${s.slice(0,3)}-${s.slice(3,6)}-${s.slice(6)}`
  return p
}

export function initials(name) {
  if (!name) return '?'
  const parts = String(name).trim().split(/\s+/)
  if (parts.length === 1) return parts[0].slice(0, 1).toUpperCase()
  return (parts[0].slice(0, 1) + parts[parts.length - 1].slice(0, 1)).toUpperCase()
}

export function avatarColor(name) {
  // deterministic pleasant color based on name hash
  const palette = ['#0071E3', '#30D158', '#FF9F0A', '#5E5CE6', '#FF375F', '#64D2FF', '#BF5AF2']
  let h = 0
  for (const ch of String(name || '')) h = (h * 31 + ch.charCodeAt(0)) >>> 0
  return palette[h % palette.length]
}

export function statusLabel(s) {
  return {
    active: 'ปกติ',
    near_due: 'ใกล้ครบ',
    overdue: 'เกินกำหนด',
    closed: 'ปิดบัญชี',
  }[s] || s
}

export function statusColor(s) {
  return {
    active: { bg: '#E8F1FB', text: '#0071E3' },
    near_due: { bg: '#FFF4E5', text: '#B25E00' },
    overdue: { bg: '#FFE5E3', text: '#C0271F' },
    closed: { bg: '#EEEEF0', text: '#86868B' },
  }[s] || { bg: '#EEEEF0', text: '#3A3A3C' }
}
