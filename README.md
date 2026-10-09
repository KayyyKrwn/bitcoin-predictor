# Prediksi Harga Bitcoin dengan N-BEATS

Web app Streamlit dari hasil skripsi Kia: prediksi harga penutupan BTC-USD
1 hari ke depan memakai model **N-BEATS + Adam** (model terbaik skripsi:
RMSE 1.790, MAPE 2,35%, R² 0,9969).

Data: BTC-USD harian **realtime dari Yahoo Finance**, 17 Sep 2014 – sekarang
(Yahoo hanya menyimpan BTC-USD mulai tanggal itu).

## Struktur

```
├── app.py               # aplikasi Streamlit (3 halaman)
├── nbeats_model.py      # arsitektur N-BEATS (disalin dari notebook skripsi)
├── scripts/train.py     # training + evaluasi + simpan artefak
├── data/               # cache CSV BTC-USD (diunduh otomatis)
├── models/             # bobot, scaler, metrik, prediksi test set
└── requirements.txt
```

## Cara menjalankan

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt

# 1. Training (sekali saja, ~5-10 menit di CPU)
.venv/bin/python scripts/train.py

# 2. Jalankan app
.venv/bin/python -m streamlit run app.py
```

## Halaman

1. **Prediksi** — harga live + prediksi besok + tren 90 hari
2. **Data Historis** — grafik penuh 2014–sekarang + statistik
3. **Model & Skripsi** — arsitektur, hyperparameter, tabel perbandingan
   8 eksperimen skripsi, dan performa model yang di-deploy

## Catatan deploy N-BEATS

N-BEATS diimplementasikan sebagai custom Keras `Layer`/`Model`, jadi tidak
bisa di-load dari file `.keras` polos. Solusinya (dipakai di sini):
definisi class dibawa dalam `nbeats_model.py`, model dibangun ulang dari
kode, lalu `load_weights()` — plus `CUSTOM_OBJECTS` bila memakai
`load_model()`. Arsitektur dan hyperparameter 100% sama dengan skripsi.

⚠️ Project portofolio/edukasi, bukan saran investasi.
