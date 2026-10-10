import { useQuery } from "@tanstack/react-query";
import { fetchBillingSummary, getSessionGeneration } from "../services/api";
import type { BillingSelection } from "../services/contracts";
import { checkOperationalMetadata } from "../lib/operationalCostDashboard";

interface CostKpisOptions {
  token: string;
  tenantId?: string;
  selection: BillingSelection;
  enabled?: boolean;
}

export function useCostKpis({ token, tenantId, selection, enabled = true }: CostKpisOptions) {
  const generation = getSessionGeneration();
  return useQuery({
    queryKey: ["billing-summary", tenantId, 2, generation,
      selection.start_date, selection.end_date, selection.group_by, selection.tag_key,
      selection.subscription_id, selection.service_name, selection.project, selection.filter_tag_key, selection.filter_tag_value],
    queryFn: async ({ signal }) => {
      if (!tenantId) throw new Error("Tenant required");
      const data = await fetchBillingSummary(token, tenantId, selection, signal);
      if (signal.aborted || generation !== getSessionGeneration()) throw new DOMException("Consulta cancelada", "AbortError");
      checkOperationalMetadata(data, selection);
      return data;
    },
    retry: false,
    enabled: Boolean(token && tenantId && enabled)
  });
}
