## 1. Preparación

- [x] 1.1 Anotar el snapshot del origen (ruta `../Economicon` y commit hash actual) en la sección
  "Inventario del frontend de Economicon" de `design.md`.

## 2. Confirmar supuestos (una tarea = un supuesto = un commit)

- [x] 2.1 Confirmar versión de React/Vite desde `../Economicon/package.json`; volcar al inventario de
  `design.md` y reemplazar el `[ASUNCION]` correspondiente en el spike.
- [x] 2.2 Confirmar el routing (librería y versión; dependencias nuevas); inventario + spike.
- [ ] 2.3 Confirmar la librería de datos/estado (TanStack Query / Redux / SWR / otro); inventario + spike.
- [ ] 2.4 Confirmar el modelo de auth/sesión y su encaje con `Bearer` + `X-Tenant-Id`; inventario + spike.
- [ ] 2.5 Confirmar el sistema de estilos (CSS plano / Modules / Tailwind / styled-components); inventario + spike.
- [ ] 2.6 Confirmar assets estáticos (fuentes, imágenes, iconos) y sus licencias; inventario + spike.
- [ ] 2.7 Confirmar variables de entorno `VITE_*` requeridas por el origen; inventario + spike.

## 3. Cierre y verificación

- [ ] 3.1 Actualizar el "Checklist de inspección del origen" del spike marcando los ítems resueltos.
- [ ] 3.2 Verificar que no queda ningún `[ASUNCION]` en `docs/spikes/frontend-migration.md` y que cada
  uno tiene su entrada en el inventario de `design.md`.
- [ ] 3.3 Registrar en `review.md` y en `openspec/findings/backlog.md` (ID `RF-083-<secuencia>`)
  cualquier capacidad de Economicon sin equivalente en el backend de este repo.
- [ ] 3.4 Ejecutar `pnpm openspec:validate` y dejar constancia del resultado.
