export function formatDecimal(value: number, digits = 3): string {
  return new Intl.NumberFormat("en-US", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  }).format(value);
}

export function formatSigned(value: number, digits = 3): string {
  const formatted = formatDecimal(Math.abs(value), digits);
  return `${value >= 0 ? "+" : "−"}${formatted}`;
}

export function humanizeIdentifier(value: string): string {
  return value.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

export function shortHash(value: string): string {
  return `${value.slice(0, 8)}…${value.slice(-8)}`;
}
