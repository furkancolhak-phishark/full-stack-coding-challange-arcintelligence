export function formatMoney(value: string | number): string {
  const amount = Number(value);
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(Number.isFinite(amount) ? amount : 0);
}

export function formatSignedMoney(value: string | number): string {
  const amount = Number(value);
  const formatted = formatMoney(Math.abs(amount));
  if (amount > 0) return `+${formatted}`;
  if (amount < 0) return `-${formatted}`;
  return formatted;
}

export function formatPercent(value: number | null): string {
  if (value === null) return "n/a";
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(2)}%`;
}

export function varianceClass(value: string | number): string {
  const amount = Number(value);
  if (amount > 0) return "negativeVariance";
  if (amount < 0) return "positiveVariance";
  return "neutralVariance";
}
