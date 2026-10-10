import { describe, expect, it } from "vitest";
import { billing } from "../../tests/fixtures";
import { canonicalBillingTagKey, isBillingSummary } from "../services/contracts";
import type { BillingSummary } from "../services/contracts";
import { checkOperationalMetadata, defaultOperationalSelection, operationalBillingSelection, operationalCostCsv, operationalSelectionError } from "./operationalCostDashboard";

describe("operational cost contract and export", () => {
  it.each([[" ENV ", "environment"], ["Cost Centre", "cost_center"], ["Straße", "strasse"], ["ﬃ", "ffi"], ["constructor", "constructor"], ["组织", ""]])("canonicalizes %s as %s", (input, expected) => {
    expect(canonicalBillingTagKey(input)).toBe(expected);
  });
  it("accepts unfiltered v2 metadata but rejects malformed optional filter metadata", () => {
    expect(isBillingSummary(billing)).toBe(true);
    expect(isBillingSummary({ ...billing, filters: { project: " A " } })).toBe(true);
    for (const filters of [null, {}, [], { unknown: "A" }, { project: 4 }, { project: " " }, { project: "a\nb" }, { filter_tag_key: "env", filter_tag_value: "a" }, { filter_tag_value: "a" }]) {
      expect(isBillingSummary({ ...billing, filters })).toBe(false);
    }
  });
  it("checks every selected filter and rejects unexpected filters", () => {
    const selection = { start_date: "2024-06-01", end_date: "2024-07-01", group_by: "service" as const,
      subscription_id: "s", service_name: "Compute", project: " A ", filter_tag_key: "env", filter_tag_value: "production" };
    const filters = { subscription_id: "s", service_name: "Compute", project: " A ", filter_tag_key: "environment", filter_tag_value: "production" };
    const data = { ...billing, filters } as BillingSummary;
    expect(() => checkOperationalMetadata(data, selection)).not.toThrow();
    for (const key of Object.keys(filters) as (keyof typeof filters)[]) {
      expect(() => checkOperationalMetadata({ ...data, filters: { ...filters, [key]: "WRONG" } }, selection)).toThrow(/incompatible/);
    }
    expect(() => checkOperationalMetadata(data, { start_date: selection.start_date, end_date: selection.end_date, group_by: "service" })).toThrow(/incompatible/);
  });
  it("requires a real calendar range and a valid tag pair while preserving literal values", () => {
    const draft = { ...defaultOperationalSelection(), start_date: "2024-02-29", end_date: "2024-03-01", project: " A ", filter_tag_key: "ENV", filter_tag_value: " value " };
    expect(operationalSelectionError(draft)).toBeNull();
    expect(operationalBillingSelection(draft)).toMatchObject({ project: " A ", filter_tag_key: "environment", filter_tag_value: " value " });
    expect(operationalSelectionError({ ...draft, start_date: "2023-02-29" })).not.toBeNull();
    expect(operationalSelectionError({ ...draft, service_name: "x\u007fy" })).not.toBeNull();
    expect(operationalSelectionError({ ...draft, filter_tag_key: "!!!" })).not.toBeNull();
    expect(operationalSelectionError({ ...draft, group_by: "tag", tag_key: "" })).not.toBeNull();
  });
  it("exports only the confirmed scope, exact totals and groups, with CSV and formula escaping", () => {
    const data = { ...billing, filters: { project: " A " }, totals: [
      { currency: "USD", cost: "9007199254740993.01", record_count: 1 }, { currency: "EUR", cost: "-1.01", record_count: 1 }, { currency: "GBP", cost: "0.00", record_count: 0 }
    ], groups: [{ currency: "USD", cost: "9007199254740993.01", record_count: 1, subscription_id: null, value: '=SUM(1,2)"\nnext' }] } as BillingSummary;
    const csv = operationalCostCsv(data, "tenant-1");
    expect(csv).toContain('"9007199254740993.01"'); expect(csv).toContain('"-1.01"'); expect(csv).toContain('"0.00","0"');
    expect(csv).toContain('"\'=SUM(1,2)""\nnext"'); expect(csv).toContain('" A "');
    expect(csv).toContain('"tenant-1","2024-06-01","2024-07-01"');
    expect(csv).toContain('"total"'); expect(csv).toContain('"grupo"');
  });
});
