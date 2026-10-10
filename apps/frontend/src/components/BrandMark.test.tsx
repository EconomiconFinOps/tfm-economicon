import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { BrandMark } from "./BrandMark";

describe("BrandMark", () => {
  it("shows the brand once to assistive technology and keeps the symbol decorative", () => {
    const { container } = render(<BrandMark />);
    expect(screen.getByText("Economicon")).toBeVisible();
    expect(screen.queryByRole("img")).not.toBeInTheDocument();
    const symbol = container.querySelector("img");
    expect(symbol).toHaveAttribute("alt", "");
    expect(symbol?.getAttribute("src")).toContain("economicon-primary.png");
  });

  it("provides the original inverse artwork for future brand surfaces", () => {
    const { container } = render(<BrandMark inverse />);
    expect(container.querySelector("img")?.getAttribute("src")).toContain("economicon-inverse.png");
    expect(container.firstChild).toHaveClass("brand-mark--inverse");
  });
});
