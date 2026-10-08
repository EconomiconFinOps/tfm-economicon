import { Activity, CheckCircle2, RefreshCw } from "lucide-react";
import { useLocation, useOutletContext } from "react-router";
import { MetricCard } from "../components/MetricCard";
import { SectionCard } from "../components/SectionCard";
import { StatusPill } from "../components/StatusPill";
import { useSystemHealth } from "../hooks/useSystemHealth";
import type { SessionOutletContext } from "../layouts/SessionGate";
import { isHealthObservationTime } from "../services/contracts";
import type { HealthActivitySummary, HealthComponent, HealthComponentId, HealthReason, HealthState } from "../services/contracts";

const NAMES: Record<HealthComponentId, string> = {
  backend: "API del sistema", database: "Base de datos", rabbitmq: "Cola de trabajos",
  processor: "API de procesamiento", vector_store: "Almacén de búsqueda", azure_cost_api: "Servicio de costes Azure",
  litellm: "Gateway de modelos", openrouter: "OpenRouter"
};
const LABELS: Record<HealthState, string> = { ok: "Correcto", degraded: "Degradado", failed: "Fallido", unknown: "No verificado" };
const REASONS: Record<HealthReason, string> = {
  none: "", connection: "No se pudo conectar", upstream_error: "Error al comprobar el servicio",
  authentication: "Acceso al servicio rechazado", timeout: "Se agotó el tiempo de comprobación",
  invalid_response: "Respuesta no verificable", not_configured: "Pendiente de configuración",
  not_initialized: "Preparación del servicio incompleta", not_verified: "Todavía sin comprobar",
  busy: "Comprobación ocupada", cooldown: "Espere antes de volver a comprobar",
  budget_unavailable: "Presupuesto de comprobación sin autorizar", stale: "Verificación desactualizada"
};
const JOB_LABELS: Record<string, string> = { publish_pending: "Pendientes de publicar", publish_failed: "Publicación fallida", publish_unknown: "Publicación indeterminada", queued: "En cola", running: "En ejecución", completed: "Completados", failed: "Fallidos", other: "Otros estados" };

function date(value: string | null | undefined, now: number) {
  if (!isHealthObservationTime(value, now)) return "Fecha no disponible";
  return `${new Date(value).toLocaleString()} (${value})`;
}

function ActivitySummary({ title, item, now, ingestion = false }: { title: string; item: HealthActivitySummary; now: number; ingestion?: boolean }) {
  return (
    <SectionCard title={title}>
      {item.data_status === "unavailable" ? <p>No disponible</p> : (
        <>
          {item.data_status === "empty" ? <p className="text-sm text-muted-foreground">Sin actividad registrada</p> : null}
          <dl className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            {Object.entries(item.counts ?? {}).map(([key, count]) => (
              <div key={key} className="flex min-w-0 items-start justify-between gap-3 text-sm">
                <dt className="text-muted-foreground break-words">{JOB_LABELS[key]}</dt>
                <dd className="font-medium text-foreground">{count}</dd>
              </div>
            ))}
          </dl>
          <p className="mt-4 text-sm text-muted-foreground">Fallos en las últimas 24 horas: {item.failed_last_24h}</p>
        </>
      )}
      {item.data_status !== "unavailable" ? <p className="mt-3 text-xs text-muted-foreground break-words">
        {ingestion ? "Última ingesta completada: " : "Última actualización de trabajos: "}
        {ingestion && !item.last_completed_at ? "Sin ingestas completadas" : date(ingestion ? item.last_completed_at : item.last_updated_at, now)}
      </p> : null}
      {!ingestion && (item.counts?.publish_unknown ?? 0) > 0 ? <p className="mt-2 text-sm text-warning-text">Hay publicaciones indeterminadas que requieren atención.</p> : null}
    </SectionCard>
  );
}

export function SystemHealthDashboard() {
  const { token, activeTenant } = useOutletContext<SessionOutletContext>();
  const location = useLocation();
  const health = useSystemHealth(token, activeTenant?.id, location.key);
  const future = Boolean(health.data && !isHealthObservationTime(health.data.checked_at, health.now));
  const state: HealthState = health.diagnosticError || future || !health.data ? "unknown" : health.data.status;
  const providerReason = health.stale ? "stale" : health.providerReason ?? health.provider?.reason_code ?? "not_verified";
  const componentRows = health.data?.components.map((item): HealthComponent => {
    if (item.id === "openrouter") return { ...(health.provider ?? item), status: health.providerStatus, reason_code: providerReason };
    if (health.diagnosticError || future || !isHealthObservationTime(item.checked_at, health.now)) return { ...item, status: "unknown", reason_code: "stale" };
    return item;
  });
  return (
    <div className="p-6 space-y-6 min-w-0 text-foreground">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="min-w-0">
          <h1 className="text-xl font-bold">Salud del sistema</h1>
          <p className="mt-1 text-sm text-muted-foreground">Disponibilidad de los servicios y actividad de {activeTenant?.name ?? "su cliente"}.</p>
        </div>
        <button type="button" onClick={health.refresh} disabled={health.checking}
          className="inline-flex items-center gap-2 rounded-lg border border-border bg-primary px-4 py-2 text-sm font-medium focus-visible:outline focus-visible:outline-2 focus-visible:outline-highlight disabled:opacity-60">
          <RefreshCw className="size-4" aria-hidden="true" />Actualizar
        </button>
      </div>
      <div aria-live="polite" className="flex flex-wrap items-center gap-3 text-sm">
        <Activity className="size-4 shrink-0" aria-hidden="true" />
        <StatusPill status={LABELS[state]} tone={state} />
        <span className="text-muted-foreground break-words">{health.data ? `Evaluado: ${date(health.data.checked_at, health.now)}` : "Esperando diagnóstico"}</span>
        {health.loading ? <span>Actualizando disponibilidad…</span> : null}
      </div>
      {health.diagnosticError || future ? <p role="alert" className="text-sm text-warning-text">No se pudo actualizar el diagnóstico. Los datos conservados tienen su fecha original.</p> : null}
      <div className="grid min-w-0 grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard label="Servicios correctos" value={health.diagnosticError || future || !health.data ? "—" : componentRows?.filter((item) => item.status === "ok").length ?? 0} detail="Cada observación tiene su propia fecha" />
        <MetricCard label="Fallos de trabajos · 24 h" value={health.data?.jobs.failed_last_24h ?? "—"} detail="Incluye fallos de publicación" tone="warm" />
        <MetricCard label="Fallos de ingesta · 24 h" value={health.data?.ingestion.failed_last_24h ?? "—"} detail="Solo actividad de este cliente" tone="warm" />
        <MetricCard label="Publicaciones indeterminadas" value={health.data?.jobs.counts?.publish_unknown ?? "—"} detail="Requieren atención; no son éxitos confirmados" />
      </div>
      <SectionCard title="Servicios" subtitle="La disponibilidad del gateway y la verificación del proveedor se comprueban por separado.">
        {!componentRows ? <p className="text-sm text-muted-foreground">Esperando datos de los servicios</p> : (
          <ul className="divide-y divide-border">
            {componentRows.map((item) => (
              <li key={item.id} className="flex min-w-0 flex-wrap items-start justify-between gap-3 py-4">
                <div className="min-w-0 flex-1 basis-48 space-y-1">
                  <p className="font-medium">{NAMES[item.id]}</p>
                  {item.source_kind === "simulated" ? <p className="text-xs text-muted-foreground">SIMULADO: no acredita disponibilidad de Azure real</p> : null}
                  {item.source_kind === "mock" ? <p className="text-xs text-muted-foreground">Datos de ejemplo</p> : null}
                  {item.id === "processor" ? <p className="text-xs text-muted-foreground">Actividad del procesador: sin señal verificable</p> : null}
                  {item.id === "openrouter" ? (
                    <>
                      {health.checking ? <p className="text-sm">Comprobando…</p> : REASONS[providerReason] ? <p className="text-sm text-muted-foreground">{REASONS[providerReason]}{health.retryAfter ? ` (${health.retryAfter} s)` : ""}</p> : null}
                      {health.verified ? <p className="text-xs text-muted-foreground break-words">Respuesta válida a: {date(health.verified, health.now)}{health.providerStatus !== "ok" ? " · Histórica" : ""}</p> : null}
                      {health.provider?.last_attempt_at ? <p className="text-xs text-muted-foreground break-words">Último intento: {date(health.provider.last_attempt_at, health.now)}</p> : null}
                      <p className="text-xs text-muted-foreground break-words">{health.provider?.reported_model ? "Modelo informado: " + health.provider.reported_model : "Modelo no informado"}</p>
                      <p className="text-xs text-muted-foreground">Identidad no confirmada</p>
                      <p className="text-xs text-muted-foreground break-words">
                        {health.provider?.cost_status === "gateway_reported" && health.provider.reported_cost_usd !== null
                          ? "Coste informado por el gateway: " + health.provider.reported_cost_usd + " USD · No confirmado"
                          : health.provider?.cost_status === "invalid" ? "Dato de coste no válido" : "Coste no disponible"}
                      </p>
                    </>
                  ) : item.reason_code !== "none" ? <p className="text-xs text-muted-foreground">{REASONS[item.reason_code]}</p> : null}
                  <p className="text-xs text-muted-foreground break-words">Observación: {date(item.checked_at, health.now)}</p>
                </div>
                {item.id === "openrouter" && item.status === "ok" ? (
                  <span className="inline-flex items-center gap-1 rounded-full border border-success-tint/30 bg-success-tint/20 px-2.5 py-0.5 text-xs font-medium text-success-foreground">
                    <CheckCircle2 className="size-3 shrink-0" aria-hidden="true" />Disponible
                  </span>
                ) : <StatusPill status={LABELS[item.status]} tone={item.status} />}
              </li>
            ))}
          </ul>
        )}
      </SectionCard>
      {health.data ? <div className="grid min-w-0 grid-cols-1 gap-6 md:grid-cols-2">
        <ActivitySummary title="Trabajos" item={health.data.jobs} now={health.now} />
        <ActivitySummary title="Ingesta de costes" item={health.data.ingestion} now={health.now} ingestion />
      </div> : null}
    </div>
  );
}
