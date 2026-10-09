"""
Aplikasi prediksi harga Bitcoin memakai N-BEATS (model terbaik skripsi Kia).

Halaman:
1. Prediksi      - harga live + prediksi harga besok
2. Data Historis - grafik BTC-USD penuh (17 Sep 2014 - sekarang, realtime)
3. Model & Skripsi - arsitektur, hyperparameter, hasil perbandingan skripsi

Jalankan:  .venv/bin/python -m streamlit run app.py
"""
import json
import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf

from nbeats_model import build_nbeats

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "models")
DATA_PATH = os.path.join(BASE_DIR, "data", "btc_usd_daily.csv")
TICKER = "BTC-USD"
START_DATE = "2014-09-17"

st.set_page_config(page_title="Prediksi Harga Bitcoin | N-BEATS",
                   page_icon="₿", layout="wide")


# ------------------------- Data & model loading -------------------------
@st.cache_data(ttl=3600, show_spinner="Mengambil data terbaru dari Yahoo Finance...")
def get_data():
    """BTC-USD harian realtime; fallback ke CSV lokal bila offline."""
    try:
        df = yf.download(TICKER, start=START_DATE, progress=False,
                         auto_adjust=False)
        if df is not None and len(df) > 100:
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            df = df[["Close"]].dropna()
            df.index = pd.to_datetime(df.index).tz_localize(None)
            df.to_csv(DATA_PATH)  # refresh cache lokal
            return df
    except Exception:  # noqa: BLE001
        pass
    df = pd.read_csv(DATA_PATH, index_col=0, parse_dates=True)
    return df


@st.cache_resource(show_spinner="Memuat model N-BEATS...")
def get_model():
    with open(os.path.join(MODEL_DIR, "config.json")) as f:
        config = json.load(f)
    with open(os.path.join(MODEL_DIR, "scaler.json")) as f:
        scaler = json.load(f)
    model = build_nbeats(lookback=config["lookback"],
                         horizon=config["horizon"],
                         n_blocks=config["n_blocks"],
                         units=config["units"],
                         learning_rate=config["learning_rate"])
    model.load_weights(os.path.join(MODEL_DIR, "nbeats_weights.weights.h5"))
    return model, config, scaler


def predict_next(df, model, config, scaler):
    lookback = config["lookback"]
    closes = df["Close"].to_numpy(dtype=float)
    last_n = closes[-lookback:]
    dmin, dmax = scaler["data_min"], scaler["data_max"]
    scaled = (last_n - dmin) / (dmax - dmin)
    pred_scaled = model.predict(scaled.reshape(1, lookback), verbose=0)[0, 0]
    return float(pred_scaled * (dmax - dmin) + dmin)


def fmt_usd(x):
    return f"${x:,.2f}"


# ------------------------------- Sidebar --------------------------------
st.sidebar.title("₿ Prediksi Bitcoin")
page = st.sidebar.radio("Navigasi",
                        ["Prediksi", "Data Historis", "Model & Skripsi"])
st.sidebar.caption("Model: N-BEATS + Adam\n(hyperparameter juara skripsi)")

artifacts_ok = os.path.exists(os.path.join(MODEL_DIR, "nbeats_weights.weights.h5"))
if not artifacts_ok:
    st.error("Model belum dilatih. Jalankan dulu: `.venv/bin/python scripts/train.py`")
    st.stop()

df = get_data()
model, config, scaler = get_model()
with open(os.path.join(MODEL_DIR, "metrics.json")) as f:
    metrics = json.load(f)

live_price = float(df["Close"].iloc[-1])
live_date = df.index[-1].date()
pred_price = predict_next(df, model, config, scaler)
pred_date = (df.index[-1] + pd.Timedelta(days=1)).date()
delta = pred_price - live_price
delta_pct = delta / live_price * 100

# ------------------------------ Halaman 1 -------------------------------
if page == "Prediksi":
    st.title("Prediksi Harga Bitcoin (BTC-USD)")
    st.caption(f"Data realtime Yahoo Finance • terakhir update {live_date} • "
               f"model N-BEATS (lookback {config['lookback']} hari)")

    c1, c2, c3 = st.columns(3)
    c1.metric("Harga Terakhir", fmt_usd(live_price), str(live_date))
    c2.metric("Prediksi Besok", fmt_usd(pred_price),
              f"{delta:+,.2f} ({delta_pct:+.2f}%)", delta_color="normal")
    c3.metric("Akurasi Model (MAPE)", f"{metrics['MAPE']:.2f}%",
              f"R² {metrics['R2']:.4f}", delta_color="off")

    st.subheader("Tren 90 hari terakhir + prediksi")
    recent = df.tail(90)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=recent.index, y=recent["Close"],
                             mode="lines", name="Harga aktual",
                             line=dict(color="#1f77b4", width=2)))
    fig.add_trace(go.Scatter(
        x=[recent.index[-1], pd.Timestamp(pred_date)],
        y=[live_price, pred_price], mode="lines+markers",
        name="Prediksi besok",
        line=dict(color="#ff7f0e", width=2, dash="dash"),
        marker=dict(size=8)))
    fig.update_layout(height=420, margin=dict(l=10, r=10, t=10, b=10),
                      yaxis_title="USD", xaxis_title="Tanggal",
                      legend=dict(orientation="h", y=1.05))
    st.plotly_chart(fig, use_container_width=True)

    st.info("⚠️ **Disclaimer:** ini project portofolio dari hasil skripsi, "
            "bukan saran investasi. Model memprediksi harga penutupan besok "
            "berdasarkan 10 harga terakhir — tren harian Bitcoin sangat "
            "mirip harga hari ini, jadi akurasi tinggi tidak berarti bisa "
            "mengalahkan pasar.")

# ------------------------------ Halaman 2 -------------------------------
elif page == "Data Historis":
    st.title("Data Historis BTC-USD")
    st.caption(f"Yahoo Finance • {df.index[0].date()} s/d {live_date} "
               f"• {len(df):,} baris harian")

    c1, c2, c3, c4 = st.columns(4)
    ath = float(df["Close"].max())
    ath_date = df["Close"].idxmax().date()
    first = float(df["Close"].iloc[0])
    gain = (live_price / first - 1) * 100
    c1.metric("Harga Pertama", fmt_usd(first), str(df.index[0].date()))
    c2.metric("Harga Terakhir", fmt_usd(live_price), str(live_date))
    c3.metric("Tertinggi (ATH)", fmt_usd(ath), str(ath_date))
    c4.metric("Kenaikan Total", f"{gain:,.0f}%", "sejak 2014")

    log = st.toggle("Skala logaritmik", value=False)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df["Close"], mode="lines",
                             name="BTC-USD",
                             line=dict(color="#f7931a", width=1.5)))
    fig.update_layout(height=450, margin=dict(l=10, r=10, t=10, b=10),
                      yaxis_title="USD (log)" if log else "USD",
                      xaxis_title="Tahun")
    if log:
        fig.update_yaxes(type="log")
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Catatan: Yahoo Finance hanya menyimpan BTC-USD mulai "
               "17 September 2014 (Bitcoin sendiri lahir Januari 2009).")

# ------------------------------ Halaman 3 -------------------------------
else:
    st.title("Model & Hasil Skripsi")
    st.markdown(
        "**N-BEATS** (Neural Basis Expansion Analysis for Time Series) — "
        "arsitektur feedforward khusus time series. Tiap *block* memecah "
        "input jadi dua: *backcast* (bagian yang berhasil dijelaskan block "
        "ini, dikurangkan dari sisa) dan *forecast* (kontribusi prediksi, "
        "dijumlahkan). Beberapa block ditumpuk secara residual. "
        "Implementasi di project ini disalin persis dari notebook skripsi "
        "(`nbeats_model.py`), hanya dibungkus agar bisa di-save/load "
        "untuk deploy.")

    st.subheader("Hyperparameter (konfigurasi juara)")
    hp = pd.DataFrame([
        ["Lookback", f"{config['lookback']} hari"],
        ["Horizon", f"{config['horizon']} hari ke depan"],
        ["Jumlah block", config["n_blocks"]],
        ["Units per block", config["units"]],
        ["Optimizer", f"Adam (lr={config['learning_rate']})"],
        ["Loss", "MSE"], ["Batch size", config["batch_size"]],
        ["Input", "Univariat: harga Close (MinMaxScaler)"],
    ], columns=["Parameter", "Nilai"])
    st.table(hp)

    st.subheader("Perbandingan hasil skripsi (test set)")
    st.caption("8 eksperimen utama — tuning manual. N-BEATS + Adam terbaik.")
    comp = pd.DataFrame([
        ["N-BEATS", "Adam", 1789.95, 1227.35, 2.35, 0.9969],
        ["GRU", "Adam", 2184.15, 1581.02, 2.23, 0.9939],
        ["GRU", "AdamW", 2317.21, 1698.42, 2.26, 0.9931],
        ["N-BEATS", "AdamW", 3065.19, 2108.70, 3.38, 0.9910],
        ["Hybrid CNN-LSTM", "Adam", 3450.61, 2625.78, 3.34, 0.9847],
        ["Hybrid CNN-LSTM", "AdamW", 4226.77, 3356.07, 4.35, 0.9770],
        ["LSTM", "AdamW", 4656.02, 3687.43, 4.40, 0.9718],
        ["LSTM", "Adam", 4743.73, 3596.99, 4.28, 0.9710],
    ], columns=["Model", "Optimizer", "RMSE", "MAE", "MAPE (%)", "R²"])
    st.dataframe(comp, use_container_width=True, hide_index=True)

    st.subheader("Performa model yang di-deploy (test set terbaru)")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("RMSE", f"{metrics['RMSE']:,.2f}")
    m2.metric("MAE", f"{metrics['MAE']:,.2f}")
    m3.metric("MAPE", f"{metrics['MAPE']:.2f}%")
    m4.metric("R²", f"{metrics['R2']:.4f}")
    st.caption(f"Test set: {metrics['test_start']} s/d {metrics['test_end']} "
               f"({metrics['n_test']:,} hari)")

    tp = pd.read_csv(os.path.join(MODEL_DIR, "test_predictions.csv"),
                     parse_dates=["date"])
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=tp["date"], y=tp["actual"], mode="lines",
                             name="Aktual", line=dict(color="#1f77b4")))
    fig.add_trace(go.Scatter(x=tp["date"], y=tp["predicted"], mode="lines",
                             name="Prediksi N-BEATS",
                             line=dict(color="#ff7f0e", dash="dash")))
    fig.update_layout(height=380, margin=dict(l=10, r=10, t=10, b=10),
                      yaxis_title="USD", xaxis_title="Tanggal",
                      legend=dict(orientation="h", y=1.05))
    st.plotly_chart(fig, use_container_width=True)
