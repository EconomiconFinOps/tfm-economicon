import { useQuery } from "@tanstack/react-query";
import { fetchBillingSummary, getSessionGeneration } from "../services/api";
import type { BillingSelection, BillingSummary } from "../services/contracts";
import { monthlyPeriod } from "../lib/executiveCostDashboard";
import type { ExecutiveSnapshot, SummaryOutcome } from "../lib/executiveCostDashboard";

interface ExecutiveCostKpisOptions {
  token: string;
  tenantId?: string;
  selection: BillingSelection;
  months: string[];
  enabled?: boolean;
}

function checkMetadata(data: BillingSummary, selection: BillingSelection) {
  if (data.period.start_date !== selection.start_date || data.period.end_date !== selection.end_date
    || data.period.timezone !== "UTC" || data.group_by !== selection.group_by
    || (selection.group_by !== "tag" && data.tag_key !== null)) {
    throw new Error("Respuesta de costes incompatible");
  }
}

export function useExecutiveCostKpis({ token, tenantId, selection, months, enabled = true }: ExecutiveCostKpisOptions) {
  const generation = getSessionGeneration();
  const effectiveTag = selection.group_by === "tag" ? selection.tag_key : undefined;
  const requestSelection = {
    start_date: selection.start_date, end_date: selection.end_date,
    group_by: selection.group_by, ...(effectiveTag !== undefined ? { tag_key: effectiveTag } : {})
  };
  return useQuery<ExecutiveSnapshot>({
    queryKey: ["executive-billing-summary", 2, tenantId, generation,
      selection.start_date, selection.end_date, selection.group_by, effectiveTag],
    enabled: Boolean(token && tenantId && enabled && months.length),
    retry: false,
    queryFn: async ({ signal }) => {
      if (!tenantId || !months.length || !selection.start_date || !selection.end_date) {
        throw new Error("Selección de costes incompleta");
      }
      const checkActive = () => {
        if (signal.aborted || generation !== getSessionGeneration()) {
          throw new DOMException("Consulta cancelada", "AbortError");
        }
      };
      // Adjacent control updates can commit separately within one interaction.
      // Yield before allocating any HTTP work so an already obsolete
      // intermediate selection can be cancelled rather than queried.
      await Promise.resolve();
      checkActive();
      // One month shares its aggregate request; a wider interval has N+1 jobs.
      const jobs: BillingSelection[] = [requestSelection, ...(months.length === 1 ? [] : months.map((month) => ({
        ...requestSelection, ...monthlyPeriod(month)
      })))];
      const results: SummaryOutcome[] = new Array(jobs.length);
      let next = 0;
      const worker = async () => {
        while (next < jobs.length) {
          checkActive();
          const index = next++;
          try {
            const data = await fetchBillingSummary(token, tenantId, jobs[index], signal);
            checkActive();
            checkMetadata(data, jobs[index]);
            results[index] = { kind: "success", data };
          } catch (error) {
            checkActive();
            results[index] = { kind: "error", error };
          }
        }
      };
      // Atomic queue allocation before each await: includes the aggregate,
      // starts it first, and prevents obsolete queued jobs after cancellation.
      await Promise.all(Array.from({ length: Math.min(3, jobs.length) }, worker));
      checkActive();
      const aggregate = results[0];
      return {
        aggregate,
        months: months.map((month, index) => {
          let result = results[months.length === 1 ? 0 : index + 1];
          // Let the backend canonicalize the tag. Every successful monthly
          // response must agree with this execution's aggregate, not our own
          // approximation of its Unicode normalization.
          if (aggregate.kind === "success" && result.kind === "success"
            && result.data.tag_key !== aggregate.data.tag_key) {
            result = { kind: "error", error: new Error("Respuesta de costes incompatible") };
          }
          return { month, result };
        })
      };
    }
  });
}
