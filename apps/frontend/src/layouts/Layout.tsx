import { Outlet, NavLink, useOutletContext } from "react-router";
import {
  BarChart3,
  TrendingDown,
  AlertTriangle,
  Lightbulb,
  DollarSign,
  Activity,
  LogOut,
  Upload,
  MessageSquare,
  LayoutDashboard
} from "lucide-react";
import type { SessionOutletContext } from "./SessionGate";

// TenantScopedOutlet: frontera de remontaje por tenant (reconciliacion con
// develop, Punto 1 -- aislamiento de estado entre tenants). Se usa como
// `Component` de un nivel de ruta intermedio en routes.tsx que envuelve
// UNICAMENTE `IngestPage`/`ConversationsPage` (las dos pantallas con
// formularios/selecciones/resultados de mutacion locales que no deben
// sobrevivir a un cambio de tenant) -- mismo alcance que `tenantPageKey` en
// App.jsx original (App.jsx:159), que tampoco envolvia el dashboard ni las
// pantallas de demostracion. `key={activeTenant?.id}` fuerza a React a
// desmontar la pantalla anterior por completo al cambiar de tenant en vez de
// limpiar campos en un efecto: eso es lo que garantiza que una respuesta
// tardia de una mutacion iniciada con el tenant anterior (el `onSuccess`/
// `onError` sigue capturando su `queryClient`/queryKey en la closure) no
// tenga ya una instancia montada de ese tenant cuyo estado local pueda
// tocar. `"no-tenant"` cubre el caso sin tenant activo.
export function TenantScopedOutlet() {
  const ctx = useOutletContext<Partial<SessionOutletContext>>() ?? {};
  return <Outlet key={ctx.activeTenant?.id ?? "no-tenant"} context={ctx} />;
}

export function Layout() {
  // Contexto defensivo: `Layout` puede montarse sin `SessionGate` por encima
  // (test del grupo 5, ya commiteado, que renderiza <Layout /> dentro de un
  // MemoryRouter sin arbol de rutas real) -- `useOutletContext` devuelve
  // `undefined` en ese caso, no lanza, asi que `?? {}` evita desestructurar
  // sobre `undefined`. `Partial<...>` porque, sin el contexto real, ninguno
  // de los campos esta garantizado.
  const ctx = useOutletContext<Partial<SessionOutletContext>>() ?? {};
  const { tenants, activeTenantId, onTenantChange, user, onLogout } = ctx;

  const navItems = [
    { path: "/", label: "Coste Global", icon: DollarSign },
    { path: "/operational", label: "Coste Detallado", icon: BarChart3 },
    { path: "/cuts", label: "Corte Global", icon: TrendingDown },
    { path: "/anomalies", label: "Anomalías", icon: AlertTriangle },
    { path: "/recommendations", label: "Recomendaciones", icon: Lightbulb },
  ];

  // Reconciliacion con develop (Punto 5): las tres pantallas conectadas al
  // backend (ingesta, asistente, resumen puente) existian como rutas
  // (routes.tsx) pero sin ningun enlace real en el menu -- solo alcanzables
  // escribiendo la URL a mano. Se listan en un grupo separado, con un
  // separador visual respecto a las 5 de arriba, para no confundir datos de
  // demostracion (navItems) con datos reales del backend (backendNavItems).
  // Etiquetas en ingles porque son las mismas que ya usan estas tres
  // pantallas (Create ingestion job, Assistant chat...), a diferencia de las
  // 5 de demostracion (traducidas del origen Figma).
  const backendNavItems = [
    { path: "/ingest", label: "Ingestions", icon: Upload },
    { path: "/assistant", label: "Assistant", icon: MessageSquare },
    { path: "/overview-legacy", label: "Overview", icon: LayoutDashboard },
  ];

  return (
    <div className="size-full flex flex-col bg-[#0f1419]">
      {/* Header */}
      <header className="bg-gradient-to-r from-[#1a1f2e] to-[#232834] border-b border-[#2d3748] px-6 py-4 shadow-lg">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-gradient-to-br from-[#0078d4] to-[#00bcf2] shadow-lg shadow-blue-500/30">
              <Activity className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="font-bold text-white">FinOps AI Platform</h1>
              <p className="text-sm text-slate-400">Automatización Inteligente del Ciclo Operativo</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            {/* Selector de ambito de cliente: mismo patron que
                AppShell.jsx:38-49 (select nativo controlado), adaptado a
                Tailwind. Solo se renderiza cuando SessionGate provee los tres
                datos que necesita -- sin ellos (p.ej. sin Outlet context)
                queda ausente, tal como exige Layout.selector.test.tsx. */}
            {tenants && activeTenantId !== undefined && onTenantChange ? (
              <select
                aria-label="Ambito de cliente"
                className="text-sm text-white bg-[#1a1f2e] px-3 py-2 rounded-lg border border-[#2d3748] focus:outline-none focus:border-[#00bcf2]"
                value={activeTenantId}
                onChange={(event) => onTenantChange(event.target.value)}
              >
                {tenants.map((tenant) => (
                  <option key={tenant.id} value={tenant.id}>
                    {tenant.name}
                  </option>
                ))}
              </select>
            ) : null}

            {/* Panel de sesion: mismo patron que AppShell.jsx:52-61
                (identidad + boton de logout), adaptado a Tailwind. */}
            {user && onLogout ? (
              <div className="flex items-center gap-2 text-sm text-slate-400 bg-[#1a1f2e] px-4 py-2 rounded-lg border border-[#2d3748]">
                <div className="text-right leading-tight">
                  <p className="text-white font-medium">{user.full_name}</p>
                  <p className="text-xs text-slate-400">{user.email}</p>
                </div>
                <button
                  type="button"
                  onClick={onLogout}
                  className="ml-2 p-2 rounded-lg text-slate-400 hover:text-white hover:bg-[#232834] transition-all"
                  aria-label="Cerrar sesion"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            ) : null}

            <div className="text-sm text-slate-400 bg-[#1a1f2e] px-4 py-2 rounded-lg border border-[#2d3748]">
              {new Date().toLocaleDateString('es-ES', {
                weekday: 'long',
                year: 'numeric',
                month: 'long',
                day: 'numeric'
              })}
            </div>
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="bg-[#1a1f2e] border-b border-[#2d3748] px-6 shadow-lg">
        <div className="flex items-center gap-1">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === "/"}
              className={({ isActive }) =>
                `flex items-center gap-2 px-4 py-3 border-b-2 transition-all ${
                  isActive
                    ? "border-[#00bcf2] text-[#00bcf2] bg-[#0078d4]/10 shadow-inner"
                    : "border-transparent text-slate-400 hover:text-white hover:bg-[#232834]"
                }`
              }
            >
              <item.icon className="w-4 h-4" />
              <span className="text-sm font-medium">{item.label}</span>
            </NavLink>
          ))}

          {/* Separador entre las 5 pantallas de demostracion y las 3
              conectadas al backend (Punto 5): misma barra de navegacion,
              distincion visual de que unas sirven datos reales y otras no. */}
          <div className="mx-2 h-6 w-px bg-[#2d3748]" aria-hidden="true" />

          {backendNavItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `flex items-center gap-2 px-4 py-3 border-b-2 transition-all ${
                  isActive
                    ? "border-[#00bcf2] text-[#00bcf2] bg-[#0078d4]/10 shadow-inner"
                    : "border-transparent text-slate-400 hover:text-white hover:bg-[#232834]"
                }`
              }
            >
              <item.icon className="w-4 h-4" />
              <span className="text-sm font-medium">{item.label}</span>
            </NavLink>
          ))}
        </div>
      </nav>

      {/* Main Content */}
      <main className="flex-1 overflow-auto bg-[#0f1419]">
        {/* Reenvia el mismo contexto hacia las rutas hijas: necesario para
            las siguientes sub-rondas del grupo 6, aunque hoy ningun hijo lo
            consuma todavia.

            Reconciliacion con develop (Punto 1): la frontera de remontaje
            por tenant NO vive aqui (no se aplica a las 5 pantallas de
            demostracion ni a `DashboardPage`, que no tienen estado local
            que proteger y solo necesitan que su query se re-dispare con la
            nueva `tenantId`). Vive en `TenantScopedOutlet`, envolviendo
            unicamente `IngestPage`/`ConversationsPage` en routes.tsx --
            mismo alcance que `tenantPageKey` en App.jsx original
            (App.jsx:159), que tampoco envolvia el dashboard. Aplicarla aqui,
            a nivel de Layout, remontaria tambien la pantalla indice durante
            el arranque de sesion (SessionGate resuelve `activeTenant` en
            dos renders: null mientras `activeTenantId` local vale "",
            luego el tenant auto-seleccionado tras su efecto), introduciendo
            una carrera visible en un login en vivo aunque nunca hubiera
            cambio real de tenant. */}
        <Outlet context={ctx} />
      </main>
    </div>
  );
}
