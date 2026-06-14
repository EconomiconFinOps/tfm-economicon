import { MetricCard } from "../components/MetricCard";
import { SectionCard } from "../components/SectionCard";
import { StatusPill } from "../components/StatusPill";
import { useDashboardData } from "../hooks/useDashboardData";

export function DashboardPage() {
  const { loading, error, payload } = useDashboardData();

  if (loading) {
    return (
      <div className="stack-gap">
        <p className="eyebrow">Bootstrapping</p>
        <h2>Connecting to the FinOps control plane...</h2>
      </div>
    );
  }

  if (error) {
    return (
      <SectionCard
        title="Backend unavailable"
        subtitle="The dashboard could not retrieve its initial context."
      >
        <p>{error}</p>
      </SectionCard>
    );
  }

  const { profile, tenants, billing, health } = payload;

  return (
    <div className="dashboard">
      <section className="hero-panel">
        <div>
          <p className="eyebrow">Active operator</p>
          <h2>{profile.user.full_name}</h2>
          <p className="hero-copy">
            Tenant-aware FinOps workspace for billing visibility, ingestion control
            and AI-assisted operational analysis.
          </p>
        </div>
        <div className="hero-status">
          <p>API status</p>
          <StatusPill status={health.status} />
        </div>
      </section>

      <section className="metric-grid">
        <MetricCard
          label="Monthly Spend"
          value={`$${billing.monthly_spend.toLocaleString()}`}
          detail="Aggregated from current billing summary"
          tone="warm"
        />
        <MetricCard
          label="Savings Identified"
          value={`$${billing.savings_identified.toLocaleString()}`}
          detail="Potential cost actions tracked by the assistant"
          tone="success"
        />
        <MetricCard
          label="Tracked Tenants"
          value={tenants.items.length}
          detail="Tenants currently visible from the backend API"
        />
      </section>

      <div className="content-grid">
        <SectionCard
          title="Tenants"
          subtitle="Current tenant catalogue loaded from FastAPI."
        >
          <div className="tenant-list">
            {tenants.items.map((tenant) => (
              <article key={tenant.id} className="tenant-row">
                <div>
                  <strong>{tenant.name}</strong>
                  <p>{tenant.slug}</p>
                </div>
                <StatusPill status={tenant.plan} />
              </article>
            ))}
          </div>
        </SectionCard>

        <SectionCard
          title="Service Health"
          subtitle="Shallow runtime checks from the backend health endpoint."
        >
          <div className="health-stack">
            {Object.entries(health.services).map(([service, status]) => (
              <div key={service} className="health-row">
                <span>{service}</span>
                <StatusPill status={status} />
              </div>
            ))}
          </div>
        </SectionCard>
      </div>
    </div>
  );
}

