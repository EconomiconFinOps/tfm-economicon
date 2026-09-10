// SessionGate: ruta padre de `Layout` en el arbol de react-router. Resuelve
// sesion y bootstrap de tenants antes de exponerlos hacia las rutas hijas via
// Outlet context (JUP-095, grupo 6, sub-ronda a -- ver Addendum de
// design.md). La logica de sesion/tenant se reproduce verbatim desde
// `App.jsx` (mismo patron de inicializacion perezosa, misma query, mismo
// efecto de auto-seleccion): no es una reescritura, es un traslado de sitio
// -- unicamente cambian los estados de carga/error del bootstrap, que son
// armazon nuevo (no una pantalla portada), reconstruidos sobre Tailwind.
import { useEffect, useMemo, useState } from "react";
import { Navigate, Outlet } from "react-router";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { fetchTenants } from "../services/api";

const SESSION_KEY = "finops.session";
const TENANT_KEY = "finops.activeTenant";

// Forma minima de los datos que SessionGate controla directamente: la sesion
// persistida en localStorage y un tenant. `services/api.js` no esta tipado
// (checkJs: false, JUP-096 pendiente), asi que el resultado de `fetchTenants`
// llega con tipado laxo por la frontera JS->TS; no forzamos casts sobre esa
// frontera, solo tipamos explicitamente lo que exponemos hacia abajo.
interface SessionUser {
  full_name?: string;
  email?: string;
  id?: string;
  [key: string]: unknown;
}

interface Session {
  accessToken: string;
  user?: SessionUser;
}

interface Tenant {
  id: string;
  name: string;
  [key: string]: unknown;
}

// Contrato de Outlet context que `Layout.tsx` y las paginas de las siguientes
// sub-rondas del grupo 6 deben importar y usar para tipar su
// `useOutletContext<SessionOutletContext>()`, en vez de repetir la forma a
// mano en cada consumidor.
export interface SessionOutletContext {
  token: string;
  user?: SessionUser;
  tenants: Tenant[];
  activeTenant: Tenant | null;
  activeTenantId: string;
  onTenantChange: (nextTenantId: string) => void;
  onLogout: () => void;
}

// Copiada tal cual de App.jsx:21-33 (mismo patron de lectura perezosa de
// localStorage con manejo de error de parseo) -- no se reinventa el
// mecanismo, se traslada de sitio.
function loadStoredJson<T>(key: string): T | null {
  const value = window.localStorage.getItem(key);
  if (!value) {
    return null;
  }

  try {
    return JSON.parse(value) as T;
  } catch {
    window.localStorage.removeItem(key);
    return null;
  }
}

export function SessionGate() {
  const queryClient = useQueryClient();
  const [session, setSession] = useState<Session | null>(() => loadStoredJson<Session>(SESSION_KEY));
  const [activeTenantId, setActiveTenantId] = useState<string>(
    () => window.localStorage.getItem(TENANT_KEY) || ""
  );

  // Bootstrap de tenants: mismo queryKey/queryFn/enabled que App.jsx:43-47.
  // `enabled: Boolean(session?.accessToken)` es lo que garantiza que, sin
  // sesion, nunca se llega a invocar `fetch` (cubierto por
  // SessionGate.test.tsx, escenario "sin sesion").
  const tenantsQuery = useQuery({
    queryKey: ["tenants", session?.user?.id],
    queryFn: () => fetchTenants(session?.accessToken),
    enabled: Boolean(session?.accessToken)
  });

  // Auto-seleccion de tenant activo: mismo efecto que App.jsx:49-67,
  // incluida la limpieza de la clave de localStorage cuando no hay sesion.
  useEffect(() => {
    if (!session) {
      setActiveTenantId("");
      window.localStorage.removeItem(TENANT_KEY);
      return;
    }

    const tenants: Tenant[] = tenantsQuery.data?.items ?? [];
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

  const activeTenant = useMemo<Tenant | null>(
    () =>
      (tenantsQuery.data?.items ?? []).find((tenant: Tenant) => tenant.id === activeTenantId) ??
      null,
    [tenantsQuery.data, activeTenantId]
  );

  // Verbatim de App.jsx:83-89: limpia sesion (estado + localStorage), tenant
  // activo y cache de react-query. Al poner `session` a null aqui (igual que
  // `setSession(null)` en el origen), el propio SessionGate se re-renderiza y
  // el `if (!session)` de mas abajo pasa a devolver `<Navigate to="/login" />`
  // -- sin necesidad de navegacion imperativa adicional. Se usa tanto desde
  // el boton de logout del panel de sesion (Layout, via Outlet context) como
  // desde el estado de error del bootstrap ("Reset session").
  function handleLogout() {
    setSession(null);
    setActiveTenantId("");
    window.localStorage.removeItem(SESSION_KEY);
    window.localStorage.removeItem(TENANT_KEY);
    queryClient.clear();
  }

  function handleTenantChange(nextTenantId: string) {
    setActiveTenantId(nextTenantId);
    window.localStorage.setItem(TENANT_KEY, nextTenantId);
  }

  if (!session) {
    return <Navigate to="/login" replace />;
  }

  if (tenantsQuery.isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#0f1419] text-white">
        <section className="rounded-lg border border-[#2d3748] bg-[#1a1f2e] px-8 py-6 text-center shadow-lg">
          <p className="text-sm uppercase tracking-wide text-slate-400">Tenant bootstrap</p>
          <h1 className="mt-2 font-bold">Cargando tenants disponibles...</h1>
        </section>
      </div>
    );
  }

  if (tenantsQuery.error) {
    const message =
      tenantsQuery.error instanceof Error ? tenantsQuery.error.message : "Error desconocido";
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#0f1419] text-white">
        <section className="rounded-lg border border-[#2d3748] bg-[#1a1f2e] px-8 py-6 text-center shadow-lg">
          <p className="text-sm uppercase tracking-wide text-slate-400">Tenant bootstrap failed</p>
          <h1 className="mt-2 font-bold">No se han podido cargar los tenants</h1>
          <p className="mt-2 text-sm text-slate-400">{message}</p>
          <button
            className="mt-4 rounded-md bg-[#0078d4] px-4 py-2 text-sm font-medium text-white hover:bg-[#0078d4]/80"
            type="button"
            onClick={handleLogout}
          >
            Reset session
          </button>
        </section>
      </div>
    );
  }

  const tenants: Tenant[] = tenantsQuery.data?.items ?? [];

  const context: SessionOutletContext = {
    token: session.accessToken,
    user: session.user,
    tenants,
    activeTenant,
    activeTenantId,
    onTenantChange: handleTenantChange,
    onLogout: handleLogout
  };

  return <Outlet context={context} />;
}
