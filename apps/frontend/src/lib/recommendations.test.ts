import { describe, expect, it } from "vitest";
import { demoImpactReport, demoRecommendationReport as report, demoRecommendationTenant } from "@/data/demo/recommendationsPanel";
import { compareDecimal, defaultRecommendationFilters, filterRecommendations, formatDecimal, recommendationRows, recommendationsCsv, savingsAmount } from "./recommendations";
import { isRecommendationReport } from "@/services/recommendations";

describe("recommendation contract and presentation", () => {
  it("validates the JUP-033 serialized double and rejects unsafe or mismatched evidence", () => {
    expect(isRecommendationReport(report)).toBe(true);
    for (const mutate of [
      (value: typeof report) => { value.recommendations[0].difficulty = "easy" as "low"; },
      (value: typeof report) => { value.recommendations[0].evidence_ids = ["unknown"]; },
      (value: typeof report) => { value.evidence[0].query.period.start_date = "2026-08-01"; },
      (value: typeof report) => { value.recommendations[0].requires_human_approval = false as true; },
      (value: typeof report) => { value.evidence[0].observed_cost.amount = "NaN"; },
      (value: typeof report) => { value.recommendations[0].observed_cost.record_count = 0; },
      (value: typeof report) => { value.recommendations[1].id = value.recommendations[0].id; },
    ]) {
      const invalid = JSON.parse(JSON.stringify(report)) as typeof report;
      mutate(invalid);
      expect(isRecommendationReport(invalid)).toBe(false);
    }
  });

  it("keeps unknown separate from zero and never uses observed cost as savings", () => {
    expect(recommendationRows(report).every(row => savingsAmount(row, "monthly") === null)).toBe(true);
    const rows = recommendationRows(report, demoImpactReport, demoRecommendationTenant);
    expect(savingsAmount(rows[0], "monthly")).toBe("0.00");
    expect(savingsAmount(rows[4], "monthly")).toBeNull();
    expect(rows[2].impact?.included_in_total).toBe(false);
    expect(rows[2].impact?.excluded_by).toEqual([rows[1].id]);
  });

  it("rejects impact from another tenant or period", () => {
    expect(() => recommendationRows(report, demoImpactReport, "other-tenant")).toThrow(/cliente y mes/);
    expect(() => recommendationRows(report, { ...demoImpactReport, baseline_month: "2026-08-01" }, demoRecommendationTenant)).toThrow(/cliente y mes/);
  });

  it("sorts high precision amounts exactly while preserving explicit monthly and annual values", () => {
    expect(compareDecimal("999999999999999999.000002", "999999999999999999.000001")).toBe(1);
    expect(compareDecimal("0", "0.000000")).toBe(0);
    expect(formatDecimal("999999999999999999.000001")).toBe("999.999.999.999.999.999,000001");
    const impact = structuredClone(demoImpactReport);
    impact.recommendations[1].potential_monthly_savings = "999999999999999999.000001";
    impact.recommendations[2].potential_monthly_savings = "999999999999999999.000002";
    impact.recommendations[1].potential_annual_savings = "1.12";
    impact.recommendations[2].potential_annual_savings = null;
    const rows = recommendationRows(report, impact, demoRecommendationTenant);
    expect(filterRecommendations(rows, defaultRecommendationFilters).slice(0, 2).map(row => row.id)).toEqual([rows[2].id, rows[1].id]);
    expect(savingsAmount(rows[1], "annual")).toBe("1.12");
    expect(savingsAmount(rows[2], "annual")).toBeNull();
  });

  it("quotes CSV text, neutralizes formulas and carries uncertainty with exact decimal strings", () => {
    const rows = recommendationRows(report, demoImpactReport, demoRecommendationTenant);
    rows[0].action = '=HYPERLINK("https://example.invalid","demo")';
    rows[0].rationale = 'Two, fields\n"quoted"';
    rows[4].action = " \t@SUM(1)";
    const csv = recommendationsCsv([rows[0], rows[4]], report, "monthly", "Demo", demoImpactReport);
    expect(csv).toContain('"\'=HYPERLINK(""https://example.invalid"",""demo"")"');
    expect(csv).toContain('"Two, fields\n""quoted"""');
    expect(csv).toContain('"\' \t@SUM(1)"');
    expect(csv).toContain('"No estimado"');
    expect(csv).toContain('"0.00","EUR","Mensual"');
    expect(csv).toContain('"caller_supplied_scenario","2026-09-01"');
    expect(csv).not.toContain('"900.00"');
  });
});
