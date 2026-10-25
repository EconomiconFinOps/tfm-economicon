// /overview-legacy retains its combined billing/health hook and session context.
// Billing v2 amounts remain exact strings, including multiple currencies.
import { useOutletContext } from "react-router";
import { MetricCard } from "../components/MetricCard";
import { SectionCard } from "../components/SectionCard";
import { StatusPill } from "../components/StatusPill";
import { useDashboardData } from "../hooks/useDashboardData";
import type { SessionOutletContext } from "../layouts/SessionGate";

const SERVICE_STATUS_LABELS: Record<string, string> = {
  ok: "Correcto", degraded: "Degradado", failed: "Fallido", unknown: "No verificado"
};

export function DashboardPage() {
  const { token, user, tenants, activeTenant } = useOutletContext<SessionOutletContext>();

  const { loading, error, payload } = useDashboardData({
    token,
    tenantId: activeTenant?.id
  });

  if (!activeTenant) {
    return (
      <SectionCard
        title="Elige un cliente"
        subtitle="El panel necesita un cliente activo para cargar el contexto de facturación y del asistente."
      >
        <p className="text-sm text-muted-foreground">No hay ningún cliente activo en esta sesión.</p>
      </SectionCard>
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
      <div className="flex min-h-[50vh] flex-col items-center justify-center gap-2 text-foreground">
        <p className="text-sm uppercase tracking-wide text-muted-foreground">Arrancando</p>
        <h2 className="text-xl font-bold">Conectando con el plano de control FinOps...</h2>
      </div>
    );
  }

  if (error) {
    const overlap = error.includes("ambiguous_cost_source");
    return (
      <SectionCard
        title={overlap ? "Posible solapamiento de fuentes de ingesta" : "Backend no disponible"}
        subtitle="El panel no ha podido obtener su contexto inicial."
      >
        <p role="alert" className="text-sm text-muted-foreground">{overlap
          ? "Los costes no están disponibles porque las fuentes de ingesta pueden solaparse en este periodo."
          : error}</p>
      </SectionCard>
    );
  }

  if (!payload) {
    return null;
  }

  const { billing, health } = payload;

  return (
    <div className="flex flex-col gap-6">
      <section className="flex flex-col justify-between gap-4 rounded-lg border border-border bg-gradient-to-br from-card to-accent p-6 shadow-xl sm:flex-row sm:items-center">
        <div>
          <p className="text-sm uppercase tracking-wide text-muted-foreground">Operador activo</p>
          <h2 className="mt-1 text-xl font-bold text-foreground">{user?.full_name}</h2>
          <p className="mt-2 max-w-2xl text-sm text-muted-foreground">
            Espacio FinOps por cliente para ver la facturación, ingerir documentos,
            conversar con respaldo documental y procesar de forma asíncrona con RabbitMQ.
          </p>
        </div>
        <div className="flex flex-col items-start gap-1 sm:items-end">
          <p className="text-sm text-muted-foreground">Cliente</p>
          <StatusPill status={activeTenant.slug} />
        </div>
      </section>

      <section className="space-y-2 text-sm text-muted-foreground" aria-label="Periodo de facturación">
        <p>{billing.period.start_date} a {billing.period.end_date} (excluido), UTC</p>
        {billing.data_status === "empty" && <p>No hay datos de coste para este periodo.</p>}
        {billing.data_status === "partial" && <p role="status">Datos parciales: {billing.missing_dimension_count} dimensiones ausentes; {billing.excluded_undated_count} registros sin fecha excluidos.</p>}
      </section>
      <section className="grid grid-cols-1 gap-4 sm:grid-cols-3 [&_article]:min-w-0 [&_article]:[overflow-wrap:anywhere]">
        <MetricCard
          label="Gasto mensual"
          value={billing.totals.length
            ? billing.totals.map((total) => `${total.cost} ${total.currency}`).join("; ")
            : "Sin datos de coste"}
          detail="Resumen actual del cliente activo"
          tone="warm"
        />
        <MetricCard
          label="Ahorro identificado"
          value="No disponible"
          detail="El ahorro no se ha calculado"
          tone="success"
        />
        <MetricCard
          label="Clientes visibles"
          value={tenants.length}
          detail="Clientes disponibles para el operador actual"
        />
      </section>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <SectionCard
          title="Clientes"
          subtitle="Aquí solo se ven los clientes vinculados al operador autenticado."
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
          title="Salud de los servicios"
          subtitle="Comprobaciones básicas de ejecución del endpoint de salud del backend."
        >
          <div className="flex flex-col gap-2">
            {Object.entries(health.services).map(([service, serviceStatus]) => (
              <div
                key={service}
                className="flex items-center justify-between rounded-md border border-border bg-background px-3 py-2"
              >
                <span className="text-sm text-foreground">{service}</span>
                <StatusPill status={Object.hasOwn(SERVICE_STATUS_LABELS, serviceStatus) ? SERVICE_STATUS_LABELS[serviceStatus] : serviceStatus} />
              </div>
            ))}
          </div>
        </SectionCard>
      </div>
    </div>
  );
}
