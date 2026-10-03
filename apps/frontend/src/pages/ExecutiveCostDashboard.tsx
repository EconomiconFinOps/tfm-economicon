import { useState } from "react";
import { useOutletContext } from "react-router";
import { AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { ExportButton } from "@/components/ExportButton";
import { TagCoveragePanel } from "@/components/TagCoveragePanel";
import { chartTooltipStyle } from "@/components/chartTheme";
import { monthlyData, kpiData } from "@/data/demo/executiveCostDashboard";
import { useCostKpis } from "@/hooks/useCostKpis";
import type { SessionOutletContext } from "@/layouts/SessionGate";
import { ApiError } from "@/services/api";
import type { BillingGrouping } from "@/services/contracts";

export function ExecutiveCostDashboard() {
  const { token, activeTenant } = useOutletContext<SessionOutletContext>();
  const [period, setPeriod] = useState(() => {
    const now = new Date();
    return {
      start_date: new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), 1)).toISOString().slice(0, 10),
      end_date: new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth() + 1, 1)).toISOString().slice(0, 10)
    };
  });
  const [groupBy, setGroupBy] = useState<BillingGrouping>("service");
  const [tagKey, setTagKey] = useState("");
  const validSelection = Boolean(period.start_date && period.end_date && period.start_date < period.end_date
    && (groupBy !== "tag" || tagKey.trim()));
  const query = useCostKpis({
    token, tenantId: activeTenant?.id, enabled: validSelection,
    selection: { ...period, group_by: groupBy, ...(groupBy === "tag" ? { tag_key: tagKey } : {}) }
  });
  const billing = activeTenant && validSelection && !query.isError ? query.data : undefined;
  const overlap = query.error instanceof ApiError && query.error.status === 409
    && query.error.message.includes("ambiguous_cost_source");
  const inputClass = "mt-1 block w-full min-w-0 rounded-md border border-border bg-background p-2 text-foreground";
  const exportData = monthlyData.map(d => ({
    Mes: d.mes,
    'Total (€)': d.total,
    'Compute (€)': d.compute,
    'Storage (€)': d.storage,
    'Network (€)': d.network,
  }));

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="font-bold text-foreground">Dashboard Ejecutivo - Coste Global</h2>
          <p className="text-sm text-muted-foreground">Costes de Azure</p>
        </div>
      </div>

      <section aria-label="Costes reales de Azure" className="space-y-5">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <label className="min-w-0 text-sm text-subtle-foreground">Inicio (UTC)
            <input type="date" value={period.start_date} className={inputClass}
              onChange={(event) => setPeriod({ ...period, start_date: event.target.value })} />
          </label>
          <label className="min-w-0 text-sm text-subtle-foreground">Fin exclusivo (UTC)
            <input type="date" value={period.end_date} className={inputClass}
              onChange={(event) => setPeriod({ ...period, end_date: event.target.value })} />
          </label>
          <label className="min-w-0 text-sm text-subtle-foreground">Agrupar por
            <select value={groupBy} className={inputClass}
              onChange={(event) => setGroupBy(event.target.value as BillingGrouping)}>
              <option value="subscription">Suscripción</option>
              <option value="resource_group">Grupo de recursos</option>
              <option value="service">Servicio</option>
              <option value="project">Proyecto</option>
              <option value="tag">Etiqueta</option>
            </select>
          </label>
          {groupBy === "tag" && <label className="min-w-0 text-sm text-subtle-foreground">Clave de etiqueta
            <input value={tagKey} className={inputClass} onChange={(event) => setTagKey(event.target.value)} />
          </label>}
        </div>
        {!activeTenant ? <p role="status" className="text-subtle-foreground">Selecciona un cliente.</p>
          : !validSelection ? <p role="status" className="text-warning-text">Periodo incompleto o no válido; la etiqueta requiere una clave.</p>
          : query.isError ? <p role="alert" className="text-warning-text">{overlap
            ? "Posible solapamiento de fuentes de ingesta. Costes no disponibles para este periodo."
            : "Error al cargar costes. Datos no disponibles."}</p>
          : !billing ? <p role="status" className="text-subtle-foreground">Cargando costes...</p> : null}
        {billing && <>
          <p className="text-sm text-muted-foreground">{billing.period.start_date} a {billing.period.end_date} (fin exclusivo), {billing.period.timezone}</p>
          {billing.data_status === "partial" && <p role="status" className="text-warning-text">
            Datos parciales: {billing.missing_dimension_count} registros sin dimensión; {billing.excluded_undated_count} registros sin fecha excluidos.
          </p>}
          {billing.totals.length === 0 ? <p role="status" className="text-subtle-foreground">Sin datos de costes para este periodo.</p> : <>
            <div className="space-y-2">
              <h3 className="font-semibold text-foreground">Coste total del periodo</h3>
              {billing.totals.map((total) => <p key={total.currency} className="break-all font-bold text-foreground">{total.cost} {total.currency}</p>)}
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm text-subtle-foreground">
                <caption className="pb-3 text-left font-semibold text-foreground">Desglose de costes de Azure</caption>
                <thead className="border-b border-border"><tr>
                  <th scope="col" className="p-2">Dimensión</th>
                  <th scope="col" className="p-2">Suscripción</th>
                  <th scope="col" className="p-2">Moneda</th>
                  <th scope="col" className="p-2 text-right">Coste</th>
                  <th scope="col" className="p-2 text-right">Registros</th>
                </tr></thead>
                <tbody>{billing.groups.map((group) => <tr key={JSON.stringify([group.currency, group.subscription_id, group.value])} className="border-b border-border">
                  <th scope="row" className="max-w-64 break-words p-2 font-normal">{group.value ?? "Sin dimensión"}</th>
                  <td className="max-w-64 break-all p-2">{group.subscription_id ?? "No aplica"}</td>
                  <td className="p-2">{group.currency}</td>
                  <td className="p-2 text-right tabular-nums">{group.cost}</td>
                  <td className="p-2 text-right">{group.record_count}</td>
                </tr>)}</tbody>
              </table>
            </div>
          </>}
        </>}
        <p className="text-sm text-muted-foreground">Ahorro potencial: no disponible.</p>
      </section>

      <TagCoveragePanel token={token} tenantId={activeTenant?.id} period={period} />

      <section aria-label="Datos de demostración" className="space-y-6 border-t border-border pt-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <h3 className="font-semibold text-foreground">Demostración: evolución, inventario y exportación</h3>
          <ExportButton data={exportData} filename="demo-coste-global-ejecutivo" />
        </div>
        <p className="text-sm text-muted-foreground">Inventario demo: {kpiData[3].title}, {kpiData[3].value}</p>

      {/* Charts Row */}
      <div>
        {/* Trend Chart */}
        <div className="lg:col-span-2 bg-gradient-to-br from-card to-accent rounded-lg border border-border p-6 shadow-xl">
          <h3 className="font-semibold text-foreground mb-4">Evolución de Costes Mensuales</h3>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={monthlyData}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis dataKey="mes" stroke="var(--chart-axis)" />
              <YAxis stroke="var(--chart-axis)" />
              <Tooltip
                formatter={(value) => `${value.toLocaleString()}€`}
                contentStyle={chartTooltipStyle}
              />
              <Legend />
              <Area type="monotone" dataKey="total" stroke="var(--highlight)" fill="var(--primary)" fillOpacity={0.3} name="Total" />
            </AreaChart>
          </ResponsiveContainer>
        </div>

      </div>
      {/* Service Breakdown */}
      <div className="bg-gradient-to-br from-card to-accent rounded-lg border border-border p-6 shadow-xl">
        <h3 className="font-semibold text-foreground mb-4">Desglose por Categoría</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={monthlyData}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
            <XAxis dataKey="mes" stroke="var(--chart-axis)" />
            <YAxis stroke="var(--chart-axis)" />
            <Tooltip
              formatter={(value) => `${value.toLocaleString()}€`}
              contentStyle={chartTooltipStyle}
            />
            <Legend />
            <Bar dataKey="compute" fill="var(--primary)" name="Compute" />
            <Bar dataKey="storage" fill="var(--chart-2)" name="Storage" />
            <Bar dataKey="network" fill="var(--chart-5)" name="Network" />
          </BarChart>
        </ResponsiveContainer>
      </div>
      </section>
    </div>
  );
}
