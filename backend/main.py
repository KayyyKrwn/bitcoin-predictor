"""
Backend FastAPI untuk Bitcoin Predictor.

Menyajikan model N-BEATS (hasil skripsi) sebagai REST API untuk
frontend Next.js + HeroUI.

Endpoints:
  GET /api/health   - status
  GET /api/predict  - harga live + prediksi besok + 90 hari terakhir
  GET /api/history  - seluruh riwayat BTC-USD + statistik
  GET /api/model    - hyperparameter, metrik, perbandingan skripsi,
                      prediksi vs aktual (test set)

Jika artefak model belum ada, training dijalankan otomatis sekali
saat startup (memakai backend/scripts/train.py).

Jalankan:  uvicorn main:app --port 8000   (dari folder backend/)
"""
import json
import os
import sys
import threading
import time
from contextlib import asynccontextmanager

import numpy as np
import pandas as pd
import yfinance as yf
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "models")
DATA_PATH = os.path.join(BASE_DIR, "data", "btc_usd_daily.csv")
TICKER = "BTC-USD"
START_DATE = "2014-09-17"
DATA_TTL = 3600  # detik

sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, "scripts"))
from nbeats_model import build_nbeats  # noqa: E402
import train as train_module  # noqa: E402

# Hasil 8 eksperimen utama skripsi (tuning manual, test set) — untuk
# ditampilkan di halaman Model & Skripsi.
THESIS_COMPARISON = [
    {"model": "N-BEATS", "optimizer": "Adam", "rmse": 1789.95,
     "mae": 1227.35, "mape": 2.35, "r2": 0.9969, "best": True},
    {"model": "GRU", "optimizer": "Adam", "rmse": 2184.15,
     "mae": 1581.02, "mape": 2.23, "r2": 0.9939, "best": False},
    {"model": "GRU", "optimizer": "AdamW", "rmse": 2317.21,
     "mae": 1698.42, "mape": 2.26, "r2": 0.9931, "best": False},
    {"model": "N-BEATS", "optimizer": "AdamW", "rmse": 3065.19,
     "mae": 2108.70, "mape": 3.38, "r2": 0.9910, "best": False},
    {"model": "Hybrid CNN-LSTM", "optimizer": "Adam", "rmse": 3450.61,
     "mae": 2625.78, "mape": 3.34, "r2": 0.9847, "best": False},
    {"model": "Hybrid CNN-LSTM", "optimizer": "AdamW", "rmse": 4226.77,
     "mae": 3356.07, "mape": 4.35, "r2": 0.9770, "best": False},
    {"model": "LSTM", "optimizer": "AdamW", "rmse": 4656.02,
     "mae": 3687.43, "mape": 4.40, "r2": 0.9718, "best": False},
    {"model": "LSTM", "optimizer": "Adam", "rmse": 4743.73,
     "mae": 3596.99, "mape": 4.28, "r2": 0.9710, "best": False},
]

state = {"model": None, "config": None, "scaler": None,
         "metrics": None, "lock": threading.Lock()}
_data_cache = {"df": None, "ts": 0.0}


def _needed_files():
    return ["nbeats_weights.weights.h5", "scaler.json", "config.json",
            "metrics.json", "test_predictions.csv"]


def ensure_artifacts():
    """Training otomatis bila artefak model belum ada."""
    missing = [f for f in _needed_files()
               if not os.path.exists(os.path.join(MODEL_DIR, f))]
    if not missing:
        return
    print(f"[backend] artefak belum ada ({missing}), training dulu ...")
    train_module.main()
    print("[backend] training selesai.")


def load_state():
    with open(os.path.join(MODEL_DIR, "config.json")) as f:
        config = json.load(f)
    with open(os.path.join(MODEL_DIR, "scaler.json")) as f:
        scaler = json.load(f)
    with open(os.path.join(MODEL_DIR, "metrics.json")) as f:
        metrics = json.load(f)
    model = build_nbeats(lookback=config["lookback"],
                         horizon=config["horizon"],
                         n_blocks=config["n_blocks"],
                         units=config["units"],
                         learning_rate=config["learning_rate"])
    model.load_weights(os.path.join(MODEL_DIR, "nbeats_weights.weights.h5"))
    state.update(model=model, config=config, scaler=scaler, metrics=metrics)


def get_data() -> pd.DataFrame:
    """BTC-USD harian; cache 1 jam; fallback ke CSV lokal."""
    now = time.time()
    if _data_cache["df"] is not None and now - _data_cache["ts"] < DATA_TTL:
        return _data_cache["df"]
    df = None
    try:
        raw = yf.download(TICKER, start=START_DATE, progress=False,
                          auto_adjust=False)
        if raw is not None and len(raw) > 100:
            if isinstance(raw.columns, pd.MultiIndex):
                raw.columns = raw.columns.get_level_values(0)
            df = raw[["Close"]].dropna()
            df.index = pd.to_datetime(df.index).tz_localize(None)
            os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
            df.to_csv(DATA_PATH)
    except Exception:  # noqa: BLE001
        df = None
    if df is None:
        if not os.path.exists(DATA_PATH):
            raise HTTPException(503, "Data tidak tersedia (Yahoo Finance "
                                     "gagal & tidak ada cache lokal).")
        df = pd.read_csv(DATA_PATH, index_col=0, parse_dates=True)
    _data_cache.update(df=df, ts=now)
    return df


def predict_next(df: pd.DataFrame) -> float:
    cfg, sc = state["config"], state["scaler"]
    lb = cfg["lookback"]
    closes = df["Close"].to_numpy(dtype=float)
    if len(closes) < lb:
        raise HTTPException(500, "Data kurang dari lookback.")
    dmin, dmax = sc["data_min"], sc["data_max"]
    scaled = (closes[-lb:] - dmin) / (dmax - dmin)
    with state["lock"]:
        pred_scaled = state["model"].predict(scaled.reshape(1, lb),
                                             verbose=0)[0, 0]
    return float(pred_scaled * (dmax - dmin) + dmin)


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_artifacts()
    load_state()
    print("[backend] model N-BEATS siap.")
    yield


app = FastAPI(title="Bitcoin Predictor API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # dev; batasi di production
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok", "model": "nbeats",
            "loaded": state["model"] is not None}


@app.get("/api/predict")
def predict():
    df = get_data()
    live = float(df["Close"].iloc[-1])
    live_date = df.index[-1].date().isoformat()
    pred = predict_next(df)
    pred_date = (df.index[-1] + pd.Timedelta(days=1)).date().isoformat()
    delta = pred - live
    recent = df.tail(90)
    return {
        "live_price": live,
        "live_date": live_date,
        "pred_price": pred,
        "pred_date": pred_date,
        "delta": delta,
        "delta_pct": delta / live * 100,
        "metrics": state["metrics"],
        "recent": [{"date": d.date().isoformat(), "close": float(c)}
                   for d, c in zip(recent.index, recent["Close"])],
    }


@app.get("/api/history")
def history():
    df = get_data()
    closes = df["Close"]
    ath = float(closes.max())
    return {
        "start": df.index[0].date().isoformat(),
        "end": df.index[-1].date().isoformat(),
        "count": len(df),
        "first_price": float(closes.iloc[0]),
        "last_price": float(closes.iloc[-1]),
        "ath": ath,
        "ath_date": closes.idxmax().date().isoformat(),
        "gain_pct": (float(closes.iloc[-1]) / float(closes.iloc[0]) - 1) * 100,
        "points": [{"date": d.date().isoformat(), "close": float(c)}
                   for d, c in zip(df.index, closes)],
    }


@app.get("/api/model")
def model_info():
    tp_path = os.path.join(MODEL_DIR, "test_predictions.csv")
    test_predictions = []
    if os.path.exists(tp_path):
        tp = pd.read_csv(tp_path, parse_dates=["date"])
        test_predictions = [
            {"date": d.date().isoformat(), "actual": float(a),
             "predicted": float(p)}
            for d, a, p in zip(tp["date"], tp["actual"], tp["predicted"])
        ]
    return {
        "hyperparams": state["config"],
        "metrics": state["metrics"],
        "comparison": THESIS_COMPARISON,
        "test_predictions": test_predictions,
    }
