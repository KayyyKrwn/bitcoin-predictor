# Bitcoin Predictor — N-BEATS + HeroUI

Prediksi harga penutupan Bitcoin (BTC-USD) 1 hari ke depan memakai model
**N-BEATS + Adam** — model terbaik dari skripsi Kia (RMSE 1.790, MAPE 2,35%,
R² 0,9969 pada eksperimen utama; 4 arsitektur × 2 optimizer × 2 mode tuning).

Aplikasi full-stack:

| Lapisan   | Teknologi                              |
|-----------|----------------------------------------|
| Frontend  | Next.js (App Router) + HeroUI v3 + Tailwind CSS v4 + Recharts |
| Backend   | FastAPI — menyajikan model N-BEATS sebagai REST API |
| Data      | BTC-USD harian realtime dari Yahoo Finance (17 Sep 2014 – sekarang) |

Halaman: **Prediksi** (harga live + prediksi besok), **Data Historis**
(grafik penuh + statistik), **Model & Skripsi** (arsitektur, hyperparameter,
tabel perbandingan 8 eksperimen, performa model yang di-deploy).

## Struktur repo

```
├── frontend/               # Next.js + HeroUI
│   ├── app/                # 3 halaman: /, /history, /model
│   ├── components/         # Navbar, PriceChart (recharts)
│   └── lib/                # api.ts (client backend), format.ts
├── backend/
│   ├── main.py             # FastAPI: /api/predict, /api/history, /api/model
│   ├── nbeats_model.py     # arsitektur N-BEATS (dari notebook skripsi)
│   ├── scripts/train.py    # training + evaluasi
│   ├── requirements.txt
│   └── models/             # bobot, scaler, metrik (bobot tidak ikut git)
└── README.md
```

## Menjalankan backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate | Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --port 8000
```

> Pertama kali dijalankan, backend otomatis training model bila bobot belum
> ada (data diunduh dari Yahoo Finance, training ~1 menit di CPU).

## Menjalankan frontend

```bash
cd frontend
npm install
npm run dev
```

Buka http://localhost:3000. Backend harus jalan di http://localhost:8000
(atau set `NEXT_PUBLIC_API_URL` di `.env.local`).

## API

- `GET /api/health` — status
- `GET /api/predict` — harga live, prediksi besok, 90 hari terakhir, metrik
- `GET /api/history` — seluruh riwayat + statistik (ATH, kenaikan total)
- `GET /api/model` — hyperparameter, metrik, perbandingan skripsi,
  prediksi vs aktual (test set)
- Dokumentasi interaktif: http://localhost:8000/docs

## Catatan deploy N-BEATS

N-BEATS diimplementasikan sebagai custom Keras `Layer`/`Model`, sehingga
arsitektur dibangun ulang dari kode (`backend/nbeats_model.py`) lalu
`load_weights()` — 100% sama dengan skripsi.

⚠️ Project portofolio/edukasi, bukan saran investasi.
