// /overview-legacy retains its combined billing/health hook and session context.
// Billing v2 amounts remain exact strings, including multiple currencies.
import { useOutletContext } from "react-router";
import { MetricCard } from "../components/MetricCard";
import { SectionCard } from "../components/SectionCard";
import { StatusPill } from "../components/StatusPill";
import { useDashboardData } from "../hooks/useDashboardData";
import type { SessionOutletContext } from "../layouts/SessionGate";

export function DashboardPage() {
  const { token, user, tenants, activeTenant } = useOutletContext<SessionOutletContext>();

  const { loading, error, payload } = useDashboardData({
    token,
    tenantId: activeTenant?.id
  });

  if (!activeTenant) {
    return (
      <div className="page-content">
        <SectionCard
          headingLevel={1}
          title="Select a tenant"
          subtitle="The dashboard needs an active tenant to load billing and assistant context."
        >
          <p className="text-sm text-muted-foreground">No tenant is active for this session.</p>
        </SectionCard>
      </div>
    );
  }

  // Reconciliacion con develop (JUP-087): no basta con `loading` para saber
  // que `payload` ya esta poblado. Con dos queries combinadas
  // (`useDashboardData`), `enabled: false` transitorio (p.ej. token vacio un
  // instante) puede dejar `isLoading` en `false` sin que `payload` llegue a
  // construirse -- una asercion no-nula (`payload!`) explotaria en ese caso.
  // Se sigue esperando mientras no haya ni error ni payload.
  if (loading || (!error && !payload)) {
    return (
      <div className="page-content flex min-h-[50vh] flex-col items-center justify-center gap-2 text-foreground">
        <p className="text-sm uppercase tracking-wide text-muted-foreground">Bootstrapping</p>
        <h1 className="page-title text-center">Connecting to the FinOps control plane...</h1>
      </div>
    );
  }

  if (error) {
    const overlap = error.includes("ambiguous_cost_source");
    return (
      <div className="page-content">
        <SectionCard
          headingLevel={1}
          title={overlap ? "Possible overlapping ingestion sources" : "Backend unavailable"}
          subtitle="The dashboard could not retrieve its initial context."
        >
          <p role="alert" className="text-sm text-muted-foreground">{overlap
            ? "Costs are unavailable because ingestion sources may overlap for this period."
            : error}</p>
        </SectionCard>
      </div>
    );
  }

  if (!payload) {
    return null;
  }

  const { billing, health } = payload;

  return (
    <div className="page-content flex flex-col gap-6">
      <section className="flex flex-col justify-between gap-4 rounded-lg border border-border bg-card p-6 shadow-sm sm:flex-row sm:items-center">
        <div>
          <p className="text-sm uppercase tracking-wide text-muted-foreground">Active operator</p>
          <h1 className="page-title mt-1">{user?.full_name}</h1>
          <p className="mt-2 max-w-2xl text-sm text-muted-foreground">
            Tenant-aware FinOps workspace for billing visibility, document ingestion,
            retrieval-backed chat and async processing with RabbitMQ.
          </p>
        </div>
        <div className="flex flex-col items-start gap-1 sm:items-end">
          <p className="text-sm text-muted-foreground">Tenant</p>
          <StatusPill status={activeTenant.slug} />
        </div>
      </section>

      <section className="space-y-2 text-sm text-muted-foreground" aria-label="Billing period">
        <p>{billing.period.start_date} to {billing.period.end_date} (exclusive), UTC</p>
        {billing.data_status === "empty" && <p>No cost data for this period.</p>}
        {billing.data_status === "partial" && <p role="status">Partial data: {billing.missing_dimension_count} missing dimensions; {billing.excluded_undated_count} undated records excluded.</p>}
      </section>
      <section className="grid grid-cols-1 gap-4 sm:grid-cols-3 [&_article]:min-w-0 [&_article]:[overflow-wrap:anywhere]">
        <MetricCard
          label="Monthly Spend"
          value={billing.totals.length
            ? billing.totals.map((total) => `${total.cost} ${total.currency}`).join("; ")
            : "No cost data"}
          detail="Current summary for the active tenant"
          tone="warm"
        />
        <MetricCard
          label="Savings Identified"
          value="Unavailable"
          detail="Savings have not been calculated"
          tone="success"
        />
        <MetricCard
          label="Visible Tenants"
          value={tenants.length}
          detail="Tenants available to the current operator"
        />
      </section>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <SectionCard
          title="Tenants"
          subtitle="Only tenants bound to the authenticated operator are visible here."
        >
          <div className="flex flex-col gap-3">
            {tenants.map((tenant) => (
              <article
                key={tenant.id}
                className="flex items-center justify-between rounded-md border border-border bg-background px-3 py-2"
              >
                <div>
                  <strong className="text-foreground">{tenant.name}</strong>
                  <p className="text-sm text-muted-foreground">{tenant.slug}</p>
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
          <div className="flex flex-col gap-2">
            {Object.entries(health.services).map(([service, serviceStatus]) => (
              <div
                key={service}
                className="flex items-center justify-between rounded-md border border-border bg-background px-3 py-2"
              >
                <span className="text-sm text-foreground">{service}</span>
                <StatusPill status={serviceStatus} />
              </div>
            ))}
          </div>
        </SectionCard>
      </div>
    </div>
  );
}
