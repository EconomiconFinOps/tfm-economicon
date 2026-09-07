import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { ExportButton } from "@/components/ExportButton";
// Datos de demostracion extraidos a src/data/demo/ (JUP-095, grupo 5,
// tarea 5.2): mismo contenido que el origen, solo cambia la ubicacion.
import { savingsData, cutActions, kpiData } from "@/data/demo/executiveCutDashboard";

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
          <h2 className="font-bold text-white">Dashboard Ejecutivo - Corte Global</h2>
          <p className="text-sm text-slate-400">Seguimiento de iniciativas de optimización y ahorro</p>
        </div>
        <ExportButton data={exportData} filename="corte-global-ejecutivo" />
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {kpiData.map((kpi, idx) => (
          <div key={idx} className="bg-gradient-to-br from-[#1a1f2e] to-[#232834] rounded-lg border border-[#2d3748] p-5 shadow-xl hover:shadow-blue-500/10 transition-shadow">
            <div className="flex items-center gap-3 mb-3">
              <div className={`p-2 rounded-lg bg-${kpi.color}-500/20 border border-${kpi.color}-500/30`}>
                <kpi.icon className={`w-6 h-6 text-${kpi.color}-400`} />
              </div>
            </div>
            <p className="text-sm text-slate-400 mb-1">{kpi.title}</p>
            <p className="font-bold text-white">{kpi.value}</p>
            <p className="text-xs text-slate-500 mt-1">{kpi.subtitle}</p>
          </div>
        ))}
      </div>

      {/* Savings Progress Chart */}
      <div className="bg-gradient-to-br from-[#1a1f2e] to-[#232834] rounded-lg border border-[#2d3748] p-6 shadow-xl">
        <h3 className="font-semibold text-white mb-4">Evolución de Ahorros vs Objetivo</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={savingsData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#2d3748" />
            <XAxis dataKey="mes" stroke="#94a3b8" />
            <YAxis stroke="#94a3b8" />
            <Tooltip
              formatter={(value) => `${value.toLocaleString()}€`}
              contentStyle={{ backgroundColor: '#1a1f2e', border: '1px solid #2d3748', borderRadius: '8px', color: '#fff' }}
            />
            <Legend />
            <Bar dataKey="objetivo" fill="#64748b" name="Objetivo" />
            <Bar dataKey="alcanzado" fill="#10b981" name="Alcanzado" />
            <Bar dataKey="pendiente" fill="#ef4444" name="Pendiente" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Actions Table */}
      <div className="bg-gradient-to-br from-[#1a1f2e] to-[#232834] rounded-lg border border-[#2d3748] shadow-xl overflow-hidden">
        <div className="px-6 py-4 border-b border-[#2d3748]">
          <h3 className="font-semibold text-white">Acciones de Optimización</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-[#0f1419] border-b border-[#2d3748]">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">Acción</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-slate-400 uppercase tracking-wider">Impacto Mensual</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">Estado</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">Responsable</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">Fecha</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#2d3748]">
              {cutActions.map((action, idx) => (
                <tr key={idx} className="hover:bg-[#232834] transition-colors">
                  <td className="px-6 py-4 text-sm font-medium text-white">{action.accion}</td>
                  <td className="px-6 py-4 text-sm text-right font-semibold text-green-400">
                    {action.impacto.toLocaleString()}€
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs rounded-full ${
                      action.estado === 'Completado' ? 'bg-green-500/20 text-green-300 border border-green-500/30' :
                      action.estado === 'En progreso' ? 'bg-blue-500/20 text-blue-300 border border-blue-500/30' :
                      'bg-slate-500/20 text-slate-300 border border-slate-500/30'
                    }`}>
                      {action.estado}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-slate-300">{action.responsable}</td>
                  <td className="px-6 py-4 text-sm text-slate-300">{action.fecha}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Cumulative Savings */}
      <div className="bg-gradient-to-br from-[#1a1f2e] to-[#232834] rounded-lg border border-[#2d3748] p-6 shadow-xl">
        <h3 className="font-semibold text-white mb-4">Ahorro Acumulado</h3>
        <ResponsiveContainer width="100%" height={250}>
          <LineChart data={savingsData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#2d3748" />
            <XAxis dataKey="mes" stroke="#94a3b8" />
            <YAxis stroke="#94a3b8" />
            <Tooltip
              formatter={(value) => `${value.toLocaleString()}€`}
              contentStyle={{ backgroundColor: '#1a1f2e', border: '1px solid #2d3748', borderRadius: '8px', color: '#fff' }}
            />
            <Legend />
            <Line type="monotone" dataKey="alcanzado" stroke="#10b981" strokeWidth={2} name="Ahorro Acumulado" />
            <Line type="monotone" dataKey="objetivo" stroke="#64748b" strokeWidth={2} strokeDasharray="5 5" name="Objetivo" />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
