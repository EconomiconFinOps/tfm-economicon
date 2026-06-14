import { useEffect, useMemo, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { AppShell } from "./layouts/AppShell";
import { DashboardPage } from "./pages/DashboardPage";
import { IngestPage } from "./pages/IngestPage";
import { LoginPage } from "./pages/LoginPage";
import { ConversationsPage } from "./pages/ConversationsPage";
import { PlaceholderPage } from "./pages/PlaceholderPage";
import { fetchTenants } from "./services/api";

const NAV_ITEMS = [
  { id: "overview", label: "Overview" },
  { id: "ingest", label: "Ingestions" },
  { id: "assistant", label: "Assistant" },
  { id: "settings", label: "Settings" }
];

const SESSION_KEY = "finops.session";
const TENANT_KEY = "finops.activeTenant";

function loadStoredJson(key) {
  const value = window.localStorage.getItem(key);
  if (!value) {
    return null;
  }

  try {
    return JSON.parse(value);
  } catch {
    window.localStorage.removeItem(key);
    return null;
  }
}

export default function App() {
  const queryClient = useQueryClient();
  const [activeView, setActiveView] = useState("overview");
  const [session, setSession] = useState(() => loadStoredJson(SESSION_KEY));
  const [activeTenantId, setActiveTenantId] = useState(
    () => window.localStorage.getItem(TENANT_KEY) || ""
  );

  const tenantsQuery = useQuery({
    queryKey: ["tenants", session?.user?.id],
    queryFn: () => fetchTenants(session.accessToken),
    enabled: Boolean(session?.accessToken)
  });

  useEffect(() => {
    if (!session) {
      setActiveTenantId("");
      window.localStorage.removeItem(TENANT_KEY);
      return;
    }

    const tenants = tenantsQuery.data?.items ?? [];
    if (tenants.length === 0) {
      return;
    }

    const stillAvailable = tenants.some((tenant) => tenant.id === activeTenantId);
    if (!stillAvailable) {
      const nextTenantId = tenants[0].id;
      setActiveTenantId(nextTenantId);
      window.localStorage.setItem(TENANT_KEY, nextTenantId);
    }
  }, [session, tenantsQuery.data, activeTenantId]);

  const activeTenant = useMemo(
    () => (tenantsQuery.data?.items ?? []).find((tenant) => tenant.id === activeTenantId) ?? null,
    [tenantsQuery.data, activeTenantId]
  );

  function handleLogin(payload) {
    const nextSession = {
      accessToken: payload.access_token,
      user: payload.user
    };
    setSession(nextSession);
    window.localStorage.setItem(SESSION_KEY, JSON.stringify(nextSession));
  }

  function handleLogout() {
    setSession(null);
    setActiveTenantId("");
    window.localStorage.removeItem(SESSION_KEY);
    window.localStorage.removeItem(TENANT_KEY);
    queryClient.clear();
  }

  function handleTenantChange(nextTenantId) {
    setActiveTenantId(nextTenantId);
    window.localStorage.setItem(TENANT_KEY, nextTenantId);
  }

  if (!session) {
    return <LoginPage onLogin={handleLogin} />;
  }

  if (tenantsQuery.isLoading) {
    return (
      <div className="auth-shell">
        <section className="auth-card">
          <p className="eyebrow">Tenant bootstrap</p>
          <h1>Loading available tenants...</h1>
        </section>
      </div>
    );
  }

  if (tenantsQuery.error) {
    return (
      <div className="auth-shell">
        <section className="auth-card">
          <p className="eyebrow">Tenant bootstrap failed</p>
          <h1>Unable to load tenants</h1>
          <p>{tenantsQuery.error.message}</p>
          <button className="primary-button" type="button" onClick={handleLogout}>
            Reset session
          </button>
        </section>
      </div>
    );
  }

  const tenants = tenantsQuery.data?.items ?? [];
  const view = activeView === "overview"
    ? (
        <DashboardPage
          token={session.accessToken}
          user={session.user}
          tenants={tenants}
          activeTenant={activeTenant}
        />
      )
    : activeView === "ingest"
      ? (
          <IngestPage
            token={session.accessToken}
            activeTenant={activeTenant}
          />
        )
      : activeView === "assistant"
        ? (
            <ConversationsPage
              token={session.accessToken}
              activeTenant={activeTenant}
            />
          )
        : <PlaceholderPage view={activeView} />;

  return (
    <AppShell
      activeView={activeView}
      items={NAV_ITEMS}
      onSelect={setActiveView}
      user={session.user}
      tenants={tenants}
      activeTenantId={activeTenantId}
      onTenantChange={handleTenantChange}
      onLogout={handleLogout}
    >
      {view}
    </AppShell>
  );
}
