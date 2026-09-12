import { createBrowserRouter } from "react-router";
import { SessionGate } from "./layouts/SessionGate";
import { Layout } from "./layouts/Layout";
import { ExecutiveCostDashboard } from "./pages/ExecutiveCostDashboard";
import { OperationalCostDashboard } from "./pages/OperationalCostDashboard";
import { ExecutiveCutDashboard } from "./pages/ExecutiveCutDashboard";
import { AnomaliesPanel } from "./pages/AnomaliesPanel";
import { RecommendationsPanel } from "./pages/RecommendationsPanel";
import { LoginPage } from "./pages/LoginPage";
import { IngestPage } from "./pages/IngestPage";
import { ConversationsPage } from "./pages/ConversationsPage";
import { DashboardPage } from "./pages/DashboardPage";

// Mapa de rutas completo (JUP-095, grupo 6, sub-ronda d -- ver Addendum de
// design.md, decision 3). `/login` vive fuera de `SessionGate` (no requiere
// sesion, es donde se crea). `SessionGate` resuelve sesion y bootstrap de
// tenants (redirigiendo a /login si no hay sesion) antes de exponerlos via
// Outlet context hacia `Layout` y, desde ahi, hacia las 8 pantallas
// portadas. `/overview-legacy` es la ruta puente que conserva el unico
// dashboard con datos reales hasta que JUP-096 conecte el nuevo Overview
// (decision 6 de design.md).
export const router = createBrowserRouter([
  { path: "/login", Component: LoginPage },
  {
    path: "/",
    Component: SessionGate,
    children: [
      {
        Component: Layout,
        children: [
          { index: true, Component: ExecutiveCostDashboard },
          { path: "operational", Component: OperationalCostDashboard },
          { path: "cuts", Component: ExecutiveCutDashboard },
          { path: "anomalies", Component: AnomaliesPanel },
          { path: "recommendations", Component: RecommendationsPanel },
          { path: "ingest", Component: IngestPage },
          { path: "assistant", Component: ConversationsPage },
          { path: "overview-legacy", Component: DashboardPage },
        ],
      },
    ],
  },
]);
