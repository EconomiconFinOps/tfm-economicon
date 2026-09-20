import { AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { TrendingUp, TrendingDown } from 'lucide-react';
import { ExportButton } from "@/components/ExportButton";
// Datos de demostracion extraidos a src/data/demo/ (JUP-095, grupo 5,
// tarea 5.2): mismo contenido que el origen, solo cambia la ubicacion.
import { monthlyData, serviceData, kpiData } from "@/data/demo/executiveCostDashboard";

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
          <h2 className="font-bold text-white">Dashboard Ejecutivo - Coste Global</h2>
          <p className="text-sm text-slate-400">Vista general de costes cloud multi-proveedor</p>
        </div>
        <ExportButton data={exportData} filename="coste-global-ejecutivo" />
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {kpiData.map((kpi, idx) => (
          <div key={idx} className="bg-gradient-to-br from-[#1a1f2e] to-[#232834] rounded-lg border border-[#2d3748] p-5 shadow-xl hover:shadow-blue-500/10 transition-shadow">
            <div className="flex items-center justify-between mb-3">
              <kpi.icon className={`w-8 h-8 text-${kpi.color}-400`} />
              {kpi.trend === 'up' && <TrendingUp className="w-5 h-5 text-green-400" />}
              {kpi.trend === 'down' && <TrendingDown className="w-5 h-5 text-red-400" />}
            </div>
            <p className="text-sm text-slate-400 mb-1">{kpi.title}</p>
            <p className="font-bold text-white">{kpi.value}</p>
            <p className="text-xs text-slate-500 mt-1">{kpi.change}</p>
          </div>
        ))}
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Trend Chart */}
        <div className="lg:col-span-2 bg-gradient-to-br from-[#1a1f2e] to-[#232834] rounded-lg border border-[#2d3748] p-6 shadow-xl">
          <h3 className="font-semibold text-white mb-4">Evolución de Costes Mensuales</h3>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={monthlyData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2d3748" />
              <XAxis dataKey="mes" stroke="#94a3b8" />
              <YAxis stroke="#94a3b8" />
              <Tooltip
                formatter={(value) => `${value.toLocaleString()}€`}
                contentStyle={{ backgroundColor: '#1a1f2e', border: '1px solid #2d3748', borderRadius: '8px', color: '#fff' }}
              />
              <Legend />
              <Area type="monotone" dataKey="total" stroke="#00bcf2" fill="#0078d4" fillOpacity={0.3} name="Total" />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Service Distribution */}
        <div className="bg-gradient-to-br from-[#1a1f2e] to-[#232834] rounded-lg border border-[#2d3748] p-6 shadow-xl">
          <h3 className="font-semibold text-white mb-4">Distribución por Servicio</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={serviceData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, value }) => `${name} ${value}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {serviceData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{ backgroundColor: '#1a1f2e', border: '1px solid #2d3748', borderRadius: '8px', color: '#fff' }}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Service Breakdown */}
      <div className="bg-gradient-to-br from-[#1a1f2e] to-[#232834] rounded-lg border border-[#2d3748] p-6 shadow-xl">
        <h3 className="font-semibold text-white mb-4">Desglose por Categoría</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={monthlyData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#2d3748" />
            <XAxis dataKey="mes" stroke="#94a3b8" />
            <YAxis stroke="#94a3b8" />
            <Tooltip
              formatter={(value) => `${value.toLocaleString()}€`}
              contentStyle={{ backgroundColor: '#1a1f2e', border: '1px solid #2d3748', borderRadius: '8px', color: '#fff' }}
            />
            <Legend />
            <Bar dataKey="compute" fill="#0078d4" name="Compute" />
            <Bar dataKey="storage" fill="#10b981" name="Storage" />
            <Bar dataKey="network" fill="#ff8c00" name="Network" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
