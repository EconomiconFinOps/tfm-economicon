import { useState } from "react";
import { useOutletContext } from "react-router";
import { Download, RefreshCw } from "lucide-react";
import { MetricCard } from "@/components/MetricCard";
import { SectionCard } from "@/components/SectionCard";
import { useCostKpis } from "@/hooks/useCostKpis";
import type { SessionOutletContext } from "@/layouts/SessionGate";
import { describeCostError } from "@/lib/executiveCostDashboard";
import { defaultOperationalSelection, downloadOperationalCosts, operationalBillingSelection, operationalSelectionError } from "@/lib/operationalCostDashboard";
import type { OperationalSelection } from "@/lib/operationalCostDashboard";
import { getSessionGeneration } from "@/services/api";
import { billingFilterKeys } from "@/services/contracts";
import type { BillingGrouping } from "@/services/contracts";

const inputClass = "mt-1 block w-full min-w-0 rounded-md border border-border bg-background p-2 text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring";
const buttonClass = "inline-flex items-center justify-center gap-2 rounded-md border border-border bg-primary px-4 py-2 text-sm text-foreground transition-colors hover:bg-highlight focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50";
const secondaryButtonClass = "inline-flex items-center justify-center gap-2 rounded-md border border-border bg-background px-4 py-2 text-sm text-foreground transition-colors hover:bg-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50";
const filterLabels = {
  subscription_id: "Cuenta (ID de suscripción Azure)", service_name: "Servicio", project: "Proyecto",
  filter_tag_key: "Clave de etiqueta a filtrar", filter_tag_value: "Valor de etiqueta a filtrar"
};
const groupingLabels: Record<BillingGrouping, string> = {
  service: "Servicio", subscription: "Suscripción", resource_group: "Grupo de recursos", project: "Proyecto", tag: "Etiqueta"
};

export function OperationalCostDashboard() {
  const context = useOutletContext<SessionOutletContext>();
  return <OperationalCostInvestigation key={JSON.stringify([context.activeTenant?.id, getSessionGeneration()])} context={context} />;
}

function OperationalCostInvestigation({ context }: { context: SessionOutletContext }) {
  const { token, activeTenant } = context;
  const [applied, setApplied] = useState(defaultOperationalSelection);
  const [draft, setDraft] = useState(applied);
  const error = operationalSelectionError(draft);
  const dirty = JSON.stringify(draft) !== JSON.stringify(applied);
  // Draft keys detach obsolete observers (and abort their HTTP request), but
  // disabled queries never fetch until Apply commits this complete selection.
  const query = useCostKpis({ token, tenantId: activeTenant?.id,
    selection: operationalBillingSelection(draft), enabled: !error && !dirty });
  const billing = token && activeTenant && !error && !dirty && !query.isFetching && !query.isError ? query.data : undefined;
  const change = (field: keyof OperationalSelection, value: string) => setDraft((previous) => ({ ...previous, [field]: value }));
  const clear = () => {
    const next = { ...draft, subscription_id: "", service_name: "", project: "", filter_tag_key: "", filter_tag_value: "" };
    setDraft(next);
    setApplied(next);
  };

  return <div className="min-w-0 space-y-6 p-6">
    <header className="flex flex-wrap items-center justify-between gap-4">
      <div className="min-w-0">
        <h2 className="font-bold text-foreground">Dashboard Operativo - Coste Detallado</h2>
        <p className="text-sm text-muted-foreground">Investiga costes de Azure almacenados por cuenta, servicio, proyecto y etiqueta.</p>
      </div>
      <button type="button" className={secondaryButtonClass} disabled={!activeTenant || Boolean(error) || dirty || query.isFetching}
        onClick={() => { void query.refetch(); }}>
        <RefreshCw className="h-4 w-4" aria-hidden="true" />{query.isError ? "Reintentar" : "Actualizar costes"}
      </button>
    </header>

    <SectionCard title="Ámbito de análisis" subtitle={activeTenant ? "Cliente: " + activeTenant.name : "Selecciona un cliente para consultar costes"}>
      <form noValidate onSubmit={(event) => { event.preventDefault(); if (!error) setApplied({ ...draft }); }} className="space-y-5">
        <div className="grid min-w-0 grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <label className="min-w-0 text-sm text-subtle-foreground">Desde (incluido)
            <input type="date" min="0001-01-01" max="9999-12-31" className={inputClass} value={draft.start_date}
              onChange={(event) => change("start_date", event.target.value)} aria-describedby="operational-period-help" />
          </label>
          <label className="min-w-0 text-sm text-subtle-foreground">Hasta (excluido)
            <input type="date" min="0001-01-01" max="9999-12-31" className={inputClass} value={draft.end_date}
              onChange={(event) => change("end_date", event.target.value)} aria-describedby="operational-period-help" />
          </label>
          <label className="min-w-0 text-sm text-subtle-foreground">Agrupar por
            <select className={inputClass} value={draft.group_by} onChange={(event) => change("group_by", event.target.value)}>
              {Object.entries(groupingLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
            </select>
          </label>
          {draft.group_by === "tag" && <label className="min-w-0 text-sm text-subtle-foreground">Clave para agrupar por etiqueta
            <input className={inputClass} value={draft.tag_key} onChange={(event) => change("tag_key", event.target.value)} />
          </label>}
        </div>
        <p id="operational-period-help" className="text-sm text-muted-foreground">Fechas en UTC: se incluye el inicio y se excluye el fin. Por defecto, el último mes completo.</p>
        <fieldset className="min-w-0 border-t border-border pt-4">
          <legend className="px-1 text-sm font-semibold text-foreground">Filtros combinables</legend>
          <div className="grid min-w-0 grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
            {billingFilterKeys.map((key) => <label key={key} className="min-w-0 text-sm text-subtle-foreground">{filterLabels[key]}
              <input className={inputClass} value={draft[key]} onChange={(event) => change(key, event.target.value)}
                aria-describedby="operational-filter-help" autoComplete="off" />
            </label>)}
          </div>
          <p id="operational-filter-help" className="mt-3 text-sm text-muted-foreground">
            Todos los filtros se cumplen a la vez. Los valores distinguen mayúsculas y conservan espacios; vacíos no filtran.
            Cuenta corresponde al ID de suscripción. La clave de etiqueta se normaliza (por ejemplo, env → environment).
          </p>
        </fieldset>
        <div className="flex flex-wrap items-center gap-3">
          <button type="submit" className={buttonClass} disabled={!activeTenant || Boolean(error) || !dirty}>Aplicar filtros</button>
          <button type="button" className={secondaryButtonClass} onClick={clear}>Limpiar filtros</button>
        </div>
      </form>
    </SectionCard>

    <div aria-live="polite" aria-atomic="true">
      {!activeTenant ? <p role="status" className="text-subtle-foreground">Selecciona un cliente.</p>
        : error ? <p role="status" className="text-warning-text">{error}</p>
          : dirty ? <p role="status" className="text-subtle-foreground">Cambios sin aplicar. Aplica los filtros para consultar el nuevo ámbito.</p>
            : query.isFetching || !billing && !query.isError ? <p role="status" className="text-subtle-foreground">Cargando costes del ámbito seleccionado...</p>
              : query.isError ? <p role="alert" className="text-warning-text">{describeCostError(query.error)}</p> : null}
    </div>

    {billing && activeTenant && <>
      <section aria-label="Ámbito aplicado" className="space-y-2 border-l-2 border-highlight pl-4 text-sm">
        <h3 className="font-semibold text-foreground">Ámbito aplicado · {activeTenant.name}</h3>
        <p className="text-subtle-foreground">{billing.period.start_date} incluido → {billing.period.end_date} excluido (UTC)
          {" · "}Agrupación: {groupingLabels[billing.group_by]}{billing.tag_key ? " · " + billing.tag_key : ""}</p>
        {billing.filters ? <dl className="flex flex-wrap gap-x-6 gap-y-2 text-subtle-foreground">
          {billingFilterKeys.filter((key) => billing.filters?.[key] !== undefined).map((key) => <div key={key} className="min-w-0 max-w-full">
            <dt className="text-xs text-muted-foreground">{filterLabels[key]}</dt>
            <dd className="break-all whitespace-pre-wrap font-medium">{billing.filters?.[key]}</dd>
          </div>)}
        </dl> : <p className="text-muted-foreground">Sin filtros de dimensión: todos los registros del cliente y periodo.</p>}
      </section>

      {billing.data_status === "partial" && <p role="status" className="text-sm text-warning-text">
        Datos parciales: {billing.missing_dimension_count} registros sin dimensión en este resultado; {billing.excluded_undated_count} registros sin fecha excluidos del cliente completo.
        El recuento sin fecha no está limitado por los filtros.
      </p>}

      {billing.totals.length ? <>
        <section aria-label="Totales del ámbito" className="space-y-3">
          <h3 className="font-semibold text-foreground">Coste del ámbito por moneda</h3>
          <div className="grid min-w-0 grid-cols-1 gap-4 break-all sm:grid-cols-2 xl:grid-cols-3">
            {billing.totals.map((total) => <MetricCard key={total.currency} label={"Total " + total.currency}
              value={total.cost + " " + total.currency} detail={total.record_count + " registros · importe exacto"} />)}
          </div>
        </section>
        <SectionCard title="Desglose de costes" subtitle="Importes separados por moneda; sin conversión de divisas">
          <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
            <p className="text-sm text-muted-foreground">{billing.groups.length} grupos en el ámbito aplicado</p>
            <button type="button" className={secondaryButtonClass} onClick={() => downloadOperationalCosts(billing, activeTenant.id)}>
              <Download className="h-4 w-4" aria-hidden="true" />Exportar CSV del ámbito
            </button>
          </div>
          <div className="max-w-full overflow-x-auto">
            <table className="w-full text-left text-sm text-subtle-foreground">
              <caption className="pb-3 text-left font-semibold text-foreground">Desglose de costes del ámbito aplicado</caption>
              <thead className="border-b border-border"><tr>
                <th scope="col" className="p-2">{groupingLabels[billing.group_by]}</th>
                <th scope="col" className="p-2">Suscripción del grupo</th>
                <th scope="col" className="p-2">Moneda</th>
                <th scope="col" className="p-2 text-right">Coste</th>
                <th scope="col" className="p-2 text-right">Registros</th>
              </tr></thead>
              <tbody>{billing.groups.map((group) => <tr className="border-b border-border hover:bg-accent"
                key={JSON.stringify([group.currency, group.subscription_id, group.value])}>
                <th scope="row" className="max-w-64 break-words whitespace-pre-wrap p-2 font-normal">{group.value ?? "Sin dimensión"}</th>
                <td className="max-w-64 break-all whitespace-pre-wrap p-2">{group.subscription_id
                  ?? (billing.group_by === "subscription" || billing.group_by === "resource_group" ? "Sin suscripción" : "No aplica")}</td>
                <td className="p-2">{group.currency}</td>
                <td className="p-2 text-right tabular-nums">{group.cost}</td>
                <td className="p-2 text-right tabular-nums">{group.record_count}</td>
              </tr>)}</tbody>
            </table>
          </div>
          <p className="mt-3 text-sm text-muted-foreground">Cada grupo se redondea por consulta; su suma puede diferir del total.</p>
        </SectionCard>
      </> : <p role="status" className="text-subtle-foreground">Sin datos de costes para el ámbito aplicado. Amplía el periodo o limpia los filtros.</p>}
      <p className="text-sm text-muted-foreground">Solo costes almacenados: disponer de registros no certifica cobertura completa de Azure. El periodo en curso puede estar incompleto.</p>
    </>}
  </div>;
}
