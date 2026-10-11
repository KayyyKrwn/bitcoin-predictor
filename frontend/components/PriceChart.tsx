"use client";

import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { fmtUSD, fmtDate } from "@/lib/format";

export interface ChartPoint {
  date: string;
  close?: number | null;
  actual?: number;
  predicted?: number | null;
}

interface Props {
  data: ChartPoint[];
  height?: number;
  logScale?: boolean;
  showPredictedLine?: boolean;
}

function ChartTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-lg border border-white/10 bg-zinc-900 px-3 py-2 text-sm shadow-xl">
      <div className="mb-1 text-xs text-white/50">{fmtDate(String(label))}</div>
      {payload.map((p: any) => (
        <div key={p.dataKey} className="flex items-center gap-2">
          <span
            className="h-2 w-2 rounded-full"
            style={{ background: p.color || p.stroke }}
          />
          <span className="text-white/70">{p.name}:</span>
          <span className="font-semibold">{fmtUSD(Number(p.value))}</span>
        </div>
      ))}
    </div>
  );
}

export default function PriceChart({
  data,
  height = 380,
  logScale = false,
  showPredictedLine = false,
}: Props) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={data} margin={{ top: 8, right: 8, bottom: 8, left: 8 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
        <XAxis
          dataKey="date"
          tickFormatter={(d: string) =>
            new Date(d + "T00:00:00").toLocaleDateString("id-ID", {
              month: "short",
              year: "2-digit",
            })
          }
          minTickGap={60}
          tick={{ fill: "rgba(255,255,255,0.5)", fontSize: 12 }}
          axisLine={{ stroke: "rgba(255,255,255,0.15)" }}
          tickLine={false}
        />
        <YAxis
          scale={logScale ? "log" : "auto"}
          domain={logScale ? ["auto", "auto"] : ["auto", "auto"]}
          tickFormatter={(v: number) =>
            v >= 1000 ? `$${Math.round(v / 1000)}k` : `$${v}`
          }
          tick={{ fill: "rgba(255,255,255,0.5)", fontSize: 12 }}
          axisLine={false}
          tickLine={false}
          width={64}
        />
        <Tooltip content={<ChartTooltip />} />
        {(data[0]?.close !== undefined || data[0]?.actual !== undefined) && (
          <Line
            type="monotone"
            dataKey={data[0]?.close !== undefined ? "close" : "actual"}
            name="Aktual"
            stroke="#f59e0b"
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4 }}
          />
        )}
        {showPredictedLine && (
          <Line
            type="monotone"
            dataKey="predicted"
            name="Prediksi"
            stroke="#38bdf8"
            strokeWidth={2}
            strokeDasharray="6 4"
            dot={false}
            activeDot={{ r: 4 }}
            connectNulls
          />
        )}
      </LineChart>
    </ResponsiveContainer>
  );
}
