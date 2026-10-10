import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { ExportButton } from "@/components/ExportButton";
import { chartLegendFormatter, chartTooltipStyle } from "@/components/chartTheme";
// Datos de demostracion extraidos a src/data/demo/ (JUP-095, grupo 5,
// tarea 5.2): mismo contenido que el origen, solo cambia la ubicacion.
import { savingsData, cutActions, kpiData } from "@/data/demo/executiveCutDashboard";

// Traduce el tono de los datos demo a clases del tema. Antes se interpolaba
// `bg-${color}-500/20`, `text-${color}-400`..., que Tailwind no puede detectar:
// solo generaba la clase si el literal completo aparecia en otro sitio del
// codigo. Con los literales migrados a tokens esas clases dejarian de
// generarse, asi que se declara un mapa explicito con cadenas completas.
// Los tonos ausentes (`purple`, y `orange` en el texto) no tenian clase
// generada; se conservan sin ella para que el resultado visual sea identico,
// no para fijar ese comportamiento.
const toneBoxClass: Record<string, string> = {
  green: 'bg-success-tint/20 border-success-tint/30',
  blue: 'bg-info-tint/20 border-info-tint/30',
  orange: 'bg-accent border-border',
};
const toneIconClass: Record<string, string> = {
  green: 'text-success',
  blue: 'text-info',
};

export function ExecutiveCutDashboard() {
  const exportData = cutActions.map(a => ({
    Acción: a.accion,
    'Impacto (€)': a.impacto,
    Estado: a.estado,
    Responsable: a.responsable,
    Fecha: a.fecha,
  }));

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="font-bold text-foreground">Dashboard Ejecutivo - Corte Global</h2>
          <p className="text-sm text-muted-foreground">Seguimiento de iniciativas de optimización y ahorro</p>
        </div>
        <ExportButton data={exportData} filename="corte-global-ejecutivo" />
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {kpiData.map((kpi, idx) => (
          <div key={idx} className="bg-gradient-to-br from-card to-accent rounded-lg border border-border p-5 shadow-xl hover:shadow-info-tint/10 transition-shadow">
            <div className="flex items-center gap-3 mb-3">
              <div className={`p-2 rounded-lg ${toneBoxClass[kpi.color] ?? ''} border`}>
                <kpi.icon className={`w-6 h-6 ${toneIconClass[kpi.color] ?? ''}`} />
              </div>
            </div>
            <p className="text-sm text-muted-foreground mb-1">{kpi.title}</p>
            <p className="font-bold text-foreground">{kpi.value}</p>
            <p className="text-xs text-neutral mt-1">{kpi.subtitle}</p>
          </div>
        ))}
      </div>

      {/* Savings Progress Chart */}
      <div className="bg-gradient-to-br from-card to-accent rounded-lg border border-border p-6 shadow-xl">
        <h3 className="font-semibold text-foreground mb-4">Evolución de Ahorros vs Objetivo</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={savingsData}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
            <XAxis dataKey="mes" stroke="var(--chart-axis)" />
            <YAxis stroke="var(--chart-axis)" />
            <Tooltip
              formatter={(value) => `${value.toLocaleString()}€`}
              contentStyle={chartTooltipStyle}
            />
            <Legend formatter={chartLegendFormatter} />
            <Bar dataKey="objetivo" fill="var(--chart-baseline)" name="Objetivo" />
            <Bar dataKey="alcanzado" fill="var(--chart-2)" name="Alcanzado" />
            <Bar dataKey="pendiente" fill="var(--chart-negative)" name="Pendiente" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Actions Table */}
      <div className="bg-gradient-to-br from-card to-accent rounded-lg border border-border shadow-xl overflow-hidden">
        <div className="px-6 py-4 border-b border-border">
          <h3 className="font-semibold text-foreground">Acciones de Optimización</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-background border-b border-border">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Acción</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-muted-foreground uppercase tracking-wider">Impacto Mensual</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Estado</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Responsable</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Fecha</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {cutActions.map((action, idx) => (
                <tr key={idx} className="hover:bg-accent transition-colors">
                  <td className="px-6 py-4 text-sm font-medium text-foreground">{action.accion}</td>
                  <td className="px-6 py-4 text-sm text-right font-semibold text-success">
                    {action.impacto.toLocaleString()}€
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs rounded-full ${
                      action.estado === 'Completado' ? 'bg-success-tint/20 text-success-foreground border border-success-tint/30' :
                      action.estado === 'En progreso' ? 'bg-info-tint/20 text-info-foreground border border-info-tint/30' :
                      'bg-neutral/20 text-subtle-foreground border border-neutral/30'
                    }`}>
                      {action.estado}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-subtle-foreground">{action.responsable}</td>
                  <td className="px-6 py-4 text-sm text-subtle-foreground">{action.fecha}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Cumulative Savings */}
      <div className="bg-gradient-to-br from-card to-accent rounded-lg border border-border p-6 shadow-xl">
        <h3 className="font-semibold text-foreground mb-4">Ahorro Acumulado</h3>
        <ResponsiveContainer width="100%" height={250}>
          <LineChart data={savingsData}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
            <XAxis dataKey="mes" stroke="var(--chart-axis)" />
            <YAxis stroke="var(--chart-axis)" />
            <Tooltip
              formatter={(value) => `${value.toLocaleString()}€`}
              contentStyle={chartTooltipStyle}
            />
            <Legend formatter={chartLegendFormatter} />
            <Line type="monotone" dataKey="alcanzado" stroke="var(--chart-2)" strokeWidth={2} name="Ahorro Acumulado" />
            <Line type="monotone" dataKey="objetivo" stroke="var(--chart-baseline)" strokeWidth={2} strokeDasharray="5 5" name="Objetivo" />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
