"use client";

import { useEffect, useState } from "react";
import { Card, Chip, Skeleton } from "@heroui/react";
import { api, type PredictResponse } from "@/lib/api";
import { fmtUSD, fmtPct, fmtDate } from "@/lib/format";
import PriceChart from "@/components/PriceChart";

function LoadingSkeleton() {
  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-3">
        {[0, 1, 2].map((i) => (
          <Skeleton key={i} className="h-36 rounded-xl" />
        ))}
      </div>
      <Skeleton className="h-96 rounded-xl" />
    </div>
  );
}

export default function PredictPage() {
  const [data, setData] = useState<PredictResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .predict()
      .then(setData)
      .catch(() => setError("Gagal mengambil data. Pastikan backend berjalan."));
  }, []);

  if (error) {
    return (
      <Card variant="secondary" className="border-danger/40">
        <Card.Content>
          <p className="text-danger">⚠️ {error}</p>
          <p className="mt-2 text-sm text-white/60">
            Jalankan backend dulu:{" "}
            <code className="rounded bg-white/10 px-1">uvicorn main:app --port 8000</code>{" "}
            dari folder <code className="rounded bg-white/10 px-1">backend/</code>
          </p>
        </Card.Content>
      </Card>
    );
  }

  if (!data) return <LoadingSkeleton />;

  const up = data.delta >= 0;

  // Data grafik: 90 hari aktual + segmen garis putus-putus ke prediksi besok
  const chartData = data.recent.map((p) => ({
    date: p.date,
    close: p.close as number | null,
    predicted: null as number | null,
  }));
  chartData[chartData.length - 1].predicted = data.live_price;
  chartData.push({
    date: data.pred_date,
    close: null,
    predicted: data.pred_price,
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">
          Prediksi Harga Bitcoin
        </h1>
        <p className="mt-1 text-sm text-white/50">
          BTC-USD · Data realtime Yahoo Finance · Update {fmtDate(data.live_date)} ·
          Model N-BEATS (lookback 10 hari)
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <Card.Header>
            <Card.Title>Harga Terakhir</Card.Title>
            <Card.Description>{fmtDate(data.live_date)}</Card.Description>
          </Card.Header>
          <Card.Content>
            <p className="text-3xl font-bold">{fmtUSD(data.live_price)}</p>
          </Card.Content>
        </Card>

        <Card variant="secondary">
          <Card.Header>
            <Card.Title>Prediksi Besok</Card.Title>
            <Card.Description>{fmtDate(data.pred_date)}</Card.Description>
          </Card.Header>
          <Card.Content>
            <p className="text-3xl font-bold text-sky-400">
              {fmtUSD(data.pred_price)}
            </p>
            <div className="mt-2">
              <Chip color={up ? "success" : "danger"} variant="soft">
                {up ? "▲" : "▼"} {fmtUSD(Math.abs(data.delta))} (
                {fmtPct(data.delta_pct)})
              </Chip>
            </div>
          </Card.Content>
        </Card>

        <Card>
          <Card.Header>
            <Card.Title>Akurasi Model</Card.Title>
            <Card.Description>Test set {data.metrics.n_test} hari</Card.Description>
          </Card.Header>
          <Card.Content>
            <p className="text-3xl font-bold">
              {data.metrics.MAPE.toFixed(2)}%
            </p>
            <p className="mt-2 text-sm text-white/50">
              MAPE · R² {data.metrics.R2.toFixed(4)}
            </p>
          </Card.Content>
        </Card>
      </div>

      <Card>
        <Card.Header>
          <Card.Title>Tren 90 hari + prediksi</Card.Title>
          <Card.Description>
            Garis oranye: harga aktual · Garis putus-putus biru: prediksi besok
          </Card.Description>
        </Card.Header>
        <Card.Content>
          <PriceChart data={chartData} showPredictedLine />
        </Card.Content>
      </Card>

      <Card variant="tertiary">
        <Card.Content>
          <p className="text-sm text-white/60">
            ⚠️ <strong>Disclaimer:</strong> ini project portofolio dari hasil
            skripsi, bukan saran investasi. Model memprediksi harga penutupan
            besok dari 10 harga terakhir — harga harian Bitcoin sangat mirip
            harga hari ini, jadi akurasi tinggi tidak berarti bisa mengalahkan
            pasar.
          </p>
        </Card.Content>
      </Card>
    </div>
  );
}
