import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { ExportButton } from "@/components/ExportButton";
import { chartLegendFormatter, chartTooltipStyle } from "@/components/chartTheme";
// Datos de demostracion extraidos a src/data/demo/ (JUP-095, grupo 5,
// tarea 5.2): mismo contenido que el origen, solo cambia la ubicacion.
import { detailedData, hourlyData, providerData } from "@/data/demo/operationalCostDashboard";

export function OperationalCostDashboard() {
  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="font-bold text-foreground">Dashboard Operativo - Coste Detallado</h2>
          <p className="text-sm text-muted-foreground">Análisis granular por servicio, proyecto y proveedor</p>
        </div>
        <ExportButton data={detailedData} filename="coste-operativo-detallado" />
      </div>

      {/* Detailed Table */}
      <div className="bg-gradient-to-br from-card to-accent rounded-lg border border-border shadow-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-background border-b border-border">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Servicio</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Proyecto</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Proveedor</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-muted-foreground uppercase tracking-wider">Coste Mensual</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-muted-foreground uppercase tracking-wider">Uso (%)</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-muted-foreground uppercase tracking-wider">Tendencia</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {detailedData.map((row, idx) => (
                <tr key={idx} className="hover:bg-accent transition-colors">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-foreground">{row.servicio}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-subtle-foreground">{row.proyecto}</td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs rounded-full ${
                      row.proveedor === 'AWS' ? 'bg-neutral/20 text-muted-foreground border border-neutral/30' :
                      row.proveedor === 'Azure' ? 'bg-info-tint/20 text-info-foreground border border-info-tint/30' :
                      'bg-success-tint/20 text-success-foreground border border-success-tint/30'
                    }`}>
                      {row.proveedor}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-foreground">{row.coste.toLocaleString()}€</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-right">
                    <div className="flex items-center justify-end gap-2">
                      <div className="w-16 bg-muted rounded-full h-2">
                        <div
                          className={`h-2 rounded-full ${row.uso > 80 ? 'bg-danger-tint' : row.uso > 60 ? 'bg-warning-tint' : 'bg-success-tint'}`}
                          style={{ width: `${row.uso}%` }}
                        />
                      </div>
                      <span className="text-subtle-foreground w-8">{row.uso}%</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-right">
                    <span className={`${
                      row.tendencia.includes('+') ? 'text-danger' :
                      row.tendencia.includes('-') ? 'text-success' :
                      'text-muted-foreground'
                    }`}>
                      {row.tendencia}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Hourly Cost */}
        <div className="bg-gradient-to-br from-card to-accent rounded-lg border border-border p-6 shadow-xl">
          <h3 className="font-semibold text-foreground mb-4">Coste por Hora (Hoy)</h3>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={hourlyData}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis dataKey="hora" stroke="var(--chart-axis)" />
              <YAxis stroke="var(--chart-axis)" />
              <Tooltip
                formatter={(value) => `${value}€/hora`}
                contentStyle={chartTooltipStyle}
              />
              <Line type="monotone" dataKey="coste" stroke="var(--chart-1)" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Provider Breakdown */}
        <div className="bg-gradient-to-br from-card to-accent rounded-lg border border-border p-6 shadow-xl">
          <h3 className="font-semibold text-foreground mb-4">Coste por Proveedor</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={providerData}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis dataKey="proveedor" stroke="var(--chart-axis)" />
              <YAxis stroke="var(--chart-axis)" />
              <Tooltip
                formatter={(value) => `${value.toLocaleString()}€`}
                contentStyle={chartTooltipStyle}
              />
              <Legend formatter={chartLegendFormatter} />
              <Bar dataKey="compute" fill="var(--chart-1)" name="Compute" />
              <Bar dataKey="storage" fill="var(--chart-2)" name="Storage" />
              <Bar dataKey="network" fill="var(--chart-5)" name="Network" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
