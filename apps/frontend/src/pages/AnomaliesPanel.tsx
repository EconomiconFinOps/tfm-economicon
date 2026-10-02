import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { ExportButton } from "@/components/ExportButton";
import { chartTooltipStyle } from "@/components/chartTheme";
// Datos de demostracion extraidos a src/data/demo/ (JUP-095, grupo 5,
// tarea 5.2): mismo contenido que el origen, solo cambia la ubicacion.
import { anomalies, trendData, stats } from "@/data/demo/anomaliesPanel";

// Traduce el tono de los datos demo a clases del tema. Antes se interpolaba
// `bg-${color}-500/20`, `text-${color}-400`..., que Tailwind no puede detectar:
// solo generaba la clase si el literal completo aparecia en otro sitio del
// codigo. Con los literales migrados a tokens esas clases dejarian de
// generarse, asi que se declara un mapa explicito con cadenas completas.
// Los tonos ausentes (`purple`, y `orange` en el texto) no tenian clase
// generada; se conservan sin ella para que el resultado visual sea identico,
// no para fijar ese comportamiento.
const toneBoxClass: Record<string, string> = {
  red: 'bg-danger-tint/20 border-danger-tint/30',
  orange: 'bg-attention-tint/20 border-attention-tint/30',
  blue: 'bg-info-tint/20 border-info-tint/30',
  green: 'bg-success-tint/20 border-success-tint/30',
};
const toneIconClass: Record<string, string> = {
  red: 'text-danger',
  blue: 'text-info',
  green: 'text-success',
};

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
          <h2 className="font-bold text-foreground">Panel de Anomalías y Alertas</h2>
          <p className="text-sm text-muted-foreground">Detección automática mediante agentes especializados</p>
        </div>
        <ExportButton data={exportData} filename="anomalias-alertas" />
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat, idx) => (
          <div key={idx} className="bg-gradient-to-br from-card to-accent rounded-lg border border-border p-5 shadow-xl hover:shadow-info-tint/10 transition-shadow">
            <div className="flex items-center gap-3 mb-2">
              <div className={`p-2 rounded-lg ${toneBoxClass[stat.color] ?? ''} border`}>
                <stat.icon className={`w-5 h-5 ${toneIconClass[stat.color] ?? ''}`} />
              </div>
              <p className="text-sm text-muted-foreground">{stat.label}</p>
            </div>
            <p className="font-bold text-foreground">{stat.value}</p>
          </div>
        ))}
      </div>

      {/* Anomaly Detection Chart */}
      <div className="bg-gradient-to-br from-card to-accent rounded-lg border border-border p-6 shadow-xl">
        <h3 className="font-semibold text-foreground mb-4">Detección de Anomalías en Tiempo Real</h3>
        <ResponsiveContainer width="100%" height={250}>
          <LineChart data={trendData}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
            <XAxis dataKey="hora" stroke="var(--chart-axis)" />
            <YAxis stroke="var(--chart-axis)" />
            <Tooltip
              formatter={(value) => `${value}€/hora`}
              contentStyle={chartTooltipStyle}
            />
            <Line type="monotone" dataKey="normal" stroke="var(--chart-baseline)" strokeWidth={2} name="Patrón Normal" strokeDasharray="5 5" />
            <Line type="monotone" dataKey="actual" stroke="var(--chart-negative)" strokeWidth={2} name="Coste Actual" />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Anomalies Table */}
      <div className="bg-gradient-to-br from-card to-accent rounded-lg border border-border shadow-xl overflow-hidden">
        <div className="px-6 py-4 border-b border-border">
          <h3 className="font-semibold text-foreground">Anomalías Detectadas (Últimas 24h)</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-background border-b border-border">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Severidad</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Tipo</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Servicio</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Descripción</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-muted-foreground uppercase tracking-wider">Impacto</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Estado</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Agente IA</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {anomalies.map((anomaly) => (
                <tr key={anomaly.id} className="hover:bg-accent transition-colors">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                      anomaly.severidad === 'Alta' ? 'bg-danger-tint/20 text-danger-foreground border border-danger-tint/30' :
                      anomaly.severidad === 'Media' ? 'bg-warning-tint/20 text-warning-foreground border border-warning-tint/30' :
                      'bg-info-tint/20 text-info-foreground border border-info-tint/30'
                    }`}>
                      {anomaly.severidad}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-foreground">{anomaly.tipo}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-foreground">{anomaly.servicio}</td>
                  <td className="px-6 py-4 text-sm text-subtle-foreground max-w-xs">{anomaly.descripcion}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-right font-semibold text-danger">
                    +{anomaly.coste.toLocaleString()}€
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs rounded-full ${
                      anomaly.estado === 'Resuelto' ? 'bg-success-tint/20 text-success-foreground border border-success-tint/30' :
                      anomaly.estado === 'Investigando' ? 'bg-attention-tint/20 text-attention-foreground border border-attention-tint/30' :
                      'bg-neutral/20 text-subtle-foreground border border-neutral/30'
                    }`}>
                      {anomaly.estado}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-info font-medium">{anomaly.agente}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
