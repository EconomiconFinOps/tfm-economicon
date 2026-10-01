import { useState } from "react";
import { AlertTriangle, FlaskConical, SlidersHorizontal } from "lucide-react";
import { ExportButton } from "@/components/ExportButton";
import { anomalies, demoPeriod, type AnomalySeverity, type AnomalyStatus } from "@/data/demo/anomaliesPanel";

type StatusFilter = "Abiertas" | "Todos" | AnomalyStatus;
type SeverityFilter = "Todas" | AnomalySeverity;
const severityRank: Record<AnomalySeverity, number> = { Alta: 3, Media: 2, Baja: 1 };
const severityStyles: Record<AnomalySeverity, string> = {
  Alta: "border-red-400/30 bg-red-500/10 text-red-300",
  Media: "border-amber-400/30 bg-amber-500/10 text-amber-200",
  Baja: "border-cyan-400/30 bg-cyan-500/10 text-cyan-200",
};
const statusStyles: Record<AnomalyStatus, string> = {
  Pendiente: "border-slate-500/40 bg-slate-500/10 text-slate-200",
  Investigando: "border-amber-400/30 bg-amber-500/10 text-amber-200",
  Resuelto: "border-emerald-400/30 bg-emerald-500/10 text-emerald-200",
};
const currency = new Intl.NumberFormat("es-ES", { style: "currency", currency: "EUR", maximumFractionDigits: 0 });
const selectStyle = "mt-2 w-full rounded-md border border-slate-600 bg-[#0f1419] px-3 py-2.5 text-sm text-white focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-cyan-400";

export function AnomaliesPanel() {
  const [severity, setSeverity] = useState<SeverityFilter>("Todas");
  const [status, setStatus] = useState<StatusFilter>("Abiertas");
  const [sort, setSort] = useState("severity");
  const open = anomalies.filter(anomaly => anomaly.estado !== "Resuelto");
  const openImpact = open.reduce((total, anomaly) => total + anomaly.coste, 0);
  const visible = anomalies.filter(anomaly =>
    (severity === "Todas" || anomaly.severidad === severity) &&
    (status === "Todos" || (status === "Abiertas" ? anomaly.estado !== "Resuelto" : anomaly.estado === status))
  ).sort((a, b) => sort === "impact"
    ? b.coste - a.coste || severityRank[b.severidad] - severityRank[a.severidad]
    : severityRank[b.severidad] - severityRank[a.severidad] || b.coste - a.coste);
  const reset = () => { setSeverity("Todas"); setStatus("Abiertas"); setSort("severity"); };
  const exportData = visible.map(anomaly => ({
    Origen: "Datos de demostración",
    Periodo: demoPeriod,
    Severidad: anomaly.severidad,
    Servicio: anomaly.servicio,
    Tipo: anomaly.tipo,
    Descripción: anomaly.descripcion,
    "Impacto estimado (EUR)": anomaly.coste,
    Detectado: anomaly.detectado,
    Estado: anomaly.estado,
  }));

  return (
    <div className="min-w-0 space-y-6 p-4 text-slate-200 sm:p-6 [&_button:focus-visible]:outline-2 [&_button:focus-visible]:outline-offset-2 [&_button:focus-visible]:outline-cyan-400">
      <header className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
        <div>
          <p className="mb-1 text-xs font-semibold uppercase tracking-widest text-cyan-300">Supervisión de costes</p>
          <h2 className="text-2xl font-bold text-white">Panel de Anomalías y Alertas</h2>
          <p className="mt-1 text-sm text-slate-300">Prioriza las alertas por criticidad e impacto estimado.</p>
        </div>
        <div className="self-start">
          {visible.length > 0 ? <ExportButton data={exportData} filename="anomalias-alertas-demo-2026-04-18_19" /> :
            <button disabled className="rounded-md border border-slate-600 px-4 py-2 text-slate-400">Exportar Resultados</button>}
          <p className="mt-2 text-xs text-slate-400">Exporta la vista actual · archivo demo</p>
        </div>
      </header>

      <aside aria-label="Datos de demostración" className="flex items-start gap-3 rounded-lg border border-cyan-500/30 bg-cyan-500/5 px-4 py-3">
        <FlaskConical aria-hidden="true" className="mt-0.5 h-5 w-5 shrink-0 text-cyan-300" />
        <div className="text-sm">
          <p className="font-semibold text-cyan-200">Datos de demostración · {demoPeriod}</p>
          <p className="mt-1 text-slate-300">Ejemplos estáticos independientes del cliente seleccionado, sin conexión a detección real. El impacto estimado corresponde al periodo de muestra; no representa pérdidas ni ahorros reales.</p>
        </div>
      </aside>

      <section aria-label="Resumen del conjunto de muestra" className="overflow-hidden rounded-lg border border-[#2d3748] bg-[#1a1f2e]">
        <div className="border-b border-[#2d3748] px-5 py-3 text-xs text-slate-300">Conjunto de muestra · {anomalies.length} anomalías · El resumen no cambia con los filtros</div>
        <dl className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-[1.4fr_1fr_1fr_1fr]">
          <div className="border-b border-[#2d3748] bg-cyan-500/5 p-5 md:border-r xl:border-b-0">
            <dt className="text-sm text-cyan-200">Impacto de anomalías abiertas</dt>
            <dd className="mt-2 text-3xl font-bold tabular-nums text-white">{currency.format(openImpact)}</dd>
            <p className="mt-2 text-xs text-slate-300">Estimado · EUR · periodo de muestra</p>
          </div>
          <div className="border-b border-[#2d3748] p-5 xl:border-b-0 xl:border-r">
            <dt className="text-sm text-slate-300">Anomalías abiertas</dt>
            <dd className="mt-2 text-3xl font-semibold tabular-nums text-white">{open.length}</dd>
            <p className="mt-2 text-xs text-slate-400">Pendientes o en investigación</p>
          </div>
          <div className="border-b border-[#2d3748] p-5 md:border-b-0 md:border-r">
            <dt className="flex items-center gap-2 text-sm text-red-300"><AlertTriangle aria-hidden="true" className="h-4 w-4" />Criticidad alta · abiertas</dt>
            <dd className="mt-2 text-3xl font-semibold tabular-nums text-red-300">{open.filter(anomaly => anomaly.severidad === "Alta").length}</dd>
            <p className="mt-2 text-xs text-slate-400">Prioridad de revisión</p>
          </div>
          <div className="p-5">
            <dt className="text-sm text-slate-300">Anomalías resueltas</dt>
            <dd className="mt-2 text-3xl font-semibold tabular-nums text-white">{anomalies.length - open.length}</dd>
            <p className="mt-2 text-xs text-slate-400">En el conjunto de muestra</p>
          </div>
        </dl>
      </section>

      <section aria-labelledby="alerts-title" className="min-w-0 rounded-lg border border-[#2d3748] bg-[#1a1f2e]">
        <div className="space-y-5 border-b border-[#2d3748] p-5">
          <div className="flex items-center gap-2"><SlidersHorizontal aria-hidden="true" className="h-4 w-4 text-cyan-300" /><h3 id="alerts-title" className="font-semibold text-white">Bandeja de alertas</h3></div>
          <div className="grid grid-cols-1 items-end gap-4 md:grid-cols-3 xl:grid-cols-[1fr_1fr_1.4fr_auto]">
            <div><label className="text-sm text-slate-300" htmlFor="anomaly-severity">Criticidad</label>
              <select id="anomaly-severity" className={selectStyle} value={severity} onChange={event => setSeverity(event.target.value as SeverityFilter)}>
                <option value="Todas">Todas las criticidades</option><option>Alta</option><option>Media</option><option>Baja</option>
              </select>
            </div>
            <div><label className="text-sm text-slate-300" htmlFor="anomaly-status">Estado</label>
              <select id="anomaly-status" className={selectStyle} value={status} onChange={event => setStatus(event.target.value as StatusFilter)}>
                <option value="Abiertas">Abiertas</option><option value="Todos">Todos los estados</option><option>Pendiente</option><option>Investigando</option><option>Resuelto</option>
              </select>
            </div>
            <div><label className="text-sm text-slate-300" htmlFor="anomaly-sort">Ordenar por</label>
              <select id="anomaly-sort" className={selectStyle} value={sort} onChange={event => setSort(event.target.value)}>
                <option value="severity">Criticidad e impacto</option><option value="impact">Mayor impacto</option>
              </select>
            </div>
            <button onClick={reset} className="rounded-md border border-slate-600 px-4 py-2.5 text-sm text-slate-200 hover:border-cyan-400 hover:text-cyan-200">Restablecer filtros</button>
          </div>
          <p role="status" className="text-sm text-slate-300">Mostrando {visible.length} de {anomalies.length} anomalías de muestra · {status === "Abiertas" ? "Solo abiertas" : status === "Todos" ? "Todos los estados" : status}</p>
          {visible.length > 0 && <p className="text-xs text-cyan-200 lg:hidden">Desliza la tabla para ver impacto, fecha y estado.</p>}
        </div>
        {visible.length === 0 ? <div className="px-5 py-12 text-center">
          <h4 className="font-semibold text-white">No hay alertas con estos filtros</h4>
          <p className="mt-2 text-sm text-slate-300">Prueba otra criticidad o restablece los filtros para ver las anomalías abiertas.</p>
          <button onClick={reset} className="mt-5 rounded-md border border-cyan-400/50 px-4 py-2 text-sm text-cyan-200 hover:bg-cyan-500/10">Ver anomalías abiertas</button>
        </div> : <div role="region" aria-label="Lista de anomalías; desplazamiento horizontal disponible" tabIndex={0} className="overflow-x-auto rounded-b-lg focus-visible:outline-2 focus-visible:outline-cyan-400">
          <table className="w-full min-w-[860px] text-sm">
            <caption className="sr-only">Alertas filtradas. Impacto estimado en euros para {demoPeriod}; datos de demostración.</caption>
            <thead className="border-b border-[#2d3748] bg-[#0f1419] text-xs uppercase tracking-wider text-slate-300">
              <tr><th scope="col" className="px-5 py-3 text-left">Criticidad</th><th scope="col" className="px-5 py-3 text-left">Servicio / anomalía</th><th scope="col" className="px-5 py-3 text-right">Impacto estimado</th><th scope="col" className="px-5 py-3 text-left">Detección</th><th scope="col" className="px-5 py-3 text-left">Estado</th></tr>
            </thead>
            <tbody className="divide-y divide-[#2d3748]">
              {visible.map(anomaly => <tr key={anomaly.id} className="align-top transition-colors hover:bg-[#232834]">
                <td className="px-5 py-5"><span className={`inline-flex rounded-md border px-2 py-1 text-xs font-semibold ${severityStyles[anomaly.severidad]}`}>{anomaly.severidad}</span></td>
                <th scope="row" className="max-w-sm px-5 py-5 text-left font-normal"><p className="font-semibold text-white">{anomaly.servicio}</p><p className="mt-1 text-xs text-cyan-200">{anomaly.tipo}</p><p className="mt-2 text-sm text-slate-300">{anomaly.descripcion}</p></th>
                <td className="whitespace-nowrap px-5 py-5 text-right font-semibold tabular-nums text-white">{currency.format(anomaly.coste)}</td>
                <td className="whitespace-nowrap px-5 py-5 text-slate-300"><time dateTime={anomaly.detectado.replace(" ", "T")}>{anomaly.detectado}</time></td>
                <td className="px-5 py-5"><span className={`inline-flex rounded-md border px-2 py-1 text-xs ${statusStyles[anomaly.estado]}`}>{anomaly.estado}</span></td>
              </tr>)}
            </tbody>
          </table>
        </div>}
      </section>
    </div>
  );
}
