import { useQueries } from "@tanstack/react-query";
import { fetchBillingSummary, fetchHealth } from "../services/api";

interface DashboardDataOptions {
  token: string;
  tenantId?: string;
}

export function useDashboardData({ token, tenantId }: DashboardDataOptions) {
  const [billingQuery, healthQuery] = useQueries({
    queries: [
      {
        queryKey: ["billing-summary", tenantId],
        queryFn: () => {
          if (!tenantId) {
            throw new Error("Tenant required");
          }
          return fetchBillingSummary(token, tenantId);
        },
        enabled: Boolean(token && tenantId)
      },
      {
        queryKey: ["health"],
        queryFn: fetchHealth
      }
    ]
  });

  return {
    loading: billingQuery.isLoading || healthQuery.isLoading,
    error: billingQuery.error?.message || healthQuery.error?.message || null,
    payload: billingQuery.data && healthQuery.data
      ? {
          billing: billingQuery.data,
          health: healthQuery.data
        }
      : null
  };
}
