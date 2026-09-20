// DATOS DE DEMOSTRACION (sustituibles): valores estaticos portados tal cual
// del origen (Economicon, JUP-095 grupo 5) para alimentar el
// `ExecutiveCutDashboard` mientras no exista integracion con el backend
// real. Localizable con grep "DATOS DE DEMOSTRACION" para su futura
// sustitucion por datos en vivo.
import { Scissors, Target, TrendingDown, CheckCircle } from "lucide-react";

export const savingsData = [
  { mes: "Ene", objetivo: 50000, alcanzado: 42000, pendiente: 8000 },
  { mes: "Feb", objetivo: 50000, alcanzado: 48500, pendiente: 1500 },
  { mes: "Mar", objetivo: 50000, alcanzado: 51200, pendiente: 0 },
  { mes: "Abr", objetivo: 55000, alcanzado: 52800, pendiente: 2200 },
  { mes: "May", objetivo: 55000, alcanzado: 54100, pendiente: 900 },
  { mes: "Jun", objetivo: 55000, alcanzado: 47200, pendiente: 7800 },
];

export const cutActions = [
  { accion: "Rightsizing EC2", impacto: 18500, estado: "Completado", responsable: "DevOps Team", fecha: "2026-04-15" },
  { accion: "Eliminar snapshots antiguos", impacto: 12400, estado: "Completado", responsable: "Storage Team", fecha: "2026-04-12" },
  { accion: "Reserved Instances compra", impacto: 8900, estado: "En progreso", responsable: "FinOps Lead", fecha: "2026-04-18" },
  { accion: "Optimizar consultas DB", impacto: 15200, estado: "Planificado", responsable: "Backend Team", fecha: "2026-04-22" },
  { accion: "Reducir retención logs", impacto: 6800, estado: "Completado", responsable: "Platform Team", fecha: "2026-04-10" },
  { accion: "Auto-scaling ajuste", impacto: 9400, estado: "En progreso", responsable: "DevOps Team", fecha: "2026-04-19" },
];

export const kpiData = [
  { title: "Ahorro Total", value: "295.200€", subtitle: "Últimos 6 meses", icon: TrendingDown, color: "green" },
  { title: "Objetivo Mensual", value: "55.000€", subtitle: "Junio 2026", icon: Target, color: "blue" },
  { title: "Alcanzado (Jun)", value: "47.200€", subtitle: "85.8% del objetivo", icon: CheckCircle, color: "purple" },
  { title: "Acciones Activas", value: "12", subtitle: "6 completadas", icon: Scissors, color: "orange" },
];
