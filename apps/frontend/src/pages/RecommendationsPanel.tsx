import { Lightbulb, TrendingDown } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { ExportButton } from "@/components/ExportButton";
import { chartTooltipStyle } from "@/components/chartTheme";
// Datos de demostracion extraidos a src/data/demo/ (JUP-095, grupo 5,
// tarea 5.2): mismo contenido que el origen, solo cambia la ubicacion.
import { recommendations, savingsByCategory, stats } from "@/data/demo/recommendationsPanel";

// Traduce el tono de los datos demo a clases del tema. Antes se interpolaba
// `bg-${color}-500/20`, `text-${color}-400`..., que Tailwind no puede detectar:
// solo generaba la clase si el literal completo aparecia en otro sitio del
// codigo. Con los literales migrados a tokens esas clases dejarian de
// generarse, asi que se declara un mapa explicito con cadenas completas.
// Los tonos ausentes (`purple`, y `orange` en el texto) no tenian clase
// generada; se conservan sin ella para que el resultado visual sea identico,
// no para fijar ese comportamiento.
const toneTextClass: Record<string, string> = {
  green: 'text-success',
  blue: 'text-info',
};

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
          <h2 className="font-bold text-foreground">Panel de Recomendaciones</h2>
          <p className="text-sm text-muted-foreground">Optimizaciones generadas por agentes especializados de IA</p>
        </div>
        <ExportButton data={exportData} filename="recomendaciones-finops" />
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat, idx) => (
          <div key={idx} className="bg-gradient-to-br from-card to-accent rounded-lg border border-border p-5 shadow-xl hover:shadow-info-tint/10 transition-shadow">
            <p className="text-sm text-muted-foreground mb-1">{stat.label}</p>
            <div className="flex items-baseline gap-1">
              <p className={`font-bold ${toneTextClass[stat.color] ?? ''}`}>{stat.value}</p>
              <span className="text-xs text-neutral">{stat.subtitle}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Savings by Category Chart */}
      <div className="bg-gradient-to-br from-card to-accent rounded-lg border border-border p-6 shadow-xl">
        <h3 className="font-semibold text-foreground mb-4">Ahorro Potencial por Categoría</h3>
        <ResponsiveContainer width="100%" height={250}>
          <BarChart data={savingsByCategory} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
            <XAxis type="number" stroke="var(--chart-axis)" />
            <YAxis dataKey="categoria" type="category" width={120} stroke="var(--chart-axis)" />
            <Tooltip
              formatter={(value) => `${value.toLocaleString()}€/mes`}
              contentStyle={chartTooltipStyle}
            />
            <Bar dataKey="ahorro" fill="var(--chart-2)" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Recommendations List */}
      <div className="space-y-4">
        {recommendations.map((rec) => (
          <div key={rec.id} className="bg-gradient-to-br from-card to-accent rounded-lg border border-border shadow-xl overflow-hidden hover:border-highlight transition-all">
            <div className="p-4 sm:p-6">
              <div className="mb-4 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                <div className="flex min-w-0 items-start gap-4">
                  <div className={`p-3 rounded-lg ${
                    rec.prioridad === 'Alta' ? 'bg-danger-tint/20 border border-danger-tint/30' : 'bg-info-tint/20 border border-info-tint/30'
                  }`}>
                    <rec.icon className={`w-6 h-6 ${
                      rec.prioridad === 'Alta' ? 'text-danger' : 'text-info'
                    }`} />
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="mb-2 flex flex-wrap items-center gap-x-3 gap-y-1">
                      <h3 className="font-semibold text-foreground">{rec.titulo}</h3>
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        rec.prioridad === 'Alta' ? 'bg-danger-tint/20 text-danger-foreground border border-danger-tint/30' :
                        'bg-info-tint/20 text-info-foreground border border-info-tint/30'
                      }`}>
                        {rec.prioridad}
                      </span>
                      <span className="inline-flex px-2 py-1 text-xs rounded-full bg-neutral/20 text-subtle-foreground border border-neutral/30">
                        {rec.categoria}
                      </span>
                    </div>
                    <p className="text-sm text-subtle-foreground mb-3">{rec.descripcion}</p>
                    <div className="flex flex-wrap items-center gap-x-6 gap-y-2 text-sm">
                      <div className="flex items-center gap-2 rounded-full bg-saving px-3 py-1 text-saving-foreground">
                        <TrendingDown className="w-4 h-4" aria-hidden="true" />
                        <span className="font-semibold">{rec.ahorro.toLocaleString()}€/mes</span>
                      </div>
                      <div className="text-muted-foreground">
                        <span className="font-medium">Esfuerzo:</span> {rec.esfuerzo}
                      </div>
                      <div className="text-muted-foreground">
                        <span className="font-medium">Tiempo:</span> {rec.implementacion}
                      </div>
                      <div className="text-info font-medium">
                        {rec.agente}
                      </div>
                    </div>
                  </div>
                </div>
                <button className="self-start px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-all text-sm font-medium">
                  Implementar
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* AI Agents Summary */}
      <div className="bg-accent rounded-lg border border-border p-6">
        <div className="flex items-start gap-4">
          <div className="p-3 rounded-lg bg-saving text-saving-foreground">
            <Lightbulb className="w-6 h-6" aria-hidden="true" />
          </div>
          <div>
            <h3 className="font-semibold text-foreground mb-2">Agentes IA Especializados Activos</h3>
            <p className="text-sm text-subtle-foreground mb-3">
              6 agentes especializados analizan continuamente tu infraestructura cloud para identificar oportunidades de optimización.
            </p>
            <div className="flex flex-wrap gap-2">
              {['AI-ReservationAdvisor', 'AI-StorageOptimizer', 'AI-DBOptimizer', 'AI-ScalingAdvisor', 'AI-ResourceCleaner', 'AI-NetworkOptimizer'].map((agent) => (
                <span key={agent} className="inline-flex px-3 py-1 text-xs font-medium rounded-full bg-card text-info border border-border">
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
