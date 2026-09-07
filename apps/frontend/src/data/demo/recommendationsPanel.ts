// DATOS DE DEMOSTRACION (sustituibles): valores estaticos portados tal cual
// del origen (Economicon, JUP-095 grupo 5) para alimentar el
// `RecommendationsPanel` mientras no exista integracion con el backend
// real. Localizable con grep "DATOS DE DEMOSTRACION" para su futura
// sustitucion por datos en vivo.
import { Database, Server, Zap, Network } from "lucide-react";

export const recommendations = [
  {
    id: 1,
    titulo: "Migrar a Reserved Instances",
    categoria: "Compute",
    descripcion: "15 instancias EC2 t3.large con uso >80% durante 6 meses consecutivos",
    ahorro: 28400,
    implementacion: "Inmediata",
    prioridad: "Alta",
    esfuerzo: "Bajo",
    agente: "AI-ReservationAdvisor",
    icon: Server,
  },
  {
    id: 2,
    titulo: "Optimizar tier de almacenamiento",
    categoria: "Storage",
    descripcion: "Mover 2.4TB de datos con acceso <1/mes a tier Archive",
    ahorro: 18900,
    implementacion: "1 semana",
    prioridad: "Alta",
    esfuerzo: "Medio",
    agente: "AI-StorageOptimizer",
    icon: Database,
  },
  {
    id: 3,
    titulo: "Rightsizing de bases de datos",
    categoria: "Database",
    descripcion: "8 instancias RDS sobredimensionadas (uso CPU <25%)",
    ahorro: 15200,
    implementacion: "2 semanas",
    prioridad: "Media",
    esfuerzo: "Medio",
    agente: "AI-DBOptimizer",
    icon: Database,
  },
  {
    id: 4,
    titulo: "Implementar Auto-scaling",
    categoria: "Compute",
    descripcion: "Configurar escalado automático en 12 servicios con patrón predecible",
    ahorro: 22100,
    implementacion: "3 semanas",
    prioridad: "Alta",
    esfuerzo: "Alto",
    agente: "AI-ScalingAdvisor",
    icon: Zap,
  },
  {
    id: 5,
    titulo: "Eliminar recursos huérfanos",
    categoria: "Infrastructure",
    descripcion: "45 recursos no utilizados: IPs elásticas, snapshots, volúmenes",
    ahorro: 8600,
    implementacion: "Inmediata",
    prioridad: "Media",
    esfuerzo: "Bajo",
    agente: "AI-ResourceCleaner",
    icon: Server,
  },
  {
    id: 6,
    titulo: "Optimizar transferencias de datos",
    categoria: "Network",
    descripcion: "Configurar CloudFront para reducir tráfico entre regiones",
    ahorro: 12800,
    implementacion: "1 semana",
    prioridad: "Media",
    esfuerzo: "Medio",
    agente: "AI-NetworkOptimizer",
    icon: Network,
  },
];

export const savingsByCategory = [
  { categoria: "Compute", ahorro: 50500 },
  { categoria: "Storage", ahorro: 18900 },
  { categoria: "Database", ahorro: 15200 },
  { categoria: "Network", ahorro: 12800 },
  { categoria: "Infrastructure", ahorro: 8600 },
];

export const stats = [
  { label: "Ahorro Potencial Total", value: "106.000€", subtitle: "/mes", color: "green" },
  { label: "Recomendaciones Activas", value: "24", subtitle: "6 priorizadas", color: "blue" },
  { label: "Implementación Rápida", value: "37.000€", subtitle: "<1 semana", color: "purple" },
  { label: "ROI Promedio", value: "285%", subtitle: "Último trimestre", color: "orange" },
];
