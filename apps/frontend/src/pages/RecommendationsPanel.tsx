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
// Los tonos se resuelven en la paleta clara de marca (JUP-112).
const toneTextClass: Record<string, string> = {
  green: 'text-success',
  blue: 'text-info',
  purple: 'text-brand',
  orange: 'text-attention-foreground',
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
    <div className="page-content space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="page-title">Panel de Recomendaciones</h1>
          <p className="text-sm text-muted-foreground">Optimizaciones generadas por agentes especializados de IA</p>
        </div>
        <ExportButton data={exportData} filename="recomendaciones-finops" />
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat, idx) => (
          <div key={idx} className="bg-card rounded-lg border border-border p-5 shadow-sm hover:shadow-md transition-shadow">
            <p className="text-sm text-muted-foreground mb-1">{stat.label}</p>
            <div className="flex items-baseline gap-1">
              <p className={`font-heading text-3xl font-bold tabular-nums ${toneTextClass[stat.color] ?? ''}`}>{stat.value}</p>
              <span className="text-xs text-neutral">{stat.subtitle}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Savings by Category Chart */}
      <div className="min-w-0 bg-card rounded-lg border border-border p-4 sm:p-6 shadow-sm">
        <h2 className="font-semibold text-brand mb-4">Ahorro Potencial por Categoría</h2>
        <ResponsiveContainer width="100%" height={250}>
          <BarChart data={savingsByCategory} layout="vertical" margin={{ top: 8, right: 32, left: 0, bottom: 8 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
            <XAxis type="number" stroke="var(--chart-axis)" tick={{ fontSize: 12 }} minTickGap={24} />
            <YAxis dataKey="categoria" type="category" width={120} stroke="var(--chart-axis)" tick={{ fontSize: 14 }} />
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
          <div key={rec.id} className="bg-card rounded-lg border border-border shadow-sm overflow-hidden hover:border-highlight transition-all">
            <div className="p-4 sm:p-6">
              <div className="flex flex-wrap items-start justify-between gap-4 mb-4">
                <div className="flex min-w-0 flex-col items-start gap-3 sm:flex-row sm:gap-4">
                  <div className={`p-3 rounded-lg ${
                    rec.prioridad === 'Alta' ? 'bg-danger-tint/20 border border-danger-tint/30' : 'bg-info-tint/20 border border-info-tint/30'
                  }`}>
                    <rec.icon className={`w-6 h-6 ${
                      rec.prioridad === 'Alta' ? 'text-danger' : 'text-info'
                    }`} />
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-3 mb-2">
                      <h2 className="text-xl font-semibold text-brand sm:text-2xl">{rec.titulo}</h2>
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
                      <div className="flex items-center gap-2">
                        <TrendingDown className="w-4 h-4 text-success" />
                        <span className="rounded bg-insight/30 px-2 py-1 font-semibold text-insight-foreground">{rec.ahorro.toLocaleString()}€/mes</span>
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
                <button className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-all text-sm font-medium">
                  Implementar
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* AI Agents Summary */}
      <div className="bg-accent/50 rounded-lg border border-border p-6">
        <div className="flex min-w-0 items-start gap-4">
          <div className="p-3 rounded-lg bg-insight text-insight-foreground shrink-0">
            <Lightbulb className="w-6 h-6" />
          </div>
          <div>
            <h2 className="font-semibold text-brand mb-2">Agentes IA Especializados Activos</h2>
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
