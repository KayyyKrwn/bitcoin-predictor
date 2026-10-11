"use client";

import { useEffect, useState } from "react";
import { Card, Chip, Skeleton, Table } from "@heroui/react";
import { api, type ModelResponse } from "@/lib/api";
import { fmtNum, fmtDate } from "@/lib/format";
import PriceChart from "@/components/PriceChart";

export default function ModelPage() {
  const [data, setData] = useState<ModelResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .model()
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
        <Skeleton className="h-48 rounded-xl" />
        <Skeleton className="h-64 rounded-xl" />
        <Skeleton className="h-96 rounded-xl" />
      </div>
    );
  }

  const m = data.metrics;
  const hp = data.hyperparams;
  const hpRows: [string, string][] = [
    ["Lookback", `${hp.lookback} hari`],
    ["Horizon", `${hp.horizon} hari ke depan`],
    ["Jumlah block", String(hp.n_blocks)],
    ["Units per block", String(hp.units)],
    ["Optimizer", `Adam (lr=${hp.learning_rate})`],
    ["Loss", "MSE"],
    ["Batch size", String(hp.batch_size)],
    ["Input", "Univariat: harga Close (MinMaxScaler)"],
  ];

  const metricCards = [
    { label: "RMSE", value: fmtNum(m.RMSE) },
    { label: "MAE", value: fmtNum(m.MAE) },
    { label: "MAPE", value: `${m.MAPE.toFixed(2)}%` },
    { label: "R²", value: m.R2.toFixed(4) },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Model & Hasil Skripsi</h1>
        <p className="mt-1 text-sm text-white/50">
          Arsitektur, hyperparameter, dan perbandingan 8 eksperimen skripsi
        </p>
      </div>

      <Card>
        <Card.Header>
          <Card.Title>N-BEATS</Card.Title>
          <Card.Description>
            Neural Basis Expansion Analysis for Time Series
          </Card.Description>
        </Card.Header>
        <Card.Content>
          <p className="text-sm leading-relaxed text-white/70">
            Arsitektur feedforward khusus time series. Tiap <em>block</em>{" "}
            memecah input jadi dua: <em>backcast</em> (bagian yang berhasil
            dijelaskan block ini, dikurangkan dari sisa/residual) dan{" "}
            <em>forecast</em> (kontribusi prediksi, dijumlahkan). Beberapa block
            ditumpuk secara residual. Model yang di-deploy memakai
            hyperparameter juara dari skripsi dan di-training ulang dengan data
            realtime.
          </p>
        </Card.Content>
      </Card>

      <Card>
        <Card.Header>
          <Card.Title>Hyperparameter</Card.Title>
          <Card.Description>Konfigurasi juara (N-BEATS + Adam)</Card.Description>
        </Card.Header>
        <Card.Content>
          <Table>
            <Table.ScrollContainer>
              <Table.Content aria-label="Hyperparameter" className="min-w-[400px]">
                <Table.Header>
                  <Table.Column>Parameter</Table.Column>
                  <Table.Column>Nilai</Table.Column>
                </Table.Header>
                <Table.Body>
                  {hpRows.map(([k, v]) => (
                    <Table.Row key={k}>
                      <Table.Cell className="text-white/60">{k}</Table.Cell>
                      <Table.Cell className="font-medium">{v}</Table.Cell>
                    </Table.Row>
                  ))}
                </Table.Body>
              </Table.Content>
            </Table.ScrollContainer>
          </Table>
        </Card.Content>
      </Card>

      <Card>
        <Card.Header>
          <Card.Title>Perbandingan hasil skripsi</Card.Title>
          <Card.Description>
            8 eksperimen utama (tuning manual, test set) · N-BEATS + Adam terbaik
          </Card.Description>
        </Card.Header>
        <Card.Content>
          <Table>
            <Table.ScrollContainer>
              <Table.Content aria-label="Perbandingan model" className="min-w-[700px]">
                <Table.Header>
                  <Table.Column>Model</Table.Column>
                  <Table.Column>Optimizer</Table.Column>
                  <Table.Column>RMSE</Table.Column>
                  <Table.Column>MAE</Table.Column>
                  <Table.Column>MAPE (%)</Table.Column>
                  <Table.Column>R²</Table.Column>
                </Table.Header>
                <Table.Body>
                  {data.comparison.map((r) => (
                    <Table.Row key={`${r.model}-${r.optimizer}`}>
                      <Table.Cell>
                        <span className="flex items-center gap-2">
                          {r.model}
                          {r.best && (
                            <Chip color="success" size="sm" variant="soft">
                              Terbaik
                            </Chip>
                          )}
                        </span>
                      </Table.Cell>
                      <Table.Cell>{r.optimizer}</Table.Cell>
                      <Table.Cell>{fmtNum(r.rmse)}</Table.Cell>
                      <Table.Cell>{fmtNum(r.mae)}</Table.Cell>
                      <Table.Cell>{r.mape.toFixed(2)}</Table.Cell>
                      <Table.Cell>{r.r2.toFixed(4)}</Table.Cell>
                    </Table.Row>
                  ))}
                </Table.Body>
              </Table.Content>
            </Table.ScrollContainer>
          </Table>
        </Card.Content>
      </Card>

      <div>
        <h2 className="mb-3 text-xl font-semibold">
          Performa model yang di-deploy
        </h2>
        <p className="mb-4 text-sm text-white/50">
          Test set: {fmtDate(m.test_start)} s/d {fmtDate(m.test_end)} (
          {m.n_test.toLocaleString("en-US")} hari)
        </p>
        <div className="grid gap-4 md:grid-cols-4">
          {metricCards.map((c) => (
            <Card key={c.label}>
              <Card.Header>
                <Card.Title className="text-sm font-medium text-white/60">
                  {c.label}
                </Card.Title>
              </Card.Header>
              <Card.Content>
                <p className="text-2xl font-bold">{c.value}</p>
              </Card.Content>
            </Card>
          ))}
        </div>
      </div>

      <Card>
        <Card.Header>
          <Card.Title>Aktual vs Prediksi (test set)</Card.Title>
          <Card.Description>Garis putus-putus: prediksi N-BEATS</Card.Description>
        </Card.Header>
        <Card.Content>
          <PriceChart data={data.test_predictions} showPredictedLine />
        </Card.Content>
      </Card>
    </div>
  );
}
