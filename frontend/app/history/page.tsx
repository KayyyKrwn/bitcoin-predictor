"use client";

import { useEffect, useState } from "react";
import { Card, Skeleton, Button } from "@heroui/react";
import { api, type HistoryResponse } from "@/lib/api";
import { fmtUSD, fmtDate } from "@/lib/format";
import PriceChart from "@/components/PriceChart";

export default function HistoryPage() {
  const [data, setData] = useState<HistoryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [logScale, setLogScale] = useState(false);

  useEffect(() => {
    api
      .history()
      .then(setData)
      .catch(() => setError("Gagal mengambil data. Pastikan backend berjalan."));
  }, []);

  if (error) {
    return (
      <Card variant="secondary" className="border-danger/40">
        <Card.Content>
          <p className="text-danger">⚠️ {error}</p>
        </Card.Content>
      </Card>
    );
  }

  if (!data) {
    return (
      <div className="space-y-6">
        <div className="grid gap-4 md:grid-cols-4">
          {[0, 1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-32 rounded-xl" />
          ))}
        </div>
        <Skeleton className="h-96 rounded-xl" />
      </div>
    );
  }

  const stats = [
    { label: "Harga Pertama", value: fmtUSD(data.first_price), sub: fmtDate(data.start) },
    { label: "Harga Terakhir", value: fmtUSD(data.last_price), sub: fmtDate(data.end) },
    { label: "Tertinggi (ATH)", value: fmtUSD(data.ath), sub: fmtDate(data.ath_date) },
    {
      label: "Kenaikan Total",
      value: `${data.gain_pct.toLocaleString("en-US", { maximumFractionDigits: 0 })}%`,
      sub: "sejak 2014",
    },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Data Historis BTC-USD</h1>
        <p className="mt-1 text-sm text-white/50">
          Yahoo Finance · {fmtDate(data.start)} s/d {fmtDate(data.end)} ·{" "}
          {data.count.toLocaleString("en-US")} baris harian
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        {stats.map((s) => (
          <Card key={s.label}>
            <Card.Header>
              <Card.Title className="text-sm font-medium text-white/60">
                {s.label}
              </Card.Title>
            </Card.Header>
            <Card.Content>
              <p className="text-2xl font-bold">{s.value}</p>
              <p className="mt-1 text-xs text-white/40">{s.sub}</p>
            </Card.Content>
          </Card>
        ))}
      </div>

      <Card>
        <Card.Header>
          <div className="flex items-center justify-between">
            <div>
              <Card.Title>Perjalanan harga Bitcoin</Card.Title>
              <Card.Description>Skala logaritmik cocok untuk rentang 2014–sekarang</Card.Description>
            </div>
            <div className="flex gap-2">
              <Button
                variant={!logScale ? "primary" : "secondary"}
                size="sm"
                onPress={() => setLogScale(false)}
              >
                Linear
              </Button>
              <Button
                variant={logScale ? "primary" : "secondary"}
                size="sm"
                onPress={() => setLogScale(true)}
              >
                Log
              </Button>
            </div>
          </div>
        </Card.Header>
        <Card.Content>
          <PriceChart data={data.points} height={440} logScale={logScale} />
        </Card.Content>
      </Card>

      <p className="text-xs text-white/40">
        Catatan: Yahoo Finance hanya menyimpan BTC-USD mulai 17 September 2014
        (Bitcoin sendiri lahir Januari 2009).
      </p>
    </div>
  );
}
