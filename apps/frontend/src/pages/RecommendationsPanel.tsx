import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useOutletContext } from "react-router";
import { ArrowDownWideNarrow, ChevronDown, Download, FlaskConical, Lightbulb, ShieldCheck, SlidersHorizontal } from "lucide-react";
import { demoImpactReport, demoRecommendationReport, demoRecommendationTenant } from "@/data/demo/recommendationsPanel";
import { categoryLabels, defaultRecommendationFilters, difficultyLabels, downloadRecommendations, filterRecommendations, formatDecimal, recommendationRows, recommendationsCsv, savingsAmount } from "@/lib/recommendations";
import type { RecommendationFilters, RecommendationRow, SavingsPeriod } from "@/lib/recommendations";
import { defaultMonthSelection, selectedMonthRange } from "@/lib/executiveCostDashboard";
import { ApiError, fetchRecommendations, getSessionGeneration } from "@/services/api";
import type { ImpactReport, RecommendationReport } from "@/services/recommendations";
import type { SessionOutletContext } from "@/layouts/SessionGate";

const controlStyle = "mt-2 w-full min-w-0 rounded-md border border-neutral bg-background px-3 py-2.5 text-sm text-foreground focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-highlight";
const buttonStyle = "rounded-md border border-neutral px-4 py-2.5 text-sm text-subtle-foreground transition-colors hover:border-highlight hover:text-info-foreground disabled:cursor-not-allowed disabled:opacity-50";
const difficultyStyle = { low: "border-success/30 bg-success-tint/10 text-success-foreground", medium: "border-warning/30 bg-warning-tint/10 text-warning-foreground", high: "border-danger/30 bg-danger-tint/10 text-danger-foreground", unknown: "border-neutral/40 bg-neutral/10 text-subtle-foreground" };
const unevaluatedLabels = { rightsizing: "Dimensionamiento", scheduling: "Programación de uso", orphan_cleanup: "Recursos huérfanos", rate_optimization: "Optimización de tarifas", savings_impact: "Impacto económico" };

export function RecommendationsPanel() {
  const session = useOutletContext<SessionOutletContext | null>();
  const [mode, setMode] = useState<"demo" | "tenant">("demo");
  return <div className="min-w-0 space-y-6 p-4 text-subtle-foreground [overflow-wrap:anywhere] sm:p-6 [&_button:focus-visible]:outline-2 [&_button:focus-visible]:outline-offset-2 [&_button:focus-visible]:outline-highlight">
    <header className="flex flex-col justify-between gap-4 xl:flex-row xl:items-center">
      <div><p className="mb-1 text-xs font-semibold uppercase tracking-widest text-info-foreground">Optimización de costes · Azure</p>
        <h2 className="text-2xl font-bold text-foreground">Panel de Recomendaciones</h2>
        <p className="mt-1 text-sm">Prioriza oportunidades y revisa su evidencia antes de decidir.</p></div>
      <div role="group" aria-label="Origen de recomendaciones" className="flex w-fit flex-wrap gap-2">
        <button type="button" aria-pressed={mode === "demo"} onClick={() => setMode("demo")} className={`${buttonStyle} ${mode === "demo" ? "border-highlight bg-highlight/10 text-info-foreground" : ""}`}>Demostración</button>
        <button type="button" aria-pressed={mode === "tenant"} onClick={() => setMode("tenant")} className={`${buttonStyle} ${mode === "tenant" ? "border-highlight bg-highlight/10 text-info-foreground" : ""}`}>Consultar cliente</button>
      </div>
    </header>
    {mode === "demo" ? <>
      <aside aria-label="Datos de demostración" className="flex items-start gap-3 rounded-lg border border-highlight/30 bg-highlight/5 px-4 py-3">
        <FlaskConical aria-hidden="true" className="mt-0.5 h-5 w-5 shrink-0 text-info-foreground" />
        <div className="text-sm"><p className="font-semibold text-info-foreground">Demostración · septiembre de 2026</p><p className="mt-1">Ejemplos estáticos independientes del cliente seleccionado. Las dificultades y los escenarios de ahorro son hipotéticos; no son resultados reales ni ahorros garantizados.</p></div>
      </aside>
      <RecommendationsWorkbench report={demoRecommendationReport} impact={demoImpactReport} tenantId={demoRecommendationTenant} source="Demostración estática · datos simulados" />
    </> : session?.token ? <ClientRecommendations token={session.token} tenantId={session.activeTenant?.id} tenantName={session.activeTenant?.name} />
      : <p role="status" className="rounded-lg border border-border bg-card p-6">Inicia sesión y selecciona un cliente para consultar sus recomendaciones.</p>}
  </div>;
}

function ClientRecommendations({ token, tenantId, tenantName }: { token: string; tenantId?: string; tenantName?: string }) {
  const [month, setMonth] = useState(() => defaultMonthSelection().last);
  const range = selectedMonthRange(month, month);
  const generation = getSessionGeneration();
  const query = useQuery({
    queryKey: ["recommendations", 1, generation, tenantId, month],
    enabled: Boolean(token && tenantId && range), retry: false,
    queryFn: ({ signal }) => {
      if (!tenantId || !range) throw new Error("Selección incompleta");
      return fetchRecommendations(token, tenantId, { start_date: range.start_date, end_date: range.end_date }, signal);
    },
  });
  const report = token && tenantId && range && !query.isFetching && !query.isError ? query.data : undefined;
  const error = query.error instanceof ApiError && query.error.status === 404
    ? "La consulta de recomendaciones todavía no está disponible en este entorno."
    : "No se ha podido verificar el informe de recomendaciones. Vuelve a intentarlo.";
  return <>
    <section aria-label="Consulta del cliente" className="rounded-lg border border-border bg-card p-5">
      <div className="flex flex-col items-start gap-4 sm:flex-row sm:items-end sm:justify-between"><label className="w-full text-sm sm:w-60">Mes de análisis
        <input type="month" min="0001-01" max="9998-12" value={month} aria-invalid={!range} className={`${controlStyle} [color-scheme:dark]`} onChange={event => setMonth(event.target.value)} />
      </label><button type="button" className={buttonStyle} disabled={!tenantId || !range || query.isFetching} onClick={() => { void query.refetch(); }}>Actualizar recomendaciones</button></div>
      <p className="mt-3 text-sm">Cliente: <strong className="text-foreground">{tenantName ?? "sin seleccionar"}</strong> · Mes completo en UTC.</p>
      <p className="mt-2 text-xs text-muted-foreground">Consulta de solo lectura sobre costes almacenados. Los importes observados no prueban un ahorro potencial.</p>
    </section>
    {!tenantId ? <p role="status">Selecciona un cliente.</p> : !range ? <p role="status">Selecciona un mes válido entre los años 0001 y 9998.</p>
      : query.isFetching || (!report && !query.isError) ? <p role="status" className="rounded-lg border border-border bg-card p-8">Cargando recomendaciones del cliente…</p>
        : query.isError ? <div role="alert" className="rounded-lg border border-warning/30 bg-warning-tint/5 p-6"><p>{error}</p><button type="button" onClick={() => { void query.refetch(); }} className={`${buttonStyle} mt-4`}>Reintentar consulta</button></div> : null}
    {report && <><aside aria-label="Origen del informe" className="rounded-lg border border-highlight/30 bg-highlight/5 px-4 py-3 text-sm"><p className="font-semibold text-info-foreground">Datos simulados del cliente · costes almacenados de Azure</p><p className="mt-1">El informe identifica propuestas de revisión. El ahorro y la dificultad no evaluados permanecen sin estimar.</p></aside>
      <RecommendationsWorkbench key={`${generation}:${tenantId}:${month}`} report={report} source={`Cliente ${tenantName ?? tenantId} · datos simulados`} />
    </>}
  </>;
}

interface WorkbenchProps { report: RecommendationReport; impact?: ImpactReport; tenantId?: string; source: string }
export function RecommendationsWorkbench({ report, impact, tenantId, source }: WorkbenchProps) {
  const [filters, setFilters] = useState<RecommendationFilters>(defaultRecommendationFilters);
  const rows = recommendationRows(report, impact, tenantId);
  const visible = filterRecommendations(rows, filters);
  const estimated = visible.filter(row => savingsAmount(row, filters.period) !== null).length;
  const reset = () => setFilters(defaultRecommendationFilters);
  const update = <Key extends keyof RecommendationFilters>(key: Key, value: RecommendationFilters[Key]) => setFilters(previous => ({ ...previous, [key]: value }));
  return <>
    <section aria-label="Resumen de la vista actual" className="overflow-hidden rounded-lg border border-border bg-card">
      <div className="flex flex-wrap justify-between gap-2 border-b border-border px-5 py-3 text-xs"><span>Vista actual · el resumen cambia con los filtros</span><span className="tabular-nums">{report.period.start_date} → {report.period.end_date} <span className="text-muted-foreground">(fin exclusivo · UTC)</span></span></div>
      <dl className="grid grid-cols-2 lg:grid-cols-4">
        <div className="border-b border-r border-border bg-highlight/5 p-5 lg:border-b-0"><dt className="text-sm text-info-foreground">Recomendaciones visibles</dt><dd className="mt-2 text-3xl font-bold tabular-nums text-foreground">{visible.length}</dd><p className="mt-1 text-xs text-muted-foreground">de {rows.length} recibidas</p></div>
        <div className="border-b border-border p-5 lg:border-b-0 lg:border-r"><dt className="text-sm">Con estimación de ahorro</dt><dd className="mt-2 text-3xl font-semibold tabular-nums text-foreground">{estimated}</dd><p className="mt-1 text-xs text-muted-foreground">Incluye estimaciones de cero</p></div>
        <div className="border-r border-border p-5"><dt className="text-sm">Dificultad baja</dt><dd className="mt-2 text-3xl font-semibold tabular-nums text-success-foreground">{visible.filter(row => row.difficulty === "low").length}</dd><p className="mt-1 text-xs text-muted-foreground">Según la evaluación recibida</p></div>
        <div className="p-5"><dt className="text-sm">Ahorro sin estimar</dt><dd className="mt-2 text-3xl font-semibold tabular-nums text-foreground">{visible.length - estimated}</dd><p className="mt-1 text-xs text-muted-foreground">Información pendiente</p></div>
      </dl>
    </section>
    <section aria-labelledby="recommendations-list-title" className="min-w-0 overflow-hidden rounded-lg border border-border bg-card">
      <div className="space-y-4 border-b border-border p-5">
        <div className="flex flex-wrap items-center justify-between gap-4"><div className="flex items-center gap-2"><SlidersHorizontal aria-hidden="true" className="h-4 w-4 text-info-foreground" /><h3 id="recommendations-list-title" className="font-semibold text-foreground">Oportunidades para revisar</h3></div>
          <button type="button" disabled={visible.length === 0} className={`${buttonStyle} inline-flex items-center gap-2`} onClick={() => downloadRecommendations(recommendationsCsv(visible, report, filters.period, source, impact))}><Download aria-hidden="true" className="h-4 w-4" />Exportar vista CSV</button>
        </div>
        <div className="grid grid-cols-1 items-end gap-4 sm:grid-cols-2 xl:grid-cols-[1fr_1fr_1.1fr_.8fr_auto]">
          <label className="min-w-0 text-sm">Tipo<select className={controlStyle} value={filters.category} onChange={event => update("category", event.target.value as RecommendationFilters["category"])}><option value="all">Todos los tipos</option><option value="tagging">Etiquetado</option><option value="investigation">Investigación</option></select></label>
          <label className="min-w-0 text-sm">Dificultad<select className={controlStyle} value={filters.difficulty} onChange={event => update("difficulty", event.target.value as RecommendationFilters["difficulty"])}><option value="all">Todas las dificultades</option>{Object.entries(difficultyLabels).map(([key, label]) => <option key={key} value={key}>{label}</option>)}</select></label>
          <label className="min-w-0 text-sm">Ordenar por<select className={controlStyle} value={filters.order} onChange={event => update("order", event.target.value as RecommendationFilters["order"])}><option value="savings">Mayor ahorro estimado</option><option value="difficulty">Menor dificultad</option></select></label>
          <label className="min-w-0 text-sm">Ahorro estimado<select className={controlStyle} value={filters.period} onChange={event => update("period", event.target.value as SavingsPeriod)}><option value="monthly">Mensual</option><option value="annual">Anual</option></select></label>
          <button type="button" className={buttonStyle} onClick={reset}>Restablecer filtros</button>
        </div>
        <div className="flex flex-wrap items-start justify-between gap-2"><p role="status" className="text-sm">Mostrando {visible.length} de {rows.length} recomendaciones</p><p className="flex items-center gap-1.5 text-xs text-muted-foreground"><ArrowDownWideNarrow aria-hidden="true" className="h-3.5 w-3.5" />{filters.order === "savings" ? "Monedas separadas · mayor ahorro primero · sin estimación al final" : "Baja → alta → por evaluar · ahorro como desempate por moneda"}</p></div>
        <p className="text-xs text-muted-foreground">Las estimaciones no se suman: pueden solaparse. La proyección anual es la del escenario recibido, no un ahorro realizado.</p>
      </div>
      {visible.length ? <ol aria-label="Recomendaciones priorizadas" className="divide-y divide-border">{visible.map(row => <RecommendationCard key={row.id} row={row} period={filters.period} report={report} impactReport={impact} />)}</ol>
        : <div className="px-5 py-12 text-center"><Lightbulb aria-hidden="true" className="mx-auto mb-3 h-7 w-7 text-info-foreground" /><h4 className="font-semibold text-foreground">{rows.length ? "No hay recomendaciones con estos filtros" : "No hay recomendaciones para este periodo"}</h4><p className="mt-2 text-sm">{rows.length ? "Prueba otro tipo o dificultad para ampliar la vista." : "La ausencia de propuestas no confirma que el entorno esté optimizado. Revisa la cobertura y las limitaciones del informe."}</p>{rows.length > 0 && <button type="button" className={`${buttonStyle} mt-5`} onClick={reset}>Ver todas las recomendaciones</button>}</div>}
    </section>
    <section aria-label="Cobertura y límites del informe" className="rounded-lg border border-border bg-card p-5 text-sm">
      <h3 className="font-semibold text-foreground">Cobertura y límites del informe</h3>
      {report.truncated && <p className="mt-3 text-warning-foreground">Informe limitado: se recibieron {rows.length} de {report.total_candidates} candidatos. Los filtros y la exportación actúan sobre los recibidos.</p>}
      {report.data_status === "partial" && <p className="mt-3 text-warning-foreground">Datos parciales: {report.missing_dimension_count} registros sin proyecto; {report.excluded_undated_count} registros sin fecha excluidos.</p>}
      <ul className="mt-3 list-disc space-y-2 pl-5">{[...report.assumptions, ...report.limitations, ...(impact?.assumptions ?? []), ...(impact?.limitations ?? [])].map((text, index) => <li key={index}>{text}</li>)}</ul>
      {report.not_evaluated.length > 0 && <div className="mt-4 border-t border-border pt-4"><p className="font-medium text-foreground">Fuera de la evaluación</p><ul className="mt-2 space-y-1">{report.not_evaluated.map(item => <li key={item.action}><span className="text-info-foreground">{unevaluatedLabels[item.action]}</span>: faltan {item.missing_inputs.join(", ")}.</li>)}</ul></div>}
    </section>
  </>;
}

function RecommendationCard({ row, period, report, impactReport }: { row: RecommendationRow; period: SavingsPeriod; report: RecommendationReport; impactReport?: ImpactReport }) {
  const amount = savingsAmount(row, period);
  return <li className="p-5 transition-colors hover:bg-accent/30">
    <article aria-label={row.action} className="min-w-0">
      <div className="grid min-w-0 gap-5 lg:grid-cols-[minmax(0,1fr)_minmax(180px,.32fr)]">
        <div className="min-w-0"><div className="mb-2 flex flex-wrap items-center gap-2 text-xs"><span className="rounded border border-border bg-background px-2 py-1 text-info-foreground">{categoryLabels[row.category]}</span><span className="text-muted-foreground">{row.qualification === "supported" ? "Hallazgo respaldado por costes" : "Candidato a investigación"}</span></div>
          <h4 className="break-words text-base font-semibold text-foreground">{row.action}</h4><p className="mt-2 text-sm leading-relaxed">{row.rationale}</p>
          <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-2 text-xs"><span className={`rounded-md border px-2 py-1 font-medium ${difficultyStyle[row.difficulty]}`}>Dificultad: {difficultyLabels[row.difficulty]}</span><span className="text-muted-foreground">Proyecto: {row.scope.value ?? "Sin asignar"}</span></div>
        </div>
        <div className="border-t border-border pt-4 lg:border-l lg:border-t-0 lg:pl-5 lg:pt-0"><p className="text-xs text-muted-foreground">Ahorro potencial · {period === "monthly" ? "mensual" : "anual"}</p><p className={`mt-1 break-words text-2xl font-semibold tabular-nums ${amount === null ? "text-subtle-foreground" : "text-success-foreground"}`}>{amount === null ? "No estimado" : formatDecimal(amount)}{amount !== null && <span className="ml-2 text-sm font-normal">{row.impact?.scenario.currency}</span>}</p><p className="mt-2 text-xs text-muted-foreground">{amount === null ? "Faltan datos para cuantificar" : row.impact?.status === "no_savings" ? "Escenario sin ahorro previsto" : "Estimación de escenario"}</p>{Boolean(row.impact?.excluded_by.length) && <p className="mt-2 text-xs text-warning-foreground">Alternativa solapada · excluida del total</p>}</div>
      </div>
      <details className="group mt-4 rounded-md border border-border bg-background/40">
        <summary className="flex cursor-pointer list-none items-center justify-between gap-2 rounded-md px-4 py-3 text-sm font-medium text-info-foreground focus-visible:outline-2 focus-visible:outline-highlight [&::-webkit-details-marker]:hidden"><span>Ver acción y evidencia<span className="sr-only">: {row.action}</span></span><ChevronDown aria-hidden="true" className="h-4 w-4 shrink-0 transition-transform group-open:rotate-180" /></summary>
        <div className="space-y-5 border-t border-border p-4 text-sm">
          <div className="flex items-start gap-2 text-warning-foreground"><ShieldCheck aria-hidden="true" className="mt-0.5 h-4 w-4 shrink-0" /><p>Requiere aprobación humana. Revisa el alcance, el riesgo y la evidencia con el propietario antes de cualquier cambio.</p></div>
          <div><h5 className="font-semibold text-foreground">Acción propuesta</h5><p className="mt-1">{row.action}</p></div>
          <dl className="grid grid-cols-2 gap-4"><div><dt className="text-muted-foreground">Riesgo</dt><dd className="mt-1 font-medium text-foreground">{difficultyLabels[row.risk]}</dd></div><div><dt className="text-muted-foreground">Confianza</dt><dd className="mt-1 font-medium text-foreground">{difficultyLabels[row.confidence]}</dd></div></dl>
          <div><h5 className="font-semibold text-foreground">Evidencia de costes</h5>{row.evidence.map(item => <div key={item.id} className="mt-2 rounded-md border border-border p-3"><p className="font-medium tabular-nums text-foreground">{formatDecimal(item.observed_cost.amount)} {item.observed_cost.currency} observados · {item.observed_cost.record_count} registros</p><p className="mt-1 text-xs">{item.query.period.start_date} → {item.query.period.end_date} (fin exclusivo · UTC) · Proyecto: {item.scope.value ?? "Sin asignar"}</p><p className="mt-2 break-all text-xs text-muted-foreground">Fuente: {item.source} · Regla: {item.rule_id} v{item.rule_version}</p><p className="mt-1 break-all text-xs text-muted-foreground">ID: {item.id}</p></div>)}</div>
          {row.impact && <div><h5 className="font-semibold text-foreground">Escenario de impacto recibido</h5><p className="mt-1">{row.impact.included_in_total ? "Incluido en el total de su moneda en el informe de impacto." : row.impact.excluded_by.length ? "Excluido del total por compartir alcance con otra recomendación." : "No incluido en el total del informe."}</p>{row.impact.excluded_by.map(id => <p key={id} className="mt-1 break-all text-xs text-muted-foreground">Alternativa priorizada: {id}</p>)}<p className="mt-2 break-words text-xs">Alcance: {row.impact.scenario.cost_scope_ids.join(", ")}</p><p className="mt-2 text-xs">Base mensual: {row.impact.scenario.baseline_monthly_cost === null ? "No disponible" : `${formatDecimal(row.impact.scenario.baseline_monthly_cost)} ${row.impact.scenario.currency}`} · Objetivo mensual: {row.impact.scenario.target_monthly_cost === null ? "No disponible" : `${formatDecimal(row.impact.scenario.target_monthly_cost)} ${row.impact.scenario.currency}`}</p></div>}
          <div><h5 className="font-semibold text-foreground">Supuestos y limitaciones</h5><ul className="mt-2 list-disc space-y-1 pl-5">{[...report.assumptions, ...(row.impact?.scenario.assumptions ?? []), ...(impactReport?.assumptions ?? []), ...report.limitations, ...(impactReport?.limitations ?? [])].map((text, index) => <li key={index}>{text}</li>)}</ul></div>
        </div>
      </details>
    </article>
  </li>;
}
