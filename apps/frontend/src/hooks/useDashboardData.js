import { useQueries } from "@tanstack/react-query";
import { fetchBillingSummary, fetchHealth } from "../services/api";

export function useDashboardData({ token, tenantId }) {
  const [billingQuery, healthQuery] = useQueries({
    queries: [
      {
        queryKey: ["billing-summary", tenantId],
        queryFn: () => fetchBillingSummary(token, tenantId),
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
