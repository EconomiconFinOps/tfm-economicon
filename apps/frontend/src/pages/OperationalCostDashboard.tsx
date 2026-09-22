import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { ExportButton } from "@/components/ExportButton";
// Datos de demostracion extraidos a src/data/demo/ (JUP-095, grupo 5,
// tarea 5.2): mismo contenido que el origen, solo cambia la ubicacion.
import { detailedData, hourlyData, providerData } from "@/data/demo/operationalCostDashboard";

export function OperationalCostDashboard() {
  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="font-bold text-white">Dashboard Operativo - Coste Detallado</h2>
          <p className="text-sm text-slate-400">Análisis granular por servicio, proyecto y proveedor</p>
        </div>
        <ExportButton data={detailedData} filename="coste-operativo-detallado" />
      </div>

      {/* Detailed Table */}
      <div className="bg-gradient-to-br from-[#1a1f2e] to-[#232834] rounded-lg border border-[#2d3748] shadow-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-[#0f1419] border-b border-[#2d3748]">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">Servicio</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">Proyecto</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">Proveedor</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-slate-400 uppercase tracking-wider">Coste Mensual</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-slate-400 uppercase tracking-wider">Uso (%)</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-slate-400 uppercase tracking-wider">Tendencia</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#2d3748]">
              {detailedData.map((row, idx) => (
                <tr key={idx} className="hover:bg-[#232834] transition-colors">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-white">{row.servicio}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-300">{row.proyecto}</td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs rounded-full ${
                      row.proveedor === 'AWS' ? 'bg-orange-500/20 text-orange-300 border border-orange-500/30' :
                      row.proveedor === 'Azure' ? 'bg-blue-500/20 text-blue-300 border border-blue-500/30' :
                      'bg-green-500/20 text-green-300 border border-green-500/30'
                    }`}>
                      {row.proveedor}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-white">{row.coste.toLocaleString()}€</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-right">
                    <div className="flex items-center justify-end gap-2">
                      <div className="w-16 bg-[#2d3748] rounded-full h-2">
                        <div
                          className={`h-2 rounded-full ${row.uso > 80 ? 'bg-red-500' : row.uso > 60 ? 'bg-yellow-500' : 'bg-green-500'}`}
                          style={{ width: `${row.uso}%` }}
                        />
                      </div>
                      <span className="text-slate-300 w-8">{row.uso}%</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-right">
                    <span className={`${
                      row.tendencia.includes('+') ? 'text-red-400' :
                      row.tendencia.includes('-') ? 'text-green-400' :
                      'text-slate-400'
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
        <div className="bg-gradient-to-br from-[#1a1f2e] to-[#232834] rounded-lg border border-[#2d3748] p-6 shadow-xl">
          <h3 className="font-semibold text-white mb-4">Coste por Hora (Hoy)</h3>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={hourlyData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2d3748" />
              <XAxis dataKey="hora" stroke="#94a3b8" />
              <YAxis stroke="#94a3b8" />
              <Tooltip
                formatter={(value) => `${value}€/hora`}
                contentStyle={{ backgroundColor: '#1a1f2e', border: '1px solid #2d3748', borderRadius: '8px', color: '#fff' }}
              />
              <Line type="monotone" dataKey="coste" stroke="#00bcf2" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Provider Breakdown */}
        <div className="bg-gradient-to-br from-[#1a1f2e] to-[#232834] rounded-lg border border-[#2d3748] p-6 shadow-xl">
          <h3 className="font-semibold text-white mb-4">Coste por Proveedor</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={providerData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2d3748" />
              <XAxis dataKey="proveedor" stroke="#94a3b8" />
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
    </div>
  );
}
