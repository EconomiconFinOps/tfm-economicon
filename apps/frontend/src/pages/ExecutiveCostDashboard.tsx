import { AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { TrendingUp, TrendingDown } from 'lucide-react';
import { ExportButton } from "@/components/ExportButton";
import { chartTooltipStyle } from "@/components/chartTheme";
// Datos de demostracion extraidos a src/data/demo/ (JUP-095, grupo 5,
// tarea 5.2): mismo contenido que el origen, solo cambia la ubicacion.
import { monthlyData, serviceData, kpiData } from "@/data/demo/executiveCostDashboard";

// Traduce el tono de los datos demo (`kpi.color`) a la clase de texto del tema.
// Antes se interpolaba `text-${color}-400`, que Tailwind no puede detectar: solo
// generaba la clase si el literal completo aparecia en otro sitio del codigo.
// Con los literales migrados a tokens esas clases dejarian de generarse, asi que
// se declara el mapa explicito. `purple` y `orange` no tenian clase generada
// (el icono heredaba el color del texto); se conservan sin clase para que el
// resultado visual sea identico, no para fijar ese comportamiento.
const toneIconClass: Record<string, string> = {
  blue: 'text-info',
  green: 'text-success',
};

export function ExecutiveCostDashboard() {
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
          <p className="text-sm text-muted-foreground">Vista general de costes cloud multi-proveedor</p>
        </div>
        <ExportButton data={exportData} filename="coste-global-ejecutivo" />
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {kpiData.map((kpi, idx) => (
          <div key={idx} className="bg-gradient-to-br from-card to-accent rounded-lg border border-border p-5 shadow-xl hover:shadow-info-tint/10 transition-shadow">
            <div className="flex items-center justify-between mb-3">
              <kpi.icon className={`w-8 h-8 ${toneIconClass[kpi.color] ?? ''}`} />
              {kpi.trend === 'up' && <TrendingUp className="w-5 h-5 text-success" />}
              {kpi.trend === 'down' && <TrendingDown className="w-5 h-5 text-danger" />}
            </div>
            <p className="text-sm text-muted-foreground mb-1">{kpi.title}</p>
            <p className="font-bold text-foreground">{kpi.value}</p>
            <p className="text-xs text-neutral mt-1">{kpi.change}</p>
          </div>
        ))}
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
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

        {/* Service Distribution */}
        <div className="bg-gradient-to-br from-card to-accent rounded-lg border border-border p-6 shadow-xl">
          <h3 className="font-semibold text-foreground mb-4">Distribución por Servicio</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={serviceData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, value }) => `${name} ${value}%`}
                outerRadius={80}
                dataKey="value"
              >
                {/* Sin `fill` en el <Pie>: cada sector toma su color de su <Cell>, asi que el relleno del padre quedaba siempre tapado. */}
                {serviceData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={chartTooltipStyle}
              />
            </PieChart>
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
    </div>
  );
}
