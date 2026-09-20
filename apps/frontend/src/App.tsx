// App: en la nueva arquitectura de rutas (JUP-095, grupo 6, sub-ronda d --
// ver Addendum de design.md) toda la logica que este archivo concentraba
// (sesion, bootstrap de tenants, tenant activo, el switch manual por
// `activeView`) se reparte entre `SessionGate` (sesion/tenant) y `Layout`
// (nav + selector de ambito + panel de sesion), ya trasladados en
// sub-rondas anteriores del mismo grupo. Queda reducido a montar el router,
// igual que el `App.tsx` del origen.
//
// Migracion a `.tsx` (JUP-095, grupo 8, tarea 8.1): componente sin props ni
// estado, no requiere tipado adicional bajo `strict: true` mas alla de la
// inferencia de tipos que ya aportan `RouterProvider` y `router` (tipado en
// `./routes`).
import { RouterProvider } from "react-router";
import { router } from "./routes";

export default function App() {
  return <RouterProvider router={router} />;
}
