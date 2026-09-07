import { createBrowserRouter } from "react-router";
import { Layout } from "./layouts/Layout";
import { ExecutiveCostDashboard } from "./pages/ExecutiveCostDashboard";
import { OperationalCostDashboard } from "./pages/OperationalCostDashboard";
import { ExecutiveCutDashboard } from "./pages/ExecutiveCutDashboard";
import { AnomaliesPanel } from "./pages/AnomaliesPanel";
import { RecommendationsPanel } from "./pages/RecommendationsPanel";

export const router = createBrowserRouter([
  {
    path: "/",
    Component: Layout,
    children: [
      { index: true, Component: ExecutiveCostDashboard },
      { path: "operational", Component: OperationalCostDashboard },
      { path: "cuts", Component: ExecutiveCutDashboard },
      { path: "anomalies", Component: AnomaliesPanel },
      { path: "recommendations", Component: RecommendationsPanel },
    ],
  },
]);
