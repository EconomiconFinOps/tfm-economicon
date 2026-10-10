import { defaultMonthSelection, monthlyPeriod } from "./executiveCostDashboard";
import { billingFilterKeys, canonicalBillingTagKey, validBillingFilterValue } from "../services/contracts";
import type { BillingGrouping, BillingSelection, BillingSummary } from "../services/contracts";

export interface OperationalSelection {
  start_date: string;
  end_date: string;
  group_by: BillingGrouping;
  tag_key: string;
  subscription_id: string;
  service_name: string;
  project: string;
  filter_tag_key: string;
  filter_tag_value: string;
}

export function defaultOperationalSelection(): OperationalSelection {
  return { ...monthlyPeriod(defaultMonthSelection().last), group_by: "service", tag_key: "",
    subscription_id: "", service_name: "", project: "", filter_tag_key: "", filter_tag_value: "" };
}

function validDate(value: string): boolean {
  return /^\d{4}-\d{2}-\d{2}$/.test(value) && value >= "0001-01-01" && value <= "9999-12-31"
    && !Number.isNaN(Date.parse(value)) && new Date(value).toISOString().slice(0, 10) === value;
}

export function operationalSelectionError(selection: OperationalSelection): string | null {
  if (!validDate(selection.start_date) || !validDate(selection.end_date) || selection.start_date >= selection.end_date) {
    return "Indica fechas válidas, con inicio anterior al fin. El día final queda excluido.";
  }
  if (billingFilterKeys.some((key) => selection[key] !== "" && !validBillingFilterValue(selection[key]))) {
    return "Los filtros no pueden contener solo espacios ni caracteres de control.";
  }
  if (Boolean(selection.filter_tag_key) !== Boolean(selection.filter_tag_value)) return "Para filtrar por etiqueta, indica su clave y su valor.";
  if (selection.filter_tag_key && !canonicalBillingTagKey(selection.filter_tag_key)) return "La clave de etiqueta debe contener letras o números válidos.";
  if (selection.group_by === "tag" && (!validBillingFilterValue(selection.tag_key) || !canonicalBillingTagKey(selection.tag_key))) {
    return "Indica una clave válida para agrupar por etiqueta.";
  }
  return null;
}

export function operationalBillingSelection(selection: OperationalSelection): BillingSelection {
  const request: BillingSelection = { start_date: selection.start_date, end_date: selection.end_date, group_by: selection.group_by };
  if (selection.group_by === "tag") request.tag_key = canonicalBillingTagKey(selection.tag_key);
  for (const key of billingFilterKeys) {
    if (selection[key] !== "") request[key] = key === "filter_tag_key" ? canonicalBillingTagKey(selection[key]) : selection[key];
  }
  return request;
}

export function checkOperationalMetadata(data: BillingSummary, selection: BillingSelection): void {
  const expectedTag = selection.group_by === "tag" ? canonicalBillingTagKey(selection.tag_key ?? "") : null;
  const expectedFilters = billingFilterKeys.filter((key) => selection[key] !== undefined);
  if (data.period.start_date !== selection.start_date || data.period.end_date !== selection.end_date
    || data.period.timezone !== "UTC" || data.group_by !== selection.group_by || data.tag_key !== expectedTag
    || Object.keys(data.filters ?? {}).length !== expectedFilters.length
    || expectedFilters.some((key) => data.filters?.[key] !== (key === "filter_tag_key"
      ? canonicalBillingTagKey(selection[key]!) : selection[key]))) {
    throw new Error("Respuesta de costes incompatible");
  }
}

// CSV is scoped to one confirmed response. Quote CSV delimiters and neutralize
// formula-like text from upstream dimensions; decimal amounts remain exact.
function csvCell(value: string, numeric = false): string {
  const safe = !numeric && /^[\s]*[=+\-@\t\r]/.test(value) ? "'" + value : value;
  return '"' + safe.replace(/"/g, '""') + '"';
}

export function operationalCostCsv(data: BillingSummary, tenantId: string): string {
  const headings = ["tipo", "cliente_id", "desde_UTC_incluido", "hasta_UTC_excluido", "agrupacion", "etiqueta_agrupacion",
    ...billingFilterKeys, "estado", "sin_dimension", "sin_fecha_cliente", "dimension", "suscripcion_grupo", "moneda", "coste", "registros"];
  const prefix = [tenantId, data.period.start_date, data.period.end_date, data.group_by, data.tag_key ?? "",
    ...billingFilterKeys.map((key) => data.filters?.[key] ?? ""), data.data_status, String(data.missing_dimension_count), String(data.excluded_undated_count)];
  const rows = [
    ...data.totals.map((total) => ["total", ...prefix, "", "", total.currency, total.cost, String(total.record_count)]),
    ...data.groups.map((group) => ["grupo", ...prefix, group.value ?? "", group.subscription_id ?? "", group.currency, group.cost, String(group.record_count)])
  ];
  return [headings.map((value) => csvCell(value)).join(","), ...rows.map((row) => row.map((value, index) => csvCell(value, index >= row.length - 2)).join(","))].join("\r\n");
}

export function downloadOperationalCosts(data: BillingSummary, tenantId: string): void {
  const url = URL.createObjectURL(new Blob(["\uFEFF" + operationalCostCsv(data, tenantId)], { type: "text/csv;charset=utf-8;" }));
  const link = document.createElement("a");
  link.href = url;
  link.download = `coste-operativo-${data.period.start_date}-${data.period.end_date}.csv`;
  link.click();
  // Let the browser consume the blob before releasing its URL.
  setTimeout(() => URL.revokeObjectURL(url), 0);
}
