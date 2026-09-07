// DATOS DE DEMOSTRACION (sustituibles): valores estaticos portados tal cual
// del origen (Economicon, JUP-095 grupo 5) para alimentar el
// `ExecutiveCostDashboard` mientras no exista integracion con el backend
// real. Localizable con grep "DATOS DE DEMOSTRACION" para su futura
// sustitucion por datos en vivo.
import { TrendingDown, DollarSign, Cloud, Server } from "lucide-react";

export const monthlyData = [
  { mes: "Ene", total: 245000, compute: 120000, storage: 65000, network: 60000 },
  { mes: "Feb", total: 268000, compute: 135000, storage: 68000, network: 65000 },
  { mes: "Mar", total: 292000, compute: 148000, storage: 72000, network: 72000 },
  { mes: "Abr", total: 315000, compute: 165000, storage: 75000, network: 75000 },
  { mes: "May", total: 285000, compute: 142000, storage: 71000, network: 72000 },
  { mes: "Jun", total: 298000, compute: 155000, storage: 73000, network: 70000 },
];

export const serviceData = [
  { name: "Compute", value: 42, color: "#3b82f6" },
  { name: "Storage", value: 25, color: "#10b981" },
  { name: "Network", value: 18, color: "#f59e0b" },
  { name: "Database", value: 15, color: "#8b5cf6" },
];

export const kpiData = [
  { title: "Coste Total Mensual", value: "298.000€", change: "+4.6%", trend: "up", icon: DollarSign, color: "blue" },
  { title: "Coste por Servicio", value: "42%", change: "Compute", trend: "stable", icon: Cloud, color: "green" },
  { title: "Ahorro Potencial", value: "47.200€", change: "15.8%", trend: "down", icon: TrendingDown, color: "purple" },
  { title: "Recursos Activos", value: "1.248", change: "+12", trend: "up", icon: Server, color: "orange" },
];
