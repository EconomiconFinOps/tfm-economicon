// Revalidate profile and tenants in parallel before exposing protected routes.
// Session generations isolate logout, identity replacement and subsequent login.
import { useCallback, useEffect, useMemo, useState } from "react";
import { Navigate, Outlet } from "react-router";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  advanceSessionGeneration, clearSessionMutations, fetchProfile, fetchTenants, getSessionGeneration,
  invalidateSession, subscribeSessionInvalidation
} from "../services/api";
import { isNonemptyString, isUserProfile } from "../services/contracts";
import type { TenantRecord, UserProfile } from "../services/contracts";

// Exportada porque `LoginPage.tsx` necesita la misma clave para persistir la
// sesion tras el login (App.jsx.handleLogin:74-81 trasladado alli): centraliza
// el string magico en un unico sitio para que ambos archivos no puedan
// divergir silenciosamente si la clave cambia en el futuro.
export const SESSION_KEY = "finops.session";
const TENANT_KEY = "finops.activeTenant";

// Reconciliacion con develop (JUP-087, Punto 2): forma real de la sesion,
// usando `UserProfile` del contrato compartido con el backend en vez de una
// forma local laxa. `user` ya no es opcional: `isSession` (mas abajo)
// garantiza que, si `session` no es null, trae un `user` completo.
interface Session {
  accessToken: string;
  user: UserProfile;
}

// Storage uses the same profile guard as HTTP, plus a nonempty token.
function isSession(value: unknown): value is Session {
  return typeof value === "object" && value !== null && !Array.isArray(value)
    && "accessToken" in value && isNonemptyString(value.accessToken)
    && "user" in value && isUserProfile(value.user);
}

// Reconciliacion con develop (JUP-087): `services/api` ya no es `api.js` sin
// tipar, es `api.ts` contra `services/contracts.ts`. `fetchTenants()` ahora
// devuelve `TenantCollection` (items: `TenantRecord[]`), asi que los tenants
// que SessionGate expone hacia abajo usan ese tipo real en vez de una forma
// local laxa que divergiria en silencio del contrato.
export interface SessionOutletContext {
  token: string;
  user?: UserProfile;
  tenants: TenantRecord[];
  activeTenant: TenantRecord | null;
  activeTenantId: string;
  onTenantChange: (nextTenantId: string) => void;
  onLogout: () => void;
}

// Reconciliacion con develop (JUP-087, Punto 2): sustituye a la lectura sin
// validar (`JSON.parse(value) as T`) -- ademas del JSON roto (`catch`), un
// JSON valido con estructura invalida (p.ej. `{}`) tambien se descarta y
// limpia la clave, en vez de colarse como una sesion a medias.
function loadStoredSession(key: string): Session | null {
  const value = window.localStorage.getItem(key);
  if (!value) {
    return null;
  }

  try {
    const parsed: unknown = JSON.parse(value);
    if (isSession(parsed)) {
      return parsed;
    }
    window.localStorage.removeItem(key);
    return null;
  } catch {
    window.localStorage.removeItem(key);
    return null;
  }
}

export function SessionGate() {
  const queryClient = useQueryClient();
  const [session, setSession] = useState<Session | null>(() => loadStoredSession(SESSION_KEY));
  const [activeTenantId, setActiveTenantId] = useState<string>(
    () => window.localStorage.getItem(TENANT_KEY) || ""
  );
  const [generation, setGeneration] = useState(getSessionGeneration);

  useEffect(() => {
    const unsubscribe = subscribeSessionInvalidation(() => {
      setSession(null);
      setActiveTenantId("");
      window.localStorage.removeItem(SESSION_KEY);
      window.localStorage.removeItem(TENANT_KEY);
      queryClient.getQueryCache().clear();
      clearSessionMutations(queryClient);
    });
    if (!session) invalidateSession(generation);
    return unsubscribe;
  }, [queryClient, session, generation]);

  // Bootstrap de tenants: mismo queryKey/queryFn/enabled que App.jsx:43-47.
  // `enabled: Boolean(session?.accessToken)` es lo que garantiza que, sin
  // sesion, nunca se llega a invocar `fetch` (cubierto por
  // SessionGate.test.tsx, escenario "sin sesion").
  const tenantsQuery = useQuery({
    queryKey: ["tenants", session?.user?.id],
    queryFn: () => {
      if (!session) {
        throw new Error("Session required");
      }
      return fetchTenants(session.accessToken);
    },
    enabled: Boolean(session?.accessToken)
  });

  // Revalidacion de identidad contra el servidor (RF-090-003, decision 2 del
  // design.md de jup-097): se dispara con el mismo `enabled` que
  // `tenantsQuery` (mismo gatillo, `session?.accessToken`) para que ambas
  // peticiones se emitan juntas al arrancar, no una tras otra (tarea 3.4,
  // coste aceptado de una peticion mas en el arranque, no en serie). El
  // `user` de `localStorage` deja de ser la identidad expuesta: se sustituye
  // aqui por la que confirme el servidor via `GET /me`.
  const profileQuery = useQuery({
    queryKey: ["profile", session?.accessToken],
    queryFn: () => {
      if (!session) {
        throw new Error("Session required");
      }
      return fetchProfile(session.accessToken);
    },
    enabled: Boolean(session?.accessToken)
  });

  useEffect(() => {
    const profile = profileQuery.data;
    if (!session || !profile || profileQuery.isError || generation !== getSessionGeneration()) return;

    const nextSession = { ...session, user: profile };
    if (profile.id !== session.user.id) {
      // Discard bootstrap work for the previous identity before reusing keys.
      setGeneration(advanceSessionGeneration());
      setActiveTenantId("");
      window.localStorage.removeItem(TENANT_KEY);
      queryClient.removeQueries({
        predicate: (query) => query.queryKey[0] !== "profile"
          || query.queryKey[1] !== session.accessToken
      });
      clearSessionMutations(queryClient);
    }
    if (session.user !== profile) {
      window.localStorage.setItem(SESSION_KEY, JSON.stringify(nextSession));
      setSession(nextSession);
    }
  }, [session, profileQuery.data, profileQuery.isError, generation, queryClient]);

  // Parallel tenant results may select a tenant only for the current identity.
  useEffect(() => {
    if (!session) {
      setActiveTenantId("");
      window.localStorage.removeItem(TENANT_KEY);
      return;
    }
    if (generation !== getSessionGeneration() || profileQuery.isError
      || (profileQuery.data && profileQuery.data.id !== session.user.id)) return;

    const tenants: TenantRecord[] = tenantsQuery.data?.items ?? [];
    if (tenants.length === 0) {
      return;
    }

    const stillAvailable = tenants.some((tenant) => tenant.id === activeTenantId);
    if (!stillAvailable) {
      const nextTenantId = tenants[0].id;
      setActiveTenantId(nextTenantId);
      window.localStorage.setItem(TENANT_KEY, nextTenantId);
    }
  }, [session, tenantsQuery.data, activeTenantId, profileQuery.data, profileQuery.isError, generation]);

  const activeTenant = useMemo<TenantRecord | null>(
    () =>
      (tenantsQuery.data?.items ?? []).find(
        (tenant: TenantRecord) => tenant.id === activeTenantId
      ) ?? null,
    [tenantsQuery.data, activeTenantId]
  );

  // Manual logout and profile errors use the same cleanup as a global 401.
  // A callback belonging to an older generation cannot invalidate this one.
  const handleLogout = useCallback(() => {
    invalidateSession(generation);
  }, [generation]);

  function handleTenantChange(nextTenantId: string) {
    if (generation !== getSessionGeneration()) return;
    setActiveTenantId(nextTenantId);
    window.localStorage.setItem(TENANT_KEY, nextTenantId);
  }

  // Camino de fallo de la revalidacion (RF-090-003, decision 2): un token que
  // el servidor rechaza en `/me` reutiliza `handleLogout` -- el mismo que ya
  // usaba el bloque de error de `tenantsQuery` -- en vez de inventar un guard
  // nuevo. `handleLogout` pone `session` a `null`, lo que en el siguiente
  // render cae en el `if (!session)` de mas abajo y redirige a `/login`.
  // Se declara antes de este efecto (a diferencia de antes, ya no depende
  // del hoisting de `function`) y se lista en las dependencias porque su
  // identidad ya es estable via `useCallback`.
  useEffect(() => {
    if (profileQuery.isError) {
      handleLogout();
    }
  }, [profileQuery.isError, handleLogout]);

  if (!session) {
    return <Navigate to="/login" replace />;
  }

  // El bloque de carga cubre tambien `profileQuery`: mientras esta en curso,
  // no hay identidad confirmada que exponer. `profileQuery.isError` se anade
  // aqui (no como pantalla nueva, sino ampliando esta misma condicion) porque
  // hay un frame transitorio entre que el error llega y el efecto de arriba
  // ejecuta `handleLogout()`; sin esto, ese frame renderizaria el contexto
  // normal con un `user` que el servidor ya rechazo.
  if (tenantsQuery.isLoading || profileQuery.isLoading || profileQuery.isError
    || generation !== getSessionGeneration()
    || profileQuery.data?.id !== session.user.id) {
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

  const tenants: TenantRecord[] = tenantsQuery.data?.items ?? [];

  const context: SessionOutletContext = {
    token: session.accessToken,
    // RF-090-003 (decision 2): la identidad expuesta hacia abajo pasa a ser
    // la que confirma el servidor via `GET /me`, no la persistida en
    // `localStorage` -- que puede haber quedado desactualizada u obsoleta.
    user: profileQuery.data,
    tenants,
    activeTenant,
    activeTenantId,
    onTenantChange: handleTenantChange,
    onLogout: handleLogout
  };

  return <Outlet context={context} />;
}
