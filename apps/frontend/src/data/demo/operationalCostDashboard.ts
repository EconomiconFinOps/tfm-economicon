// DATOS DE DEMOSTRACION (sustituibles): valores estaticos portados tal cual
// del origen (Economicon, JUP-095 grupo 5) para alimentar el
// `OperationalCostDashboard` mientras no exista integracion con el backend
// real. Localizable con grep "DATOS DE DEMOSTRACION" para su futura
// sustitucion por datos en vivo.
export const detailedData = [
  { servicio: "EC2 Instances", proyecto: "Web App", coste: 45200, uso: 92, tendencia: "+5%", proveedor: "AWS" },
  { servicio: "RDS Database", proyecto: "API Backend", coste: 28900, uso: 78, tendencia: "+12%", proveedor: "AWS" },
  { servicio: "S3 Storage", proyecto: "Data Lake", coste: 18700, uso: 65, tendencia: "-3%", proveedor: "AWS" },
  { servicio: "Azure VMs", proyecto: "Analytics", coste: 38500, uso: 88, tendencia: "+8%", proveedor: "Azure" },
  { servicio: "GCS Storage", proyecto: "Backups", coste: 15200, uso: 45, tendencia: "+2%", proveedor: "GCP" },
  { servicio: "CloudSQL", proyecto: "CRM", coste: 24800, uso: 71, tendencia: "+15%", proveedor: "GCP" },
  { servicio: "Load Balancers", proyecto: "Infrastructure", coste: 12400, uso: 95, tendencia: "estable", proveedor: "AWS" },
  { servicio: "Azure Storage", proyecto: "Media Files", coste: 19600, uso: 58, tendencia: "-5%", proveedor: "Azure" },
];

export const hourlyData = [
  { hora: "00:00", coste: 124 },
  { hora: "04:00", coste: 98 },
  { hora: "08:00", coste: 156 },
  { hora: "12:00", coste: 189 },
  { hora: "16:00", coste: 205 },
  { hora: "20:00", coste: 178 },
];

export const providerData = [
  { proveedor: "AWS", compute: 85000, storage: 45000, network: 28000 },
  { proveedor: "Azure", compute: 62000, storage: 35000, network: 22000 },
  { proveedor: "GCP", compute: 48000, storage: 28000, network: 18000 },
];
