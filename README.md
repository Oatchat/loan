# DebtTrack

Professional debt-tracking system for individual creditors. Apple-inspired UI meets Thai fintech.

## Stack

- **Frontend**: Vue 3 (Composition API) + Vite + Tailwind v3 + Pinia + Vue Router 4
- **Backend**: FastAPI + SQLite + SQLModel + JWT auth
- **UI**: headlessui/vue, @heroicons/vue, Chart.js (vue-chartjs), day.js
- **Forms**: vee-validate + yup
- **Toast**: vue-toastification

## Structure

```
loan/
├── backend/    # FastAPI + SQLite
└── frontend/   # Vue 3 + Vite
```

## Quick start

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m app.seed          # seed demo data (optional)
uvicorn app.main:app --reload --port 8000
```

API: http://localhost:8000  •  Docs: http://localhost:8000/docs

Demo login: `admin@debttrack.app` / `admin1234`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

App: http://localhost:5173

## Features

- ลูกหนี้ CRUD + อัปโหลดเอกสาร (สัญญา / บัตรประชาชน / สลิป / หลักทรัพย์)
- คำนวณดอกเบี้ย: flat / compound / custom
- บันทึกชำระ + amortization schedule
- ทบยอด (rollover) + ตรวจจับเกินกำหนด
- รายงาน: bar / donut / line charts + PDF/Excel export
- Thai locale, currency formatting (฿), responsive, accessible

## Deploy

### Backend → Render (Free)

1. Push repo to GitHub
2. Render dashboard → **New +** → **Blueprint** → connect repo → it reads `render.yaml`
3. After first deploy, copy the URL (e.g. `https://debttrack-api.onrender.com`)
4. Optional — open **Environment** tab, set `CORS_ORIGINS` to your Vercel domain
5. Backend auto-seeds demo data on first boot if DB is empty

**Free tier caveats:**
- Service sleeps after 15 min idle → first request after cooldown ~30s
- No persistent disk → SQLite + uploads reset on every redeploy (auto-seed re-runs)
- For long-term data persistence, either upgrade to Starter ($7/mo) or move DB to Neon Postgres (free)

### Frontend → Vercel

1. Vercel dashboard → **New Project** → import repo
2. **Root Directory** → `frontend`
3. **Environment Variables** → add `VITE_API_BASE_URL` = your Render URL (no trailing slash)
4. Deploy

After backend URL is known, you may also rewrite `/api/*` in `vercel.json` if you want a same-origin path, but it's not required since axios uses `VITE_API_BASE_URL` directly.
