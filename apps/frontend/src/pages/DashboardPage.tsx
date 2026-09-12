// DashboardPage: en la nueva arquitectura de rutas (JUP-095, grupo 6,
// sub-ronda d -- ver Addendum de design.md) deja de recibir
// `token`/`user`/`tenants`/`activeTenant` como props desde `App.jsx` y pasa
// a leerlos via `useOutletContext<SessionOutletContext>()`, mismo patron que
// `IngestPage`/`ConversationsPage`. Vive en la ruta puente
// `/overview-legacy` (decision 6 de design.md): la logica de datos
// (`useDashboardData`, las tres ramas sin-tenant/loading/error, el render
// final sobre billing/health/tenants) se preserva verbatim del origen
// (`DashboardPage.jsx`); solo cambian el origen del contexto de sesion y la
// presentacion (Tailwind + MetricCard/SectionCard/StatusPill reconstruidos).
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
      <SectionCard
        title="Select a tenant"
        subtitle="The dashboard needs an active tenant to load billing and assistant context."
      >
        <p className="text-sm text-slate-400">No tenant is active for this session.</p>
      </SectionCard>
    );
  }

  if (loading) {
    return (
      <div className="flex min-h-[50vh] flex-col items-center justify-center gap-2 text-white">
        <p className="text-sm uppercase tracking-wide text-slate-400">Bootstrapping</p>
        <h2 className="text-xl font-bold">Connecting to the FinOps control plane...</h2>
      </div>
    );
  }

  if (error) {
    return (
      <SectionCard
        title="Backend unavailable"
        subtitle="The dashboard could not retrieve its initial context."
      >
        <p className="text-sm text-slate-400">{error}</p>
      </SectionCard>
    );
  }

  // `payload` solo puede ser null mientras `loading` es true (misma
  // invariante que `useDashboardData` ya garantizaba en el origen): llegado
  // aqui, loading es false y error es null, asi que payload esta poblado.
  // Non-null assertion en vez de un cuarto branch redundante que el origen
  // tampoco tenia.
  const { billing, health } = payload!;

  return (
    <div className="flex flex-col gap-6">
      <section className="flex flex-col justify-between gap-4 rounded-lg border border-[#2d3748] bg-gradient-to-br from-[#1a1f2e] to-[#232834] p-6 shadow-xl sm:flex-row sm:items-center">
        <div>
          <p className="text-sm uppercase tracking-wide text-slate-400">Active operator</p>
          <h2 className="mt-1 text-xl font-bold text-white">{user?.full_name}</h2>
          <p className="mt-2 max-w-2xl text-sm text-slate-400">
            Tenant-aware FinOps workspace for billing visibility, document ingestion,
            retrieval-backed chat and async processing with RabbitMQ.
          </p>
        </div>
        <div className="flex flex-col items-start gap-1 sm:items-end">
          <p className="text-sm text-slate-400">Tenant</p>
          <StatusPill status={activeTenant.slug as string} />
        </div>
      </section>

      <section className="grid grid-cols-1 gap-4 sm:grid-cols-3">
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

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <SectionCard
          title="Tenants"
          subtitle="Only tenants bound to the authenticated operator are visible here."
        >
          <div className="flex flex-col gap-3">
            {tenants.map((tenant) => (
              <article
                key={tenant.id}
                className="flex items-center justify-between rounded-md border border-[#2d3748] bg-[#0f1419] px-3 py-2"
              >
                <div>
                  <strong className="text-white">{tenant.name as string}</strong>
                  <p className="text-sm text-slate-400">{tenant.slug as string}</p>
                </div>
                <StatusPill status={tenant.plan as string} />
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
                className="flex items-center justify-between rounded-md border border-[#2d3748] bg-[#0f1419] px-3 py-2"
              >
                <span className="text-sm text-white">{service}</span>
                <StatusPill status={serviceStatus as string} />
              </div>
            ))}
          </div>
        </SectionCard>
      </div>
    </div>
  );
}
