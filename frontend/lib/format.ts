export function fmtUSD(x: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 2,
  }).format(x);
}

export function fmtNum(x: number, digits = 2): string {
  return x.toLocaleString("en-US", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}

export function fmtPct(x: number, digits = 2): string {
  return `${x >= 0 ? "+" : ""}${x.toFixed(digits)}%`;
}

export function fmtDate(iso: string): string {
  return new Date(iso + "T00:00:00").toLocaleDateString("id-ID", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

export function fmtDateShort(iso: string): string {
  return new Date(iso + "T00:00:00").toLocaleDateString("id-ID", {
    day: "numeric",
    month: "short",
  });
}
