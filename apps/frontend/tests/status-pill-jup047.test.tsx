import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { StatusPill } from "../src/components/StatusPill";

describe("JUP-047 health state tones preserve existing consumers", () => {
  it("preserves the existing default green presentation and normalization", () => {
    render(<StatusPill status="ACTIVE" />);
    expect(screen.getByText("active").className).toContain("text-success-foreground");
  });

  it.each(["failed", "degraded", "unknown"])("an explicit %s health tone is not painted healthy", (tone) => {
    render(<StatusPill {...{ status: tone, tone }} />);
    const badge = screen.getByText(tone);
    expect(badge.className).not.toContain("text-success-foreground");
    expect(badge.className).not.toContain("bg-success-tint");
  });
});
