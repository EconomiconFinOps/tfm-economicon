import type { ReferenceDateInfo } from "../services/contracts";

// The reference date arrives as YYYY-MM-DD already validated; every conversion stays in UTC.
export function referenceDay(info: ReferenceDateInfo): Date {
  return new Date(info.reference_date + "T00:00:00Z");
}

export function formatReferenceDate(info: ReferenceDateInfo): string {
  const [year, month, day] = info.reference_date.split("-");
  return `${day}/${month}/${year}`;
}

export function referenceMonth(info: ReferenceDateInfo): { start: string; end: string } {
  const day = referenceDay(info);
  const first = new Date(Date.UTC(day.getUTCFullYear(), day.getUTCMonth(), 1));
  const next = new Date(Date.UTC(day.getUTCFullYear(), day.getUTCMonth() + 1, 1));
  return { start: first.toISOString().slice(0, 10), end: next.toISOString().slice(0, 10) };
}
