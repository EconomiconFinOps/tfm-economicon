import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { describe, expect, it } from "vitest";
import { billing } from "../../tests/fixtures";
import { jsonResponse, mockBackend } from "../../tests/test-support";
import { advanceSessionGeneration } from "../services/api";
import { billingFilterKeys } from "../services/contracts";
import type { BillingSelection } from "../services/contracts";
import { useCostKpis } from "./useCostKpis";

describe("operational cost query scopes", () => {
  it("keys all five filters, period, grouping, tag, tenant and session independently", async () => {
    const { requests } = mockBackend({ "GET /billing/summary": (request) => {
      const filters = Object.fromEntries(billingFilterKeys.filter((key) => request.search.has(key)).map((key) => [key, request.search.get(key)]));
      return jsonResponse({ ...billing,
        period: { start_date: request.search.get("start_date"), end_date: request.search.get("end_date"), timezone: "UTC" },
        group_by: request.search.get("group_by"), tag_key: request.search.get("tag_key"),
        ...(Object.keys(filters).length ? { filters } : {}) });
    } });
    // Infinite freshness makes missing cache-key fields observable: changing
    // any scope must fetch, even while every old response is still fresh.
    const client = new QueryClient({ defaultOptions: { queries: { retry: false, staleTime: Infinity, gcTime: Infinity } } });
    const wrapper = ({ children }: { children: ReactNode }) => <QueryClientProvider client={client}>{children}</QueryClientProvider>;
    let selection: BillingSelection = { start_date: "2024-06-01", end_date: "2024-07-01", group_by: "service" };
    let tenantId = "tenant-1";
    const { result, rerender, unmount } = renderHook((props) => useCostKpis({ token: "test-token", ...props }), { wrapper, initialProps: { selection, tenantId } });
    try {
      await waitFor(() => expect(result.current.isSuccess).toBe(true));
      const selections: BillingSelection[] = [
        { ...selection, subscription_id: "sub-1" }, { ...selection, service_name: "Compute" }, { ...selection, project: "A" },
        { ...selection, filter_tag_key: "environment", filter_tag_value: "production" },
        { ...selection, filter_tag_key: "project", filter_tag_value: "production" },
        { ...selection, filter_tag_key: "project", filter_tag_value: "staging" },
        { ...selection, start_date: "2024-06-02" }, { ...selection, end_date: "2024-07-02" },
        { ...selection, group_by: "project" }, { ...selection, group_by: "tag", tag_key: "environment" },
        { ...selection, group_by: "tag", tag_key: "project" }
      ];
      for (const next of selections) {
        const previousCount = requests.length;
        selection = next; rerender({ selection, tenantId });
        await waitFor(() => expect(result.current.isSuccess).toBe(true));
        expect(requests).toHaveLength(previousCount + 1);
      }
      let previousCount = requests.length;
      tenantId = "tenant-2"; rerender({ selection, tenantId });
      await waitFor(() => expect(result.current.isSuccess).toBe(true));
      expect(requests).toHaveLength(previousCount + 1);
      previousCount = requests.length;
      advanceSessionGeneration(); rerender({ selection, tenantId });
      await waitFor(() => expect(result.current.isSuccess).toBe(true));
      expect(requests).toHaveLength(previousCount + 1);
      expect(JSON.stringify(client.getQueryCache().getAll().map((query) => query.queryKey))).not.toContain("test-token");
    } finally { unmount(); client.clear(); }
  });
});
