import { Lightbulb, TrendingDown } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { ExportButton } from "@/components/ExportButton";
// Datos de demostracion extraidos a src/data/demo/ (JUP-095, grupo 5,
// tarea 5.2): mismo contenido que el origen, solo cambia la ubicacion.
import { recommendations, savingsByCategory, stats } from "@/data/demo/recommendationsPanel";

export function RecommendationsPanel() {
  const exportData = recommendations.map(r => ({
    Título: r.titulo,
    Categoría: r.categoria,
    Descripción: r.descripcion,
    'Ahorro Mensual (€)': r.ahorro,
    Implementación: r.implementacion,
    Prioridad: r.prioridad,
    Esfuerzo: r.esfuerzo,
    'Agente IA': r.agente,
  }));

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="font-bold text-white">Panel de Recomendaciones</h2>
          <p className="text-sm text-slate-400">Optimizaciones generadas por agentes especializados de IA</p>
        </div>
        <ExportButton data={exportData} filename="recomendaciones-finops" />
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat, idx) => (
          <div key={idx} className="bg-gradient-to-br from-[#1a1f2e] to-[#232834] rounded-lg border border-[#2d3748] p-5 shadow-xl hover:shadow-blue-500/10 transition-shadow">
            <p className="text-sm text-slate-400 mb-1">{stat.label}</p>
            <div className="flex items-baseline gap-1">
              <p className={`font-bold text-${stat.color}-400`}>{stat.value}</p>
              <span className="text-xs text-slate-500">{stat.subtitle}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Savings by Category Chart */}
      <div className="bg-gradient-to-br from-[#1a1f2e] to-[#232834] rounded-lg border border-[#2d3748] p-6 shadow-xl">
        <h3 className="font-semibold text-white mb-4">Ahorro Potencial por Categoría</h3>
        <ResponsiveContainer width="100%" height={250}>
          <BarChart data={savingsByCategory} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" stroke="#2d3748" />
            <XAxis type="number" stroke="#94a3b8" />
            <YAxis dataKey="categoria" type="category" width={100} stroke="#94a3b8" />
            <Tooltip
              formatter={(value) => `${value.toLocaleString()}€/mes`}
              contentStyle={{ backgroundColor: '#1a1f2e', border: '1px solid #2d3748', borderRadius: '8px', color: '#fff' }}
            />
            <Bar dataKey="ahorro" fill="#10b981" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Recommendations List */}
      <div className="space-y-4">
        {recommendations.map((rec) => (
          <div key={rec.id} className="bg-gradient-to-br from-[#1a1f2e] to-[#232834] rounded-lg border border-[#2d3748] shadow-xl overflow-hidden hover:border-[#00bcf2] transition-all">
            <div className="p-6">
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-start gap-4">
                  <div className={`p-3 rounded-lg ${
                    rec.prioridad === 'Alta' ? 'bg-red-500/20 border border-red-500/30' : 'bg-blue-500/20 border border-blue-500/30'
                  }`}>
                    <rec.icon className={`w-6 h-6 ${
                      rec.prioridad === 'Alta' ? 'text-red-400' : 'text-blue-400'
                    }`} />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="font-semibold text-white">{rec.titulo}</h3>
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        rec.prioridad === 'Alta' ? 'bg-red-500/20 text-red-300 border border-red-500/30' :
                        'bg-blue-500/20 text-blue-300 border border-blue-500/30'
                      }`}>
                        {rec.prioridad}
                      </span>
                      <span className="inline-flex px-2 py-1 text-xs rounded-full bg-slate-500/20 text-slate-300 border border-slate-500/30">
                        {rec.categoria}
                      </span>
                    </div>
                    <p className="text-sm text-slate-300 mb-3">{rec.descripcion}</p>
                    <div className="flex items-center gap-6 text-sm">
                      <div className="flex items-center gap-2">
                        <TrendingDown className="w-4 h-4 text-green-400" />
                        <span className="font-semibold text-green-400">{rec.ahorro.toLocaleString()}€/mes</span>
                      </div>
                      <div className="text-slate-400">
                        <span className="font-medium">Esfuerzo:</span> {rec.esfuerzo}
                      </div>
                      <div className="text-slate-400">
                        <span className="font-medium">Tiempo:</span> {rec.implementacion}
                      </div>
                      <div className="text-blue-400 font-medium">
                        {rec.agente}
                      </div>
                    </div>
                  </div>
                </div>
                <button className="px-4 py-2 bg-gradient-to-r from-[#0078d4] to-[#00bcf2] text-white rounded-lg hover:shadow-lg hover:shadow-blue-500/30 transition-all text-sm font-medium">
                  Implementar
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* AI Agents Summary */}
      <div className="bg-gradient-to-r from-[#0078d4]/20 to-[#8b5cf6]/20 rounded-lg border border-[#0078d4]/30 p-6">
        <div className="flex items-start gap-4">
          <div className="p-3 rounded-lg bg-gradient-to-br from-[#0078d4] to-[#00bcf2] shadow-lg shadow-blue-500/30">
            <Lightbulb className="w-6 h-6 text-white" />
          </div>
          <div>
            <h3 className="font-semibold text-white mb-2">Agentes IA Especializados Activos</h3>
            <p className="text-sm text-slate-300 mb-3">
              6 agentes especializados analizan continuamente tu infraestructura cloud para identificar oportunidades de optimización.
            </p>
            <div className="flex flex-wrap gap-2">
              {['AI-ReservationAdvisor', 'AI-StorageOptimizer', 'AI-DBOptimizer', 'AI-ScalingAdvisor', 'AI-ResourceCleaner', 'AI-NetworkOptimizer'].map((agent) => (
                <span key={agent} className="inline-flex px-3 py-1 text-xs font-medium rounded-full bg-[#1a1f2e] text-blue-400 border border-[#0078d4]/30">
                  {agent}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
