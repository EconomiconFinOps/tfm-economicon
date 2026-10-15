import { createContext, useContext, useLayoutEffect, useMemo, type ReactNode } from "react";
import { useLocation } from "react-router";
import { PreparedScreen, type ScreenCapture } from "../../services/screenCapture";
import type { BillingSummary } from "../../services/contracts";

const ScreenContext = createContext<{ prepared: PreparedScreen | null; route: string } | null>(null);
export type FunctionalScreen = Pick<ScreenCapture, "source" | "selection" | "datasets">;
export function ScreenCaptureProvider({ tenantId, userId, token, children }: {
  tenantId?: string; userId?: string; token?: string; children: ReactNode;
}) {
  const location = useLocation();
  const prepared = useMemo(() => tenantId && userId && token ? new PreparedScreen(tenantId, userId) : null,
    [tenantId, userId, token]);
  // Child adapters prepare their current result first; preserve it. A route
  // without an adapter receives an explicit empty descriptor for that route.
  useLayoutEffect(() => { prepared?.ensureRoute(location.pathname); }, [prepared, location.pathname]);
  const value = useMemo(() => ({ prepared, route: location.pathname }), [prepared, location.pathname]);
  return <ScreenContext.Provider value={value}>{children}</ScreenContext.Provider>;
}
export function usePreparedScreen() { return useContext(ScreenContext)?.prepared ?? null; }
export function useFunctionalScreen(data: FunctionalScreen) {
  const context = useContext(ScreenContext);
  const prepared = context?.prepared, route = context?.route;
  // Standalone existing screens keep working without the workspace provider.
  useLayoutEffect(() => { if (route) prepared?.prepare(route, data); }, [prepared, route, data]);
}
export function demoDataset(source: string, groups: { label: string; amount: string; currency: string; record_count?: number }[],
  selection: Record<string, unknown> = {}, missing: string[] = [], totals: { amount: string; currency: string }[] = []) {
  return { source, load_state: groups.length ? "loaded" : "empty", loaded_at: new Date().toISOString(),
    selection, data_environment: "demo", completeness: { status: missing.length ? "partial" : groups.length ? "complete" : "empty", missing_dimensions: missing },
    totals, groups, series: [], counts: { records: groups.length, groups: groups.length, series: 0 } };
}
export function billingDataset(summary: BillingSummary) {
  const missing = summary.missing_dimension_count ? ["grouping_dimension"] : [];
  return { source: "billing-summary-v2", data_environment: "unknown",
    load_state: summary.data_status === "partial" ? "partial" : summary.data_status === "empty" ? "empty" : "loaded",
    loaded_at: new Date().toISOString(),
    selection: { period: summary.period, group_by: summary.group_by, tag_key: summary.tag_key },
    completeness: { status: summary.data_status === "available" ? "complete" : summary.data_status,
      missing_dimensions: missing, excluded_undated_count: summary.excluded_undated_count },
    totals: summary.totals.map(row => ({ currency: row.currency, amount: row.cost, record_count: row.record_count })),
    groups: summary.groups.map(row => ({ label: row.value ?? "", subscription_id: row.subscription_id,
      currency: row.currency, amount: row.cost, record_count: row.record_count })),
    series: [], counts: { records: summary.totals.reduce((sum, row) => sum + row.record_count, 0),
      groups: summary.groups.length, series: 0 }, missing_dimensions: missing };
}
export function failedBillingDataset(period: BillingSummary["period"], groupBy: BillingSummary["group_by"], tagKey: string | null) {
  return { source: "billing-summary-v2", data_environment: "unknown", load_state: "error", loaded_at: null,
    selection: { period, group_by: groupBy, tag_key: tagKey },
    completeness: { status: "unavailable", missing_dimensions: ["billing_query"] },
    totals: [], groups: [], series: [], counts: { records: 0, groups: 0, series: 0 } };
}
