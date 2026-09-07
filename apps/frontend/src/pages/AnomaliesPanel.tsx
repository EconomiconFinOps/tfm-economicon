import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { ExportButton } from "@/components/ExportButton";
// Datos de demostracion extraidos a src/data/demo/ (JUP-095, grupo 5,
// tarea 5.2): mismo contenido que el origen, solo cambia la ubicacion.
import { anomalies, trendData, stats } from "@/data/demo/anomaliesPanel";

export function AnomaliesPanel() {
  const exportData = anomalies.map(a => ({
    Tipo: a.tipo,
    Servicio: a.servicio,
    Severidad: a.severidad,
    Descripción: a.descripcion,
    'Coste (€)': a.coste,
    Detectado: a.detectado,
    Estado: a.estado,
    Agente: a.agente,
  }));

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="font-bold text-white">Panel de Anomalías y Alertas</h2>
          <p className="text-sm text-slate-400">Detección automática mediante agentes especializados</p>
        </div>
        <ExportButton data={exportData} filename="anomalias-alertas" />
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat, idx) => (
          <div key={idx} className="bg-gradient-to-br from-[#1a1f2e] to-[#232834] rounded-lg border border-[#2d3748] p-5 shadow-xl hover:shadow-blue-500/10 transition-shadow">
            <div className="flex items-center gap-3 mb-2">
              <div className={`p-2 rounded-lg bg-${stat.color}-500/20 border border-${stat.color}-500/30`}>
                <stat.icon className={`w-5 h-5 text-${stat.color}-400`} />
              </div>
              <p className="text-sm text-slate-400">{stat.label}</p>
            </div>
            <p className="font-bold text-white">{stat.value}</p>
          </div>
        ))}
      </div>

      {/* Anomaly Detection Chart */}
      <div className="bg-gradient-to-br from-[#1a1f2e] to-[#232834] rounded-lg border border-[#2d3748] p-6 shadow-xl">
        <h3 className="font-semibold text-white mb-4">Detección de Anomalías en Tiempo Real</h3>
        <ResponsiveContainer width="100%" height={250}>
          <LineChart data={trendData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#2d3748" />
            <XAxis dataKey="hora" stroke="#94a3b8" />
            <YAxis stroke="#94a3b8" />
            <Tooltip
              formatter={(value) => `${value}€/hora`}
              contentStyle={{ backgroundColor: '#1a1f2e', border: '1px solid #2d3748', borderRadius: '8px', color: '#fff' }}
            />
            <Line type="monotone" dataKey="normal" stroke="#64748b" strokeWidth={2} name="Patrón Normal" strokeDasharray="5 5" />
            <Line type="monotone" dataKey="actual" stroke="#ef4444" strokeWidth={2} name="Coste Actual" />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Anomalies Table */}
      <div className="bg-gradient-to-br from-[#1a1f2e] to-[#232834] rounded-lg border border-[#2d3748] shadow-xl overflow-hidden">
        <div className="px-6 py-4 border-b border-[#2d3748]">
          <h3 className="font-semibold text-white">Anomalías Detectadas (Últimas 24h)</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-[#0f1419] border-b border-[#2d3748]">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">Severidad</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">Tipo</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">Servicio</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">Descripción</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-slate-400 uppercase tracking-wider">Impacto</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">Estado</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">Agente IA</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#2d3748]">
              {anomalies.map((anomaly) => (
                <tr key={anomaly.id} className="hover:bg-[#232834] transition-colors">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                      anomaly.severidad === 'Alta' ? 'bg-red-500/20 text-red-300 border border-red-500/30' :
                      anomaly.severidad === 'Media' ? 'bg-yellow-500/20 text-yellow-300 border border-yellow-500/30' :
                      'bg-blue-500/20 text-blue-300 border border-blue-500/30'
                    }`}>
                      {anomaly.severidad}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-white">{anomaly.tipo}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-white">{anomaly.servicio}</td>
                  <td className="px-6 py-4 text-sm text-slate-300 max-w-xs">{anomaly.descripcion}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-right font-semibold text-red-400">
                    +{anomaly.coste.toLocaleString()}€
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs rounded-full ${
                      anomaly.estado === 'Resuelto' ? 'bg-green-500/20 text-green-300 border border-green-500/30' :
                      anomaly.estado === 'Investigando' ? 'bg-orange-500/20 text-orange-300 border border-orange-500/30' :
                      'bg-slate-500/20 text-slate-300 border border-slate-500/30'
                    }`}>
                      {anomaly.estado}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-blue-400 font-medium">{anomaly.agente}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
