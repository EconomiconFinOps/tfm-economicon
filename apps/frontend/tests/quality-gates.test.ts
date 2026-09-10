import { ESLint } from "eslint";
import { describe, expect, it } from "vitest";

describe("component prop contracts", () => {
  const eslint = new ESLint();

  // The first lint loads ESLint plugins, which can be slow on a fresh Windows worker.
  it("still rejects missing prop contracts in JavaScript components", async () => {
    const [result] = await eslint.lintText(
      "export function QualityProbe({ label }) { return <span>{label}</span>; }",
      { filePath: "src/components/QualityProbe.jsx" }
    );
    expect(result.messages.some(({ ruleId }) => ruleId === "react/prop-types")).toBe(true);
  }, 30_000);

  it("accepts explicit TypeScript props without redundant PropTypes", async () => {
    const [result] = await eslint.lintText(
      "export function QualityProbe({ label }: { label: string }) { return <span>{label}</span>; }",
      { filePath: "src/components/QualityProbe.tsx" }
    );
    expect(result.messages).toEqual([]);
  });
});
