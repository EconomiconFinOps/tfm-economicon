import { useQuery } from "@tanstack/react-query";
import { fetchBillingSummary, getSessionGeneration } from "../services/api";
import type { BillingSelection } from "../services/contracts";

interface CostKpisOptions {
  token: string;
  tenantId?: string;
  selection: BillingSelection;
  enabled?: boolean;
}

export function useCostKpis({ token, tenantId, selection, enabled = true }: CostKpisOptions) {
  return useQuery({
    queryKey: ["billing-summary", tenantId, 2, getSessionGeneration(),
      selection.start_date, selection.end_date, selection.group_by, selection.tag_key],
    queryFn: ({ signal }) => {
      if (!tenantId) throw new Error("Tenant required");
      return fetchBillingSummary(token, tenantId, selection, signal);
    },
    enabled: Boolean(token && tenantId && enabled)
  });
}
