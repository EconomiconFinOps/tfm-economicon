export function PlaceholderPage({ view }) {
  const copy = {
    costs: "Reserved for cost anomaly views, budgets and optimization levers.",
    tenants: "Reserved for tenant administration and billing boundaries.",
    settings: "Reserved for provider credentials, ingestion sources and feature flags."
  };

  return (
    <section className="section-card">
      <p className="eyebrow">Coming next</p>
      <h2>{view}</h2>
      <p>{copy[view] ?? "This section will be expanded in the next iteration."}</p>
    </section>
  );
}

