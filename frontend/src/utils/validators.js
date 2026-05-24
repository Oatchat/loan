import * as yup from 'yup'

export const loginSchema = yup.object({
  username: yup.string().min(3, 'ผู้ใช้อย่างน้อย 3 ตัวอักษร').required('กรุณากรอกชื่อผู้ใช้'),
  password: yup.string().min(4, 'รหัสผ่านอย่างน้อย 4 ตัวอักษร').required('กรุณากรอกรหัสผ่าน'),
})

export const debtorSchema = yup.object({
  name: yup.string().min(3, 'ชื่ออย่างน้อย 3 ตัวอักษร').required('กรุณากรอกชื่อ'),
  phone: yup.string()
    .matches(/^0[6-9]\d{8}$/, 'เบอร์โทรไม่ถูกต้อง (เช่น 08XXXXXXXX)')
    .required('กรุณากรอกเบอร์โทร'),
  national_id: yup.string().nullable().notRequired().test('len', 'เลขบัตร 13 หลัก',
    v => !v || /^\d{13}$/.test(v)),
  line_id: yup.string().nullable(),
  address: yup.string().nullable(),
  principal: yup.number().typeError('ต้องเป็นตัวเลข').positive('ต้องมากกว่า 0').max(10_000_000, 'ไม่เกิน 10,000,000').required('กรุณากรอกจำนวนเงิน'),
  interest_rate: yup.number().typeError('ต้องเป็นตัวเลข').min(0, 'ต้อง ≥ 0').max(30, 'ไม่เกิน 30%').required('กรุณากรอกอัตราดอกเบี้ย'),
  interest_type: yup.string().oneOf(['flat', 'compound', 'custom']).required(),
  installments: yup.number().typeError('ต้องเป็นตัวเลข').integer('ต้องเป็นจำนวนเต็ม').min(1).max(360).required('กรุณากรอกจำนวนงวด'),
  start_date: yup.string().required('กรุณาเลือกวันที่ยืม'),
  first_due_date: yup.string().nullable(),
  bank: yup.string().nullable(),
  account_no: yup.string().nullable(),
  funding_source: yup.string().nullable().max(200, 'ไม่เกิน 200 ตัวอักษร'),
  notes: yup.string().nullable().max(500, 'ไม่เกิน 500 ตัวอักษร'),
})

export const paymentSchema = yup.object({
  amount: yup.number().typeError('ต้องเป็นตัวเลข').positive('ต้องมากกว่า 0').required('กรุณากรอกจำนวนเงิน'),
  paid_date: yup.string().required('กรุณาเลือกวันที่ชำระ'),
})

export const rolloverSchema = yup.object({
  new_principal: yup.number().typeError('ต้องเป็นตัวเลข').positive().required(),
  interest_rate: yup.number().min(0).max(30).required(),
  installments: yup.number().integer().min(1).max(360).required(),
  start_date: yup.string().required(),
})
