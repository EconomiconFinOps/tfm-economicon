import { Outlet, NavLink } from "react-router";
import { BarChart3, TrendingDown, AlertTriangle, Lightbulb, DollarSign, Activity } from "lucide-react";

export function Layout() {
  const navItems = [
    { path: "/", label: "Coste Global", icon: DollarSign },
    { path: "/operational", label: "Coste Detallado", icon: BarChart3 },
    { path: "/cuts", label: "Corte Global", icon: TrendingDown },
    { path: "/anomalies", label: "Anomalías", icon: AlertTriangle },
    { path: "/recommendations", label: "Recomendaciones", icon: Lightbulb },
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
          <div className="text-sm text-slate-400 bg-[#1a1f2e] px-4 py-2 rounded-lg border border-[#2d3748]">
            {new Date().toLocaleDateString('es-ES', {
              weekday: 'long',
              year: 'numeric',
              month: 'long',
              day: 'numeric'
            })}
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="bg-[#1a1f2e] border-b border-[#2d3748] px-6 shadow-lg">
        <div className="flex gap-1">
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
        </div>
      </nav>

      {/* Main Content */}
      <main className="flex-1 overflow-auto bg-[#0f1419]">
        <Outlet />
      </main>
    </div>
  );
}
