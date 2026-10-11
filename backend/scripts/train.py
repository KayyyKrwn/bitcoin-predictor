"""
Training N-BEATS untuk prediksi harga Bitcoin (BTC-USD).

Pipeline disamakan dengan notebook skripsi NBEATS_Bitcoin_Adam.ipynb:
- Data: BTC-USD harian dari Yahoo Finance (univariat, kolom Close)
- Scaling: MinMaxScaler (fit HANYA di data train)
- Split kronologis: 80% train(+val) / 20% test ; val = 20% terakhir train
- Window: lookback=10 -> prediksi 1 hari ke depan (horizon=1)
- Model: N-BEATS (n_blocks=4, units=128), Adam(lr=0.001), loss MSE,
         batch 16, epochs 50, early stopping

Output di folder models/:
- nbeats_weights.weights.h5  (bobot model)
- scaler.json                (parameter MinMaxScaler)
- config.json                (hyperparameter)
- metrics.json               (MSE/RMSE/MAE/MAPE/R2 di test set)
- test_predictions.csv       (tanggal, aktual, prediksi di test set)

Jalankan:  .venv/bin/python scripts/train.py
"""
import json
import os
import sys
import time

import numpy as np
import pandas as pd
import yfinance as yf
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.callbacks import EarlyStopping

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from nbeats_model import build_nbeats

# ---------------- Konfigurasi (hyperparameter juara skripsi) ----------------
TICKER = "BTC-USD"
START_DATE = "2014-09-17"   # data BTC-USD tertua yang tersedia di Yahoo Finance
LOOKBACK = 10
HORIZON = 1
N_BLOCKS = 4
UNITS = 128
LEARNING_RATE = 0.001
BATCH_SIZE = 16
EPOCHS = 50
PATIENCE = 8
TEST_RATIO = 0.20
VAL_RATIO = 0.20
SEED = 42

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "data", "btc_usd_daily.csv")
MODEL_DIR = os.path.join(BASE_DIR, "models")


def fetch_data(retries=5):
    """Ambil BTC-USD harian dari Yahoo Finance, dengan retry."""
    for attempt in range(1, retries + 1):
        try:
            df = yf.download(TICKER, start=START_DATE, progress=False,
                             auto_adjust=False)
            if df is not None and len(df) > 100:
                # yfinance baru kadang mengembalikan kolom MultiIndex
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)
                df = df[["Close"]].dropna()
                df.index = pd.to_datetime(df.index).tz_localize(None)
                return df
        except Exception as e:  # noqa: BLE001
            print(f"Percobaan {attempt} gagal: {e}")
        time.sleep(5 * attempt)
    raise RuntimeError("Gagal mengunduh data dari Yahoo Finance setelah "
                       f"{retries} percobaan.")


def create_dataset(series, lookback):
    X, y = [], []
    for i in range(lookback, len(series)):
        X.append(series[i - lookback:i, 0])
        y.append(series[i, 0])
    return np.array(X), np.array(y)


def main():
    np.random.seed(SEED)
    os.makedirs(MODEL_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)

    print("1/6 Mengunduh data BTC-USD dari Yahoo Finance ...")
    df = fetch_data()
    df.to_csv(DATA_PATH)
    print(f"    {len(df)} baris harian: {df.index[0].date()} s/d "
          f"{df.index[-1].date()} -> {DATA_PATH}")

    close = df["Close"].to_numpy(dtype=float).reshape(-1, 1)

    print("2/6 Split kronologis train/val/test ...")
    n = len(close)
    test_len = int(n * TEST_RATIO)
    train_val = close[:n - test_len]
    test_raw = close[n - test_len - LOOKBACK:]  # sertakan lookback utk window test

    scaler = MinMaxScaler()
    train_val_scaled = scaler.fit_transform(train_val)
    test_scaled = scaler.transform(test_raw)

    X_full, y_full = create_dataset(train_val_scaled, LOOKBACK)
    val_len = int(len(X_full) * VAL_RATIO)
    X_train, y_train = X_full[:-val_len], y_full[:-val_len]
    X_val, y_val = X_full[-val_len:], y_full[-val_len:]
    X_test, y_test_scaled = create_dataset(test_scaled, LOOKBACK)
    test_dates = df.index[n - test_len:]

    print(f"    train={len(X_train)} val={len(X_val)} test={len(X_test)}")

    print("3/6 Membangun model N-BEATS ...")
    import tensorflow as tf
    tf.random.set_seed(SEED)
    model = build_nbeats(lookback=LOOKBACK, horizon=HORIZON,
                         n_blocks=N_BLOCKS, units=UNITS,
                         learning_rate=LEARNING_RATE)
    model.summary(print_fn=lambda s: print("    " + s))

    print("4/6 Training ...")
    es = EarlyStopping(monitor="val_loss", patience=PATIENCE,
                       restore_best_weights=True, verbose=1)
    model.fit(X_train, y_train, validation_data=(X_val, y_val),
              epochs=EPOCHS, batch_size=BATCH_SIZE, callbacks=[es], verbose=2)

    print("5/6 Evaluasi di test set (skala harga asli) ...")
    pred_scaled = model.predict(X_test, verbose=0).reshape(-1, 1)
    y_pred = scaler.inverse_transform(pred_scaled).ravel()
    y_true = scaler.inverse_transform(y_test_scaled.reshape(-1, 1)).ravel()

    mse = mean_squared_error(y_true, y_pred)
    rmse = float(np.sqrt(mse))
    mae = float(mean_absolute_error(y_true, y_pred))
    mape = float(np.mean(np.abs((y_true - y_pred) / y_true)) * 100)
    r2 = float(r2_score(y_true, y_pred))
    metrics = {"MSE": mse, "RMSE": rmse, "MAE": mae, "MAPE": mape, "R2": r2,
               "n_test": len(y_true),
               "test_start": str(test_dates[0].date()),
               "test_end": str(test_dates[-1].date())}
    print(f"    MSE  : {mse:,.2f}\n    RMSE : {rmse:,.2f}\n"
          f"    MAE  : {mae:,.2f}\n    MAPE : {mape:.4f} %\n    R2   : {r2:.4f}")

    print("6/6 Menyimpan artefak ...")
    weights_path = os.path.join(MODEL_DIR, "nbeats_weights.weights.h5")
    model.save_weights(weights_path)
    with open(os.path.join(MODEL_DIR, "scaler.json"), "w") as f:
        json.dump({"data_min": float(scaler.data_min_[0]),
                   "data_max": float(scaler.data_max_[0]),
                   "data_range": float(scaler.data_range_[0])}, f, indent=2)
    with open(os.path.join(MODEL_DIR, "config.json"), "w") as f:
        json.dump({"ticker": TICKER, "lookback": LOOKBACK, "horizon": HORIZON,
                   "n_blocks": N_BLOCKS, "units": UNITS,
                   "learning_rate": LEARNING_RATE, "batch_size": BATCH_SIZE,
                   "epochs": EPOCHS}, f, indent=2)
    with open(os.path.join(MODEL_DIR, "metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2)
    pd.DataFrame({"date": test_dates, "actual": y_true,
                  "predicted": y_pred}).to_csv(
        os.path.join(MODEL_DIR, "test_predictions.csv"), index=False)
    print(f"    tersimpan di {MODEL_DIR}/")
    print("\nSELESAI.")


if __name__ == "__main__":
    main()
