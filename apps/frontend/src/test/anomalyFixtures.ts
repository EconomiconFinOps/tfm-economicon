import type { AnomalyEpisode } from "../services/contracts";

export function episode(overrides: Partial<AnomalyEpisode> = {}): AnomalyEpisode {
  return {
    id: "anomaly-1", kind: "cost_anomaly_candidate", currency: "EUR", service: "Compute",
    start_date: "2026-09-09", last_seen_date: "2026-09-20", observation: "observed", no_longer_observed_on: null,
    reference_daily_cost: "142.86", opening_observed_cost: "377.00", accumulated_impact: "2807.71",
    impact_day_count: 12, impact_through_date: "2026-09-20", severity: "P1", status: "new",
    status_changed_by: null, status_changed_at: null, first_reviewed_at: null, first_reviewed_by: null,
    closed_at: null, closure_reason: null, previous_episode_id: null, rules_version: "jup019-daily-v1",
    rules: { absolute_increase: "100.00" }, cause_status: "not_established", limitations: ["Candidata"],
    created_at: "2026-10-12T10:00:00Z", updated_at: "2026-10-12T10:00:00Z",
    ...overrides,
  };
}

export function episodeList(overrides: Record<string, unknown> = {}) {
  return {
    contract_version: 1, scope: "all", episodes: [episode()], last_evaluated_date: "2026-09-20",
    includes_synthetic_data: true, open_impact_by_currency: [{ currency: "EUR", amount: "2807.71" }],
    ...overrides,
  };
}
