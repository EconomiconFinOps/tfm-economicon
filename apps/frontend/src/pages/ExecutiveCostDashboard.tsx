import { useEffect, useMemo, useState } from "react";
import { useOutletContext } from "react-router";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { RefreshCw } from "lucide-react";
import { MetricCard } from "@/components/MetricCard";
import { SectionCard } from "@/components/SectionCard";
import { chartTooltipItemStyle, chartTooltipStyle } from "@/components/chartTheme";
import { useExecutiveCostKpis } from "@/hooks/useExecutiveCostKpis";
import {
  compareEndpoints, currentUtcMonth, defaultMonthSelection, describeCostError,
  monthlyCostPoint, monthLabel, selectedMonthRange, snapshotCurrencies
} from "@/lib/executiveCostDashboard";
import type { MonthlyCostPoint } from "@/lib/executiveCostDashboard";
import type { SessionOutletContext } from "@/layouts/SessionGate";
import type { BillingGrouping } from "@/services/contracts";

const inputClass = "mt-1 block w-full min-w-0 rounded-md border border-input bg-background p-2 text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring";
const buttonClass = "inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm text-primary-foreground transition-all hover:bg-primary/90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:cursor-wait disabled:opacity-50";

export function ExecutiveCostDashboard() {
  const { token, activeTenant } = useOutletContext<SessionOutletContext>();
  const [period, setPeriod] = useState(defaultMonthSelection);
  const [groupBy, setGroupBy] = useState<BillingGrouping>("service");
  const [tagKey, setTagKey] = useState("");
  const [selectedCurrency, setSelectedCurrency] = useState("");
  const range = useMemo(() => selectedMonthRange(period.first, period.last), [period.first, period.last]);
  const validSelection = Boolean(range && (groupBy !== "tag" || tagKey.trim()));
  const query = useExecutiveCostKpis({
    token, tenantId: activeTenant?.id, enabled: validSelection,
    months: range?.months ?? [],
    selection: {
      start_date: range?.start_date, end_date: range?.end_date, group_by: groupBy,
      ...(groupBy === "tag" ? { tag_key: tagKey } : {})
    }
  });
  // Query may retain cached data during refetch. It is deliberately not a
  // displayed result until this execution has settled under the active scope.
  const snapshot = token && activeTenant && validSelection && !query.isFetching && !query.isError
    ? query.data : undefined;
  const billing = snapshot?.aggregate.kind === "success" ? snapshot.aggregate.data : undefined;
  const currencies = useMemo(() => snapshot && billing ? snapshotCurrencies(snapshot) : [], [snapshot, billing]);
  const currency = currencies.includes(selectedCurrency) ? selectedCurrency : currencies[0] ?? "";
  useEffect(() => {
    if (snapshot && billing) {
      setSelectedCurrency((previous) => currencies.includes(previous) ? previous : currencies[0] ?? "");
    }
  }, [snapshot, billing, currencies]);
  const points = useMemo(() => snapshot && billing
    ? snapshot.months.map(({ month, result }) => monthlyCostPoint(month, result, currency)) : [],
  [snapshot, billing, currency]);
  const comparison = compareEndpoints(points, currency);
  const monthlyErrors = snapshot?.months.some(({ result }) => result.kind === "error") ?? false;
  const aggregateError = snapshot?.aggregate.kind === "error" ? snapshot.aggregate.error : query.error;
  const hasError = query.isError || snapshot?.aggregate.kind === "error" || monthlyErrors;
  const today = currentUtcMonth();
  const labels = period.first && period.last && range ? monthLabel(period.first) + " – " + monthLabel(period.last) : "";
  const periodNotice = range?.months.some((month) => month >= today);
  const partialMonths = points.some((point) => point.partial);

  return (
    <div className="min-w-0 space-y-6 p-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="min-w-0">
          <h2 className="font-bold text-foreground">Dashboard Ejecutivo - Coste Global</h2>
          <p className="text-sm text-muted-foreground">Costes de Azure almacenados y normalizados</p>
        </div>
        {activeTenant && validSelection && <button type="button" className={buttonClass}
          disabled={query.isFetching} onClick={() => { void query.refetch(); }}>
          <RefreshCw className="h-4 w-4" aria-hidden="true" />
          {hasError ? "Reintentar" : "Actualizar costes"}
        </button>}
      </div>

      <section aria-label="Selección de costes de Azure" className="space-y-3">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <label className="min-w-0 text-sm text-subtle-foreground">Mes inicial
            <input type="month" min="0001-01" max="9998-12" value={period.first} className={inputClass}
              aria-invalid={!range} aria-describedby="executive-period-help"
              onChange={(event) => setPeriod({ ...period, first: event.target.value })} />
          </label>
          <label className="min-w-0 text-sm text-subtle-foreground">Mes final
            <input type="month" min="0001-01" max="9998-12" value={period.last} className={inputClass}
              aria-invalid={!range} aria-describedby="executive-period-help"
              onChange={(event) => setPeriod({ ...period, last: event.target.value })} />
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
            <input value={tagKey} className={inputClass} aria-invalid={!tagKey.trim()}
              onChange={(event) => setTagKey(event.target.value)} />
          </label>}
        </div>
        <p id="executive-period-help" className="text-sm text-muted-foreground">
          Ambos meses están incluidos. El valor inicial son los seis últimos meses completos en UTC.
        </p>
        {range && <p className="text-sm text-muted-foreground">{labels} (UTC)</p>}
        {periodNotice && <p role="status" className="text-sm text-warning-text">
          {range?.months.includes(today) && "El mes en curso puede tener datos incompletos. "}
          {range?.months.some((month) => month > today) && "El intervalo incluye meses futuros. "}
          Se muestran solo costes almacenados; no son una previsión.
        </p>}
      </section>

      <div aria-live="polite" aria-atomic="true">
        {!activeTenant ? <p role="status" className="text-subtle-foreground">Selecciona un cliente.</p>
          : !validSelection ? <p role="status" className="text-warning-text">
            Periodo incompleto o no válido (años 0001–9998, inicio no posterior al fin); la etiqueta requiere una clave.
          </p>
          : query.isFetching || !snapshot && !query.isError
            ? <p role="status" className="text-subtle-foreground">Cargando costes...</p>
            : !billing ? <p role="alert" className="text-warning-text">{describeCostError(aggregateError)}</p> : null}
      </div>

      {billing && snapshot && <>
        {billing.tag_key !== null && <p className="text-sm text-muted-foreground">Etiqueta consultada: {billing.tag_key}</p>}
        {billing.data_status === "partial" && <p role="status" className="text-sm text-warning-text">
          Datos parciales: {billing.missing_dimension_count} registros sin dimensión; {billing.excluded_undated_count} registros sin fecha excluidos.
          El recuento sin fecha pertenece al cliente completo y no se suma por mes.
        </p>}
        {partialMonths && billing.data_status !== "partial" && <p role="status" className="text-sm text-warning-text">
          Hay meses con datos parciales. Consulta sus avisos en la tabla mensual.
        </p>}
        {monthlyErrors && <p role="status" className="text-sm text-warning-text">
          No se pudieron consultar todos los meses. Los errores aparecen como huecos y se detallan en la tabla.
        </p>}

        {billing.totals.length > 0 && <SectionCard title="Desglose del periodo" subtitle={labels}>
          <div className="max-w-full overflow-x-auto">
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
                <td className="max-w-64 break-all p-2">{group.subscription_id
                  ?? (groupBy === "subscription" || groupBy === "resource_group" ? "Sin suscripción" : "No aplica")}</td>
                <td className="p-2">{group.currency}</td>
                <td className="p-2 text-right tabular-nums">{group.cost}</td>
                <td className="p-2 text-right">{group.record_count}</td>
              </tr>)}</tbody>
            </table>
          </div>
          <p className="mt-3 text-sm text-muted-foreground">Cada grupo se redondea por consulta; su suma puede diferir del total.</p>
        </SectionCard>}

        {billing.totals.length ? <section aria-label="Totales de costes" className="space-y-3">
          <h3 className="font-semibold text-foreground">Coste total del periodo</h3>
          <div className="grid min-w-0 grid-cols-1 gap-4 break-all sm:grid-cols-2 lg:grid-cols-3">
            {billing.totals.map((total) => <MetricCard key={total.currency} label={"Total " + total.currency}
              value={total.cost + " " + total.currency} detail={labels + " · " + total.record_count + " registros"} />)}
          </div>
        </section> : <p role="status" className="text-subtle-foreground">Sin datos de costes para este periodo.</p>}

        <section aria-label="Comparación de meses" className="space-y-3">
          <h3 className="font-semibold text-foreground">
            {comparison.available
              ? "Comparación: " + monthLabel(comparison.lastMonth) + " frente a " + monthLabel(comparison.firstMonth)
              : "Comparación de meses"}{currency ? " · " + currency : ""}
          </h3>
          {comparison.available ? <>
            {comparison.interiorErrors && <p role="status" className="text-sm text-warning-text">
              Comparación de costes observados: hay errores en meses interiores. Consulta sus causas en la tabla mensual.
            </p>}
            <div className="grid min-w-0 grid-cols-1 gap-4 break-all sm:grid-cols-2">
              <MetricCard label="Variación absoluta" value={comparison.difference + " " + currency}
                detail={"Último mes con coste menos primer mes con coste" + (comparison.partial ? " · datos parciales observados" : "")} />
              <MetricCard label="Variación porcentual" value={comparison.percent + " %"}
                detail={"Respecto al primer mes con coste" + (comparison.negativeBase ? " · base negativa" : "")
                  + (comparison.partial ? " · datos parciales observados" : "")} />
            </div>
          </> : <p className="text-sm text-muted-foreground">Comparación no disponible: {comparison.reason}</p>}
        </section>

        <SectionCard title="Evolución de costes mensuales" subtitle="Un punto por mes, para la moneda seleccionada">
          <div className="space-y-4">
            <label className="block max-w-xs text-sm text-subtle-foreground">Moneda
              <select value={currency} disabled={!currencies.length} className={inputClass}
                onChange={(event) => setSelectedCurrency(event.target.value)}>
                {!currencies.length && <option value="">Sin moneda observada</option>}
                {currencies.map((code) => <option key={code} value={code}>{code}</option>)}
              </select>
            </label>
            {currency && <div className="min-w-0" role="img" aria-label={"Gráfico mensual en " + currency + "; valores exactos en la tabla de costes mensuales"}>
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={points}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                  <XAxis dataKey="label" stroke="var(--chart-axis)" />
                  <YAxis stroke="var(--chart-axis)" />
                  <Tooltip contentStyle={chartTooltipStyle} itemStyle={chartTooltipItemStyle} formatter={(_value, _name, item) => {
                    const point = item.payload as MonthlyCostPoint;
                    return point.cost === null ? "Sin datos" : point.cost + " " + currency;
                  }} />
                  <Area type="monotone" dataKey="value" name={currency} connectNulls={false} isAnimationActive={false}
                    dot={{ r: 3, fill: "var(--chart-1)", fillOpacity: 1 }}
                    stroke="var(--chart-1)" fill="var(--chart-1)" fillOpacity={0.3} />
                </AreaChart>
              </ResponsiveContainer>
            </div>}
            {points.some((point) => point.representationLimited) && <p role="status" className="text-sm text-warning-text">
              Algunos importes superan el límite de representación gráfica. Sus valores exactos permanecen en la tabla.
            </p>}
            <p className="text-sm text-muted-foreground">
              Los huecos indican ausencia, error o límite de representación, nunca un cero supuesto.
              El total del intervalo y cada mes se redondean por consulta: la suma de meses puede diferir del total.
            </p>
            <div className="max-w-full overflow-x-auto">
              <table className="w-full text-left text-sm text-subtle-foreground">
                <caption className="pb-3 text-left font-semibold text-foreground">Costes mensuales</caption>
                <thead className="border-b border-border"><tr>
                  <th scope="col" className="p-2">Mes</th>
                  <th scope="col" className="p-2">Moneda</th>
                  <th scope="col" className="p-2 text-right">Coste</th>
                  <th scope="col" className="p-2 text-right">Registros</th>
                  <th scope="col" className="p-2">Estado</th>
                </tr></thead>
                <tbody>{points.map((point) => <tr key={point.month} className="border-b border-border">
                  <th scope="row" className="p-2 font-normal">{point.label}</th>
                  <td className="p-2">{currency || "—"}</td>
                  <td className="p-2 text-right tabular-nums">{point.cost ?? "—"}</td>
                  <td className="p-2 text-right">{point.recordCount ?? "—"}</td>
                  <td className="max-w-sm p-2">{point.notice}
                    {point.partial && <p className="text-xs text-warning-text">
                      Datos parciales: {point.missingDimensions} sin dimensión; {point.undated} sin fecha (recuento del cliente).
                    </p>}
                  </td>
                </tr>)}</tbody>
              </table>
            </div>
          </div>
        </SectionCard>

        <p className="text-sm text-muted-foreground">
          Son consultas de registros almacenados, sin un corte de datos común entre peticiones.
          Actualizar permite volver a consultar; disponer de registros no certifica cobertura completa de Azure.
        </p>
      </>}
      <p className="text-sm text-muted-foreground">Ahorro potencial: no disponible.</p>
    </div>
  );
}
