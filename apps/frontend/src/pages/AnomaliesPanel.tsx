import { useEffect, useMemo, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useOutletContext } from "react-router";
import { AlertTriangle, FlaskConical, Radar, SlidersHorizontal } from "lucide-react";
import { ExportButton } from "@/components/ExportButton";
import { Dialog, DialogContent, DialogDescription, DialogTitle } from "@/components/ui/dialog";
import type { SessionOutletContext } from "@/layouts/SessionGate";
import { changeAnomalyEpisodeStatus, detectAnomalies, fetchAnomalyEpisodes, getSessionGeneration } from "@/services/api";
import type { AnomalyDetectionRun, AnomalyEpisode, AnomalySeverity, AnomalyStatus, AnomalyStatusChange } from "@/services/contracts";
import {
  dayLabel, detectionMessage, exportRows, filterEpisodes, isOpen, money, observationText, openingExcess, runCounts,
  runHeadline, severityLabels, skipReasons, statusChangeMessage, statusLabels, trimLikeBackend, validClosingReason,
  type ObservationFilter, type SeverityFilter, type StatusFilter,
} from "@/lib/anomalyPanel";

const severityStyles: Record<AnomalySeverity, string> = {
  P1: "border-danger/30 bg-danger-tint/10 text-danger-foreground",
  P2: "border-warning/30 bg-warning-tint/10 text-warning-foreground",
  P3: "border-highlight/30 bg-highlight/10 text-info-foreground",
};
const statusStyles: Record<AnomalyStatus, string> = {
  new: "border-neutral/40 bg-neutral/10 text-subtle-foreground",
  investigating: "border-warning/30 bg-warning-tint/10 text-warning-foreground",
  resolved: "border-success/30 bg-success-tint/10 text-success-foreground",
  false_positive: "border-success/30 bg-success-tint/10 text-success-foreground",
};
const selectStyle = "mt-2 w-full rounded-md border border-neutral bg-background px-3 py-2.5 text-sm text-foreground focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-highlight";
const buttonStyle = "rounded-md border border-neutral px-4 py-2.5 text-sm text-subtle-foreground hover:border-highlight hover:text-info-foreground disabled:cursor-not-allowed disabled:opacity-60";
const primaryStyle = "rounded-md border border-highlight/50 bg-highlight/10 px-4 py-2.5 text-sm font-semibold text-info-foreground hover:bg-highlight/20 disabled:cursor-not-allowed disabled:opacity-60";

type RunOutcome = { run?: AnomalyDetectionRun; error?: string; reloadFailed?: boolean };

function Badge({ className, children }: { className: string; children: string }) {
  return <span className={`inline-flex rounded-md border px-2 py-1 text-xs font-semibold ${className}`}>{children}</span>;
}

function RunResult({ outcome }: { outcome: RunOutcome }) {
  const run = outcome.run;
  return (
    <div role="status" aria-label="Resultado de la detección" className="rounded-lg border border-highlight/30 bg-highlight/5 px-4 py-3 text-sm">
      {outcome.error ? <p className="text-foreground">{outcome.error}</p> : run && <>
        <p className="font-semibold text-foreground">{runHeadline(run)}</p>
        {run.status === "completed" && <p className="mt-1 text-subtle-foreground">{runCounts(run)}</p>}
        {run.unsupported_currencies.map((currency) => (
          <p key={currency} className="mt-1 text-warning-foreground">{currency} no se evalúa (solo EUR y USD).</p>
        ))}
        {(run.evaluated_days.length > 0 || run.skipped_days.length > 0) && <details className="mt-2">
          <summary className="cursor-pointer text-info-foreground">Detalles</summary>
          {run.evaluated_days.length > 0 && <p className="mt-1">Días evaluados: {run.evaluated_days.map(dayLabel).join(", ")}</p>}
          {run.skipped_days.length > 0 && <ul className="mt-1 list-disc pl-5">
            {run.skipped_days.map((item) => <li key={item.date}>{dayLabel(item.date)}: {skipReasons[item.reason]}</li>)}
          </ul>}
        </details>}
        {outcome.reloadFailed && <p className="mt-2 text-warning-foreground">La detección se guardó, pero no se ha podido actualizar la lista. Vuelve a cargarla para ver los episodios.</p>}
      </>}
    </div>
  );
}

function EpisodeDetail({ episode, token, tenantId, onChanged, onReload }: {
  episode: AnomalyEpisode; token: string; tenantId: string; onChanged: () => void; onReload: () => void;
}) {
  const [closing, setClosing] = useState(false);
  const [target, setTarget] = useState<"resolved" | "false_positive">("resolved");
  const [reason, setReason] = useState("");
  const mutation = useMutation({
    mutationFn: (change: AnomalyStatusChange) => changeAnomalyEpisodeStatus(token, tenantId, episode.id, change),
    onSuccess: () => { setClosing(false); setReason(""); onChanged(); },
  });
  const service = episode.service ?? "(sin servicio)";
  const facts: [string, string][] = [
    ["Referencia", `${money(episode.reference_daily_cost, episode.currency)}/día`],
    ["Apertura", `${dayLabel(episode.start_date)} con ${money(episode.opening_observed_cost, episode.currency)}`],
    ["Impacto acumulado", `${money(episode.accumulated_impact, episode.currency)} en ${episode.impact_day_count} días (hasta ${dayLabel(episode.impact_through_date)})`],
    ["Periodo", `${dayLabel(episode.start_date)} → ${dayLabel(episode.last_seen_date)}`],
    ["Reglas", episode.rules_version],
  ];
  if (episode.previous_episode_id) facts.push(["Anomalía anterior del mismo servicio", episode.previous_episode_id]);
  if (episode.first_reviewed_at) facts.push(["Primera revisión", `${episode.first_reviewed_by ?? ""} · ${episode.first_reviewed_at}`]);
  if (episode.status_changed_at) facts.push(["Último cambio de estado", `${episode.status_changed_by ?? ""} · ${episode.status_changed_at}`]);
  if (episode.closed_at) facts.push(["Cierre", `${episode.closed_at} · ${episode.closure_reason ?? ""}`]);
  return (
    <>
      <DialogTitle className="pr-8 text-lg font-semibold text-foreground">{service} · {episode.currency}</DialogTitle>
      <DialogDescription asChild>
        <div className="flex flex-wrap gap-2">
          <Badge className={severityStyles[episode.severity]}>{severityLabels[episode.severity]}</Badge>
          <Badge className={statusStyles[episode.status]}>{statusLabels[episode.status]}</Badge>
          <span className="text-sm text-subtle-foreground">{observationText(episode)}</span>
        </div>
      </DialogDescription>
      <dl className="grid gap-2 text-sm">
        {facts.map(([label, value]) => <div key={label}><dt className="text-subtle-foreground">{label}</dt><dd className="text-foreground">{value}</dd></div>)}
      </dl>
      <p className="text-sm font-semibold text-info-foreground">Candidata: causa no establecida</p>
      <details className="text-sm text-subtle-foreground"><summary className="cursor-pointer">Limitaciones</summary>
        <ul className="mt-1 list-disc pl-5">{episode.limitations.map((item) => <li key={item}>{item}</li>)}</ul>
      </details>
      {mutation.isError && <div role="alert" className="rounded-md border border-danger/30 bg-danger-tint/10 p-3 text-sm text-danger-foreground">
        <p>{statusChangeMessage(mutation.error)}</p>
        <button className={`${buttonStyle} mt-2`} onClick={() => { mutation.reset(); onReload(); }}>Recargar la anomalía</button>
      </div>}
      {isOpen(episode) && !closing && <div className="flex flex-wrap gap-3">
        {episode.status === "new" && <button className={primaryStyle} disabled={mutation.isPending}
          onClick={() => mutation.mutate({ status: "investigating" })}>Marcar en investigación</button>}
        <button className={buttonStyle} disabled={mutation.isPending} onClick={() => setClosing(true)}>Cerrar…</button>
      </div>}
      {isOpen(episode) && closing && <fieldset className="grid gap-3 rounded-md border border-border p-3 text-sm">
        <legend className="px-1 font-semibold text-foreground">Cerrar la anomalía</legend>
        <p className="text-warning-foreground">Cerrar una anomalía no se puede deshacer. Si el gasto vuelve a subir, se abrirá una nueva.</p>
        <label className="flex items-center gap-2"><input type="radio" name="closing-status" checked={target === "resolved"}
          onChange={() => setTarget("resolved")} />Resuelta</label>
        <label className="flex items-center gap-2"><input type="radio" name="closing-status" checked={target === "false_positive"}
          onChange={() => setTarget("false_positive")} />Falso positivo</label>
        <label htmlFor="closing-reason" className="text-subtle-foreground">Motivo</label>
        <textarea id="closing-reason" maxLength={500} value={reason} onChange={(event) => setReason(event.target.value)}
          className="min-h-20 rounded-md border border-neutral bg-background p-2 text-foreground" />
        <div className="flex flex-wrap gap-3">
          <button className={primaryStyle} disabled={!validClosingReason(reason) || mutation.isPending}
            onClick={() => mutation.mutate({ status: target, reason: trimLikeBackend(reason) })}>Confirmar cierre</button>
          <button className={buttonStyle} onClick={() => { setClosing(false); setReason(""); }}>Cancelar</button>
        </div>
      </fieldset>}
    </>
  );
}

export function AnomaliesPanel() {
  const { token, activeTenant } = useOutletContext<SessionOutletContext>();
  const tenantId = activeTenant?.id ?? "";
  const queryClient = useQueryClient();
  const generation = getSessionGeneration();
  const queryKey = useMemo(() => ["anomaly-episodes", 1, tenantId, generation], [tenantId, generation]);
  const [severity, setSeverity] = useState<SeverityFilter>("all");
  const [status, setStatus] = useState<StatusFilter>("open");
  const [observation, setObservation] = useState<ObservationFilter>("all");
  const [outcome, setOutcome] = useState<RunOutcome | null>(null);
  const [newIds, setNewIds] = useState<Set<string>>(new Set());
  const [selectedId, setSelectedId] = useState<string | null>(null);
  // Episodios conocidos al pulsar «Detectar ahora», por cliente: un cambio de cliente no los borra y una ida y vuelta no marca todo como nuevo.
  const knownIds = useRef(new Map<string, Set<string>>());
  const tenantInView = useRef(tenantId);
  tenantInView.current = tenantId;

  const list = useQuery({
    queryKey,
    queryFn: ({ signal }) => fetchAnomalyEpisodes(token, tenantId, signal),
    enabled: Boolean(token && tenantId),
    retry: false,
  });

  useEffect(() => {
    setOutcome(null); setNewIds(new Set()); setSelectedId(null);
    setSeverity("all"); setStatus("open"); setObservation("all");
  }, [tenantId]);

  const detect = useMutation({
    mutationFn: (forTenant: string) => detectAnomalies(token, forTenant),
    onMutate: (forTenant) => { knownIds.current.set(forTenant, new Set((tenantInView.current === forTenant ? list.data?.episodes ?? [] : []).map((item) => item.id))); },
    // El resultado solo se enseña en el cliente que lo pidió: si se cambió de cliente mientras corría, se descarta.
    onSuccess: async (run, forTenant) => {
      if (tenantInView.current !== forTenant) return;
      setOutcome({ run });
      try {
        const refreshed = await queryClient.fetchQuery({ queryKey, queryFn: ({ signal }) => fetchAnomalyEpisodes(token, forTenant, signal) });
        if (tenantInView.current !== forTenant) return;
        setNewIds(new Set(refreshed.episodes.map((item) => item.id).filter((id) => !knownIds.current.get(forTenant)?.has(id))));
      } catch {
        // La detección ya está guardada: un fallo al recargar la lista no la convierte en un fallo de la detección.
        if (tenantInView.current === forTenant) setOutcome({ run, reloadFailed: true });
      }
    },
    onError: (error, forTenant) => { if (tenantInView.current === forTenant) setOutcome({ error: detectionMessage(error) }); },
  });

  // Una recarga fallida conserva en React Query los datos anteriores: no se enseñan junto al error.
  const data = list.isError ? undefined : list.data;
  const episodes = data?.episodes ?? [];
  const visible = filterEpisodes(episodes, severity, status, observation);
  const open = episodes.filter(isOpen);
  const selected = episodes.find((item) => item.id === selectedId) ?? null;
  const reset = () => { setSeverity("all"); setStatus("open"); setObservation("all"); };
  const reload = () => queryClient.invalidateQueries({ queryKey });
  const neverDetected = data !== undefined && data.last_evaluated_date === null;

  const detecting = detect.isPending && detect.variables === tenantId;
  const detectButton = (
    <button className={primaryStyle} disabled={detecting || !tenantId} onClick={() => detect.mutate(tenantId)}>
      {detecting ? "Detectando…" : "Detectar ahora"}
    </button>
  );

  return (
    <div className="min-w-0 space-y-6 p-4 text-subtle-foreground sm:p-6 [&_button:focus-visible]:outline-2 [&_button:focus-visible]:outline-offset-2 [&_button:focus-visible]:outline-highlight">
      <header className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
        <div>
          <p className="mb-1 text-xs font-semibold uppercase tracking-widest text-info-foreground">Supervisión de costes</p>
          <h2 className="text-2xl font-bold text-foreground">Panel de Anomalías y Alertas</h2>
          <p className="mt-1 text-sm text-subtle-foreground">Anomalías candidatas detectadas con la regla diaria de negocio, priorizadas por criticidad e impacto acumulado.</p>
        </div>
        <div className="flex flex-wrap items-center gap-3 self-start">
          {!neverDetected && detectButton}
          {data?.last_evaluated_date && <p className="text-sm text-subtle-foreground">Revisado hasta el {dayLabel(data.last_evaluated_date)}</p>}
          {visible.length > 0 && data ? <ExportButton data={exportRows(visible, {
            tenantName: activeTenant?.name ?? tenantId, synthetic: data.includes_synthetic_data, lastEvaluated: data.last_evaluated_date,
          })} filename={`anomalias-${tenantId}-revisado-${data.last_evaluated_date ?? "sin-revision"}`} /> :
            <button disabled className="rounded-md border border-neutral px-4 py-2 text-muted-foreground">Exportar Resultados</button>}
        </div>
      </header>

      {outcome && <RunResult outcome={outcome} />}

      {data?.includes_synthetic_data && <aside aria-label="Origen de los datos" className="flex items-start gap-3 rounded-lg border border-highlight/30 bg-highlight/5 px-4 py-3">
        <FlaskConical aria-hidden="true" className="mt-0.5 h-5 w-5 shrink-0 text-info-foreground" />
        <p className="text-sm font-semibold text-info-foreground">Datos sintéticos de demostración: no son facturas reales</p>
      </aside>}

      {list.isPending && Boolean(tenantId) && <div aria-busy="true" aria-label="Cargando anomalías" className="space-y-3">
        {[0, 1, 2].map((item) => <div key={item} className="h-12 animate-pulse rounded-md bg-muted" />)}
      </div>}

      {list.isError && <div role="alert" className="rounded-lg border border-danger/30 bg-danger-tint/10 px-5 py-6">
        <p className="font-semibold text-danger-foreground">No se han podido cargar las anomalías.</p>
        <button className={`${buttonStyle} mt-3`} onClick={() => list.refetch()}>Reintentar</button>
      </div>}

      {neverDetected && <section className="rounded-lg border border-border bg-card px-5 py-12 text-center">
        <Radar aria-hidden="true" className="mx-auto h-8 w-8 text-info-foreground" />
        <h3 className="mt-3 font-semibold text-foreground">Todavía no se han buscado anomalías en este cliente</h3>
        <p className="mt-2 text-sm">Pulsa «Detectar ahora» para revisar sus costes diarios con la regla de negocio.</p>
        <div className="mt-5">{detectButton}</div>
      </section>}

      {data && !neverDetected && <>
        <section aria-label="Resumen de todas las anomalías del cliente" className="overflow-hidden rounded-lg border border-border bg-card">
          <div className="border-b border-border px-5 py-3 text-xs text-subtle-foreground">Resumen de todas las anomalías del cliente · no cambia con los filtros</div>
          <dl className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-[1.4fr_1fr_1fr_1fr]">
            <div className="border-b border-border bg-highlight/5 p-5 md:border-r xl:border-b-0">
              <dt className="text-sm text-info-foreground">Impacto acumulado de las abiertas</dt>
              {data.open_impact_by_currency.length ? data.open_impact_by_currency.map((item) => (
                <dd key={item.currency} className="mt-2 text-2xl font-bold tabular-nums text-foreground">{money(item.amount, item.currency)}</dd>
              )) : <dd className="mt-2 text-2xl font-bold text-foreground">—</dd>}
              <p className="mt-2 text-xs text-subtle-foreground">Por moneda; no se suman monedas</p>
            </div>
            <div className="border-b border-border p-5 xl:border-b-0 xl:border-r">
              <dt className="text-sm text-subtle-foreground">Abiertas</dt>
              <dd data-testid="summary-open" className="mt-2 text-3xl font-semibold tabular-nums text-foreground">{open.length}</dd>
              <p className="mt-2 text-xs text-muted-foreground">Nuevas o en investigación</p>
            </div>
            <div className="border-b border-border p-5 md:border-b-0 md:border-r">
              <dt className="flex items-center gap-2 text-sm text-danger-foreground"><AlertTriangle aria-hidden="true" className="h-4 w-4" />Alta (P1) abiertas</dt>
              <dd data-testid="summary-p1" className="mt-2 text-3xl font-semibold tabular-nums text-danger-foreground">{open.filter((item) => item.severity === "P1").length}</dd>
              <p className="mt-2 text-xs text-muted-foreground">Revisar primero</p>
            </div>
            <div className="p-5">
              <dt className="text-sm text-subtle-foreground">Ya no se observan</dt>
              <dd data-testid="summary-ended" className="mt-2 text-3xl font-semibold tabular-nums text-foreground">
                {open.filter((item) => item.observation === "no_longer_observed").length}</dd>
              <button className="mt-2 text-left text-xs text-info-foreground underline"
                onClick={() => { setStatus("open"); setSeverity("all"); setObservation("no_longer_observed"); }}>
                Ya no se observan · pendientes de cerrar
              </button>
            </div>
          </dl>
        </section>

        {open.length === 0 && <p className="text-sm">No hay anomalías abiertas. Revisado hasta el {dayLabel(data.last_evaluated_date ?? "")}.</p>}

        <section aria-labelledby="alerts-title" className="min-w-0 rounded-lg border border-border bg-card">
          <div className="space-y-5 border-b border-border p-5">
            <div className="flex items-center gap-2"><SlidersHorizontal aria-hidden="true" className="h-4 w-4 text-info-foreground" /><h3 id="alerts-title" className="font-semibold text-foreground">Bandeja de anomalías</h3></div>
            <div className="grid grid-cols-1 items-end gap-4 md:grid-cols-[1fr_1fr_1fr_auto]">
              <div><label className="text-sm text-subtle-foreground" htmlFor="anomaly-severity">Criticidad</label>
                <select id="anomaly-severity" className={selectStyle} value={severity} onChange={(event) => setSeverity(event.target.value as SeverityFilter)}>
                  <option value="all">Todas las criticidades</option>
                  {(["P1", "P2", "P3"] as const).map((item) => <option key={item} value={item}>{severityLabels[item]}</option>)}
                </select>
              </div>
              <div><label className="text-sm text-subtle-foreground" htmlFor="anomaly-status">Estado</label>
                <select id="anomaly-status" className={selectStyle} value={status} onChange={(event) => setStatus(event.target.value as StatusFilter)}>
                  <option value="open">Abiertas</option>
                  {(["new", "investigating", "resolved", "false_positive"] as const).map((item) => <option key={item} value={item}>{statusLabels[item]}</option>)}
                  <option value="all">Todos los estados</option>
                </select>
              </div>
              <div><label className="text-sm text-subtle-foreground" htmlFor="anomaly-observation">Observación</label>
                <select id="anomaly-observation" className={selectStyle} value={observation} onChange={(event) => setObservation(event.target.value as ObservationFilter)}>
                  <option value="all">Todas</option><option value="observed">Se sigue observando</option><option value="no_longer_observed">Ya no se observa</option>
                </select>
              </div>
              <button onClick={reset} className={buttonStyle}>Restablecer filtros</button>
            </div>
            <p className="text-xs text-muted-foreground">Alta (P1): impacto acumulado de más de 2000 · Media (P2): de 500 a 2000 · Baja (P3): menos de 500, en la moneda de cada anomalía.</p>
            <p className="text-sm text-subtle-foreground">Mostrando {visible.length} de {episodes.length} anomalías · prioridad: criticidad, después impacto acumulado y después la más reciente.</p>
            {visible.length > 0 && <p className="text-xs text-info-foreground lg:hidden">Desliza la tabla para ver impacto, periodo y estado.</p>}
          </div>
          {visible.length === 0 ? <div className="px-5 py-12 text-center">
            <h4 className="font-semibold text-foreground">No hay anomalías con estos filtros</h4>
            <p className="mt-2 text-sm text-subtle-foreground">Prueba otra criticidad o restablece los filtros para ver las anomalías abiertas.</p>
            <button onClick={reset} className={`${buttonStyle} mt-5`}>Ver anomalías abiertas</button>
          </div> : <div role="region" aria-label="Lista de anomalías; desplazamiento horizontal disponible" tabIndex={0} className="relative overflow-x-auto rounded-b-lg focus-visible:outline-2 focus-visible:outline-highlight">
            <table className="w-full min-w-[860px] text-sm">
              <caption className="sr-only">Anomalías candidatas filtradas del cliente activo; impacto en la moneda de cada anomalía.</caption>
              <thead className="border-b border-border bg-background text-xs uppercase tracking-wider text-subtle-foreground">
                <tr><th scope="col" className="px-5 py-3 text-left">Criticidad</th><th scope="col" className="px-5 py-3 text-left">Servicio</th><th scope="col" className="px-5 py-3 text-right">Impacto acumulado</th><th scope="col" className="px-5 py-3 text-left">Periodo</th><th scope="col" className="px-5 py-3 text-left">Estado</th><th scope="col" className="px-5 py-3"><span className="sr-only">Detalle</span></th></tr>
              </thead>
              <tbody className="divide-y divide-border">
                {visible.map((item) => {
                  const service = item.service ?? "(sin servicio)";
                  return <tr key={item.id} data-new={newIds.has(item.id) ? "true" : undefined}
                    className={`align-top transition-colors hover:bg-accent ${newIds.has(item.id) ? "bg-highlight/10" : ""}`}>
                    <td className="px-5 py-5"><Badge className={severityStyles[item.severity]}>{severityLabels[item.severity]}</Badge></td>
                    <th scope="row" className="px-5 py-5 text-left font-normal"><p className="font-semibold text-foreground">{service}</p>
                      <p className="mt-1 text-xs text-subtle-foreground">+{money(openingExcess(item), item.currency)}/día el {dayLabel(item.start_date)}</p></th>
                    <td className="whitespace-nowrap px-5 py-5 text-right tabular-nums"><p className="font-semibold text-foreground">{money(item.accumulated_impact, item.currency)}</p>
                      <p className="mt-1 text-xs text-subtle-foreground">en {item.impact_day_count} días</p></td>
                    <td className="whitespace-nowrap px-5 py-5"><p className="text-foreground">{dayLabel(item.start_date)} → {dayLabel(item.last_seen_date)}</p>
                      <p className="mt-1 text-xs text-subtle-foreground">{observationText(item)}</p></td>
                    <td className="px-5 py-5"><Badge className={statusStyles[item.status]}>{statusLabels[item.status]}</Badge></td>
                    <td className="px-5 py-5 text-right"><button className={buttonStyle} aria-label={`Detalle de ${service}`}
                      onClick={() => setSelectedId(item.id)}>Detalle</button></td>
                  </tr>;
                })}
              </tbody>
            </table>
          </div>}
        </section>
      </>}

      <Dialog open={selected !== null} onOpenChange={(value) => { if (!value) setSelectedId(null); }}>
        <DialogContent className="max-h-[90vh] content-start overflow-y-auto [overflow-wrap:anywhere] max-sm:h-full max-sm:max-h-full max-sm:max-w-full max-sm:rounded-none">
          {selected && <EpisodeDetail key={selected.id + selected.status} episode={selected} token={token} tenantId={tenantId}
            onChanged={reload} onReload={reload} />}
        </DialogContent>
      </Dialog>
    </div>
  );
}
