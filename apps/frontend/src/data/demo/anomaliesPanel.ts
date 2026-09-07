// DATOS DE DEMOSTRACION (sustituibles): valores estaticos portados tal cual
// del origen (Economicon, JUP-095 grupo 5) para alimentar el
// `AnomaliesPanel` mientras no exista integracion con el backend real.
// Localizable con grep "DATOS DE DEMOSTRACION" para su futura sustitucion
// por datos en vivo.
import { AlertTriangle, TrendingUp, Clock, Shield } from "lucide-react";

export const anomalies = [
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

export const trendData = [
  { hora: "00:00", normal: 120, actual: 125 },
  { hora: "03:00", normal: 115, actual: 118 },
  { hora: "06:00", normal: 140, actual: 142 },
  { hora: "09:00", normal: 180, actual: 185 },
  { hora: "12:00", normal: 190, actual: 195 },
  { hora: "15:00", normal: 185, actual: 650 },
  { hora: "18:00", normal: 175, actual: 720 },
];

export const stats = [
  { label: "Anomalías Detectadas", value: "23", icon: AlertTriangle, color: "red" },
  { label: "Impacto Total", value: "44.500€", icon: TrendingUp, color: "orange" },
  { label: "Tiempo Medio Detección", value: "4.2 min", icon: Clock, color: "blue" },
  { label: "Tasa Resolución", value: "87%", icon: Shield, color: "green" },
];
