import { MetricCard } from "../components/MetricCard";
import { SectionCard } from "../components/SectionCard";
import { StatusPill } from "../components/StatusPill";
import { useDashboardData } from "../hooks/useDashboardData";

export function DashboardPage({ token, user, tenants, activeTenant }) {
  const { loading, error, payload } = useDashboardData({
    token,
    tenantId: activeTenant?.id
  });

  if (!activeTenant) {
    return (
      <SectionCard
        title="Select a tenant"
        subtitle="The dashboard needs an active tenant to load billing and assistant context."
      >
        <p>No tenant is active for this session.</p>
      </SectionCard>
    );
  }

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

  const { billing, health } = payload;

  return (
    <div className="dashboard">
      <section className="hero-panel">
        <div>
          <p className="eyebrow">Active operator</p>
          <h2>{user.full_name}</h2>
          <p className="hero-copy">
            Tenant-aware FinOps workspace for billing visibility, document ingestion,
            retrieval-backed chat and async processing with RabbitMQ.
          </p>
        </div>
        <div className="hero-status">
          <p>Tenant</p>
          <StatusPill status={activeTenant.slug} />
        </div>
      </section>

      <section className="metric-grid">
        <MetricCard
          label="Monthly Spend"
          value={`$${billing.monthly_spend.toLocaleString()}`}
          detail="Current summary for the active tenant"
          tone="warm"
        />
        <MetricCard
          label="Savings Identified"
          value={`$${billing.savings_identified.toLocaleString()}`}
          detail="Opportunities surfaced by the assistant flow"
          tone="success"
        />
        <MetricCard
          label="Visible Tenants"
          value={tenants.length}
          detail="Tenants available to the current operator"
        />
      </section>

      <div className="content-grid">
        <SectionCard
          title="Tenants"
          subtitle="Only tenants bound to the authenticated operator are visible here."
        >
          <div className="tenant-list">
            {tenants.map((tenant) => (
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
            {Object.entries(health.services).map(([service, serviceStatus]) => (
              <div key={service} className="health-row">
                <span>{service}</span>
                <StatusPill status={serviceStatus} />
              </div>
            ))}
          </div>
        </SectionCard>
      </div>
    </div>
  );
}
