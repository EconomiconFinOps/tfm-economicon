// DATOS DE DEMOSTRACION (sustituibles): fixture local; detección real pendiente
// de JUP-030/C5. Referencias: RF-091-003 y RF-095-002 en
// openspec/findings/backlog.md y docs/planning/JUP-097-frontend-data-gap-map.md.
// El impacto es una estimación ilustrativa para este periodo, no pérdida ni ahorro.
export type AnomalySeverity = "Alta" | "Media" | "Baja";
export type AnomalyStatus = "Pendiente" | "Investigando" | "Resuelto";

export interface DemoAnomaly {
  id: number;
  tipo: string;
  servicio: string;
  severidad: AnomalySeverity;
  descripcion: string;
  coste: number;
  detectado: string;
  estado: AnomalyStatus;
  agente: string;
}

export const demoPeriod = "18–19 de abril de 2026";

export const anomalies: readonly DemoAnomaly[] = [
  {
    id: 1,
    tipo: "Pico de coste",
    servicio: "EC2 - us-east-1",
    severidad: "Alta",
    descripcion: "Incremento de 340% en uso de instancias t3.xlarge",
    coste: 15800,
    detectado: "2026-04-19 03:24",
    estado: "Investigando",
    agente: "AI-CostDetector",
  },
  {
    id: 2,
    tipo: "Uso anormal",
    servicio: "RDS Database",
    severidad: "Media",
    descripcion: "Consultas costosas no optimizadas detectadas",
    coste: 8200,
    detectado: "2026-04-19 01:15",
    estado: "Resuelto",
    agente: "AI-QueryOptimizer",
  },
  {
    id: 3,
    tipo: "Recursos huérfanos",
    servicio: "EBS Volumes",
    severidad: "Baja",
    descripcion: "24 volúmenes no conectados a instancias activas",
    coste: 2400,
    detectado: "2026-04-18 22:10",
    estado: "Pendiente",
    agente: "AI-ResourceCleaner",
  },
  {
    id: 4,
    tipo: "Pico de red",
    servicio: "CloudFront",
    severidad: "Alta",
    descripcion: "Tráfico outbound 5x superior al promedio",
    coste: 12500,
    detectado: "2026-04-18 18:45",
    estado: "Investigando",
    agente: "AI-NetworkMonitor",
  },
  {
    id: 5,
    tipo: "Configuración subóptima",
    servicio: "Azure Storage",
    severidad: "Media",
    descripcion: "Tier Hot usado para datos de acceso frío",
    coste: 5600,
    detectado: "2026-04-18 14:30",
    estado: "Resuelto",
    agente: "AI-StorageOptimizer",
  },
];
