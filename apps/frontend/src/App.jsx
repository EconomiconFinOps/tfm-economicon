import { useState } from "react";
import { AppShell } from "./layouts/AppShell";
import { DashboardPage } from "./pages/DashboardPage";
import { PlaceholderPage } from "./pages/PlaceholderPage";

const NAV_ITEMS = [
  { id: "overview", label: "Overview" },
  { id: "costs", label: "Costs" },
  { id: "tenants", label: "Tenants" },
  { id: "settings", label: "Settings" }
];

export default function App() {
  const [activeView, setActiveView] = useState("overview");

  const view = activeView === "overview"
    ? <DashboardPage />
    : <PlaceholderPage view={activeView} />;

  return (
    <AppShell
      activeView={activeView}
      items={NAV_ITEMS}
      onSelect={setActiveView}
    >
      {view}
    </AppShell>
  );
}

