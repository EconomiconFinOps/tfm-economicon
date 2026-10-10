import { ApiError } from "../services/api";
import type { BillingSummary } from "../services/contracts";

export interface MonthRange {
  months: string[];
  start_date: string;
  end_date: string;
}
export type SummaryOutcome =
  | { kind: "success"; data: BillingSummary }
  | { kind: "error"; error: unknown };
export interface ExecutiveSnapshot {
  aggregate: SummaryOutcome;
  months: { month: string; result: SummaryOutcome }[];
}
export interface MonthlyCostPoint {
  month: string;
  label: string;
  cost: string | null;
  value: number | null;
  recordCount: number | null;
  state: "available" | "empty" | "error";
  partial: boolean;
  missingDimensions: number;
  undated: number;
  representationLimited: boolean;
  notice: string;
}
export type EndpointComparison =
  | { available: false; reason: string }
  | {
      available: true; firstMonth: string; lastMonth: string; difference: string; percent: string;
      negativeBase: boolean; partial: boolean; interiorErrors: boolean;
    };

const MONTH_NAMES = [
  "enero", "febrero", "marzo", "abril", "mayo", "junio",
  "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
];

function monthIndex(value: string): number | null {
  if (!/^\d{4}-(0[1-9]|1[0-2])$/.test(value)) return null;
  const year = Number(value.slice(0, 4));
  if (year < 1 || year > 9998) return null;
  return year * 12 + Number(value.slice(5, 7)) - 1;
}

function monthFromIndex(index: number): string {
  return String(Math.floor(index / 12)).padStart(4, "0") + "-" + String(index % 12 + 1).padStart(2, "0");
}

export function defaultMonthSelection(now = new Date()) {
  const current = now.getUTCFullYear() * 12 + now.getUTCMonth();
  return { first: monthFromIndex(current - 6), last: monthFromIndex(current - 1) };
}

export function selectedMonthRange(first: string, last: string): MonthRange | null {
  const from = monthIndex(first);
  const to = monthIndex(last);
  if (from === null || to === null || from > to) return null;
  return {
    months: Array.from({ length: to - from + 1 }, (_, index) => monthFromIndex(from + index)),
    start_date: first + "-01",
    end_date: monthFromIndex(to + 1) + "-01"
  };
}

export function monthlyPeriod(month: string) {
  const index = monthIndex(month);
  if (index === null) throw new Error("Mes no válido");
  return { start_date: month + "-01", end_date: monthFromIndex(index + 1) + "-01" };
}

export function monthLabel(month: string): string {
  return MONTH_NAMES[Number(month.slice(5, 7)) - 1] + " de " + month.slice(0, 4);
}

export function currentUtcMonth(now = new Date()): string {
  return monthFromIndex(now.getUTCFullYear() * 12 + now.getUTCMonth());
}

// Billing v2 has already rounded each query to two decimal places. Preserve
// those exact cents; only the graph may convert a safe integer to Number.
export function costCents(cost: string): bigint {
  if (!/^-?(0|[1-9][0-9]*)\.[0-9]{2}$/.test(cost) || cost === "-0.00") {
    throw new Error("Importe no válido");
  }
  return BigInt(cost.replace(".", ""));
}

function absolute(value: bigint): bigint {
  return value < 0n ? -value : value;
}

function centsText(value: bigint, signed = false): string {
  const magnitude = absolute(value);
  const sign = value < 0n ? "-" : signed && value > 0n ? "+" : "";
  return sign + String(magnitude / 100n) + "." + String(magnitude % 100n).padStart(2, "0");
}

export function describeCostError(error: unknown): string {
  if (error instanceof ApiError && error.status === 409 && error.message.includes("ambiguous_cost_source")) {
    return "Posible solapamiento de fuentes de ingesta. Costes no disponibles para este periodo.";
  }
  if (error instanceof Error && error.message === "Respuesta de costes incompatible") {
    return "Error: respuesta de costes incompatible con la selección.";
  }
  return "Error al cargar costes. Datos no disponibles.";
}

export function snapshotCurrencies(snapshot: ExecutiveSnapshot): string[] {
  const observed = new Set<string>();
  const outcomes = [snapshot.aggregate, ...snapshot.months.map(({ result }) => result)];
  for (const result of outcomes) {
    if (result.kind === "success") {
      for (const item of result.data.totals) {
        if (item.record_count > 0) observed.add(item.currency);
      }
    }
  }
  return [...observed].sort();
}

export function monthlyCostPoint(month: string, result: SummaryOutcome, currency: string): MonthlyCostPoint {
  const base = {
    month, label: monthLabel(month), cost: null, value: null, recordCount: null,
    partial: false, missingDimensions: 0, undated: 0, representationLimited: false
  };
  if (result.kind === "error") {
    return { ...base, state: "error", notice: describeCostError(result.error) };
  }
  const total = result.data.totals.find((item) => item.currency === currency && item.record_count > 0);
  const metadata = {
    partial: result.data.data_status === "partial",
    missingDimensions: result.data.missing_dimension_count,
    undated: result.data.excluded_undated_count
  };
  if (!total) return { ...base, ...metadata, state: "empty", notice: "Sin datos de esta moneda." };
  const cents = costCents(total.cost);
  const limited = absolute(cents) > BigInt(Number.MAX_SAFE_INTEGER);
  return {
    ...base, ...metadata, state: "available", cost: total.cost, recordCount: total.record_count,
    value: limited ? null : Number(cents) / 100,
    representationLimited: limited,
    notice: limited ? "Fuera del límite de representación gráfica; valor exacto en tabla."
      : metadata.partial ? "Datos parciales" : "Coste observado"
  };
}

export function compareEndpoints(points: MonthlyCostPoint[], currency: string): EndpointComparison {
  let firstIndex = -1;
  let lastIndex = -1;
  let firstError = -1;
  let lastError = -1;
  let base = 0n;
  let finalCost = 0n;
  let partial = false;
  // Points are already chronological. Select exact observed costs without
  // filtering the full monthly series or using its limited graph values.
  for (let index = 0; index < points.length; index++) {
    const point = points[index];
    if (point.state === "error") {
      if (firstError === -1) firstError = index;
      lastError = index;
      continue;
    }
    partial ||= point.partial;
    if (!currency || point.cost === null) continue;
    const cents = costCents(point.cost);
    if (cents === 0n) continue;
    if (firstIndex === -1) {
      firstIndex = index;
      base = cents;
    }
    lastIndex = index;
    finalCost = cents;
  }

  let blockingError = -1;
  if (firstError !== -1) {
    // With fewer than two costs, any error can hide another eligible month.
    // Otherwise only errors outside the observed endpoints hide true edges.
    if (firstIndex === lastIndex || firstError < firstIndex) blockingError = firstError;
    else if (lastError > lastIndex) blockingError = lastError;
  }
  if (blockingError !== -1) {
    const failed = points[blockingError];
    return {
      available: false,
      reason: monthLabel(failed.month) + ": " + failed.notice
        + " No se pueden determinar los meses con coste de este periodo."
    };
  }
  if (firstIndex === -1) return { available: false, reason: "No hay meses con coste en este periodo" };
  if (firstIndex === lastIndex) return { available: false, reason: "Solo hay un mes con coste para comparar" };

  const difference = finalCost - base;
  // An eligible base cannot be zero. Preserve the original exact rounding:
  // hundredths of a percent, halves away from zero, then restore the sign.
  const numerator = difference * 10000n;
  const denominator = absolute(base);
  const magnitude = absolute(numerator);
  let rounded = magnitude / denominator;
  if ((magnitude % denominator) * 2n >= denominator) rounded += 1n;
  const negative = (numerator < 0n) !== (base < 0n);
  return {
    available: true,
    firstMonth: points[firstIndex].month, lastMonth: points[lastIndex].month,
    difference: centsText(difference, true), percent: centsText(negative ? -rounded : rounded, true),
    negativeBase: base < 0n, partial, interiorErrors: firstError !== -1
  };
}
