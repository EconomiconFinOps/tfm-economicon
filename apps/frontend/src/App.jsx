// App: en la nueva arquitectura de rutas (JUP-095, grupo 6, sub-ronda d --
// ver Addendum de design.md) toda la logica que este archivo concentraba
// (sesion, bootstrap de tenants, tenant activo, el switch manual por
// `activeView`) se reparte entre `SessionGate` (sesion/tenant) y `Layout`
// (nav + selector de ambito + panel de sesion), ya trasladados en
// sub-rondas anteriores del mismo grupo. Queda reducido a montar el router,
// igual que el `App.tsx` del origen. No se renombra a `.tsx` en esta tarea:
// eso es alcance de un grupo posterior de la tarjeta.
import { RouterProvider } from "react-router";
import { router } from "./routes";

export default function App() {
  return <RouterProvider router={router} />;
}
