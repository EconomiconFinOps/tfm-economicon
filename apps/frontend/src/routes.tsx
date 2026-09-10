import { createBrowserRouter } from "react-router";
import { SessionGate } from "./layouts/SessionGate";
import { Layout } from "./layouts/Layout";
import { ExecutiveCostDashboard } from "./pages/ExecutiveCostDashboard";
import { OperationalCostDashboard } from "./pages/OperationalCostDashboard";
import { ExecutiveCutDashboard } from "./pages/ExecutiveCutDashboard";
import { AnomaliesPanel } from "./pages/AnomaliesPanel";
import { RecommendationsPanel } from "./pages/RecommendationsPanel";

// `SessionGate` pasa a ser el padre de `Layout`: resuelve sesion y bootstrap
// de tenants (redirigiendo a /login si no hay sesion) antes de exponerlos
// via Outlet context hacia Layout y, desde ahi, hacia los 5 dashboards
// portados (JUP-095, grupo 6, sub-ronda a -- ver Addendum de design.md).
// `/login`, `/ingest`, `/assistant` y `/overview-legacy` llegan en las
// siguientes sub-rondas, cuando existan las paginas reconstruidas.
export const router = createBrowserRouter([
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
        ],
      },
    ],
  },
]);
