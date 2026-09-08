import type { ViewId } from "../layouts/AppShell";

export function PlaceholderPage({ view }: { view: ViewId }) {
  const copy: Partial<Record<ViewId, string>> = {
    settings: "Reserved for provider credentials, role management and operational feature flags."
  };

  return (
    <section className="section-card">
      <p className="eyebrow">Coming next</p>
      <h2>{view}</h2>
      <p>{copy[view] ?? "This section will be expanded in the next iteration."}</p>
    </section>
  );
}
