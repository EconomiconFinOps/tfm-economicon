# JUP-105 / RF-093-001: entorno pnpm

Verificado el 10/10/2026 contra las notas de la integración oficial Trello de
DockerServer, snapshot `snapshot-20261010T075415Z.json`. La prueba se ejecutó el
09/10; este corte reconcilia su evidencia, no la repite.

- Fuente de la prueba: `ff2ea6be12abf1bea4789791c34efb46c3b55aa8`, copia aislada
  `../tmp/jup105-codex-develop-ff2ea6b`, Windows 11 Pro, Node 24.14.1, PowerShell
  de Codex y PATH original. `corepack pnpm install --frozen-lockfile`: exit 0.
- `corepack pnpm exec pnpm --version`: 11.19.0 desde el lanzador fallback de
  Codex, exit 0. `corepack pnpm lint --force`: exit 1, 0/4 tareas, 0 caché,
  `ERR_PNPM_ABORTED_REMOVE_MODULES_DIR_NO_TTY`. Es un caso distinto del error de
  versión observado con pnpm global en Victor/Lucía.
- Recibos en [JUP-105](https://trello.com/c/YZvtBdGV):
  `6ac84c3f99a6c78a1e5b2a38` y `6ac94909af1d4e6ea614bfb1`.
  Evidencia local en `../materiales/07-evidencias/JUP-105-rf093001-codex-20261009/`.
  No contiene una ejecución de la consola normal del usuario.
- Paris informó pnpm 9.0.0 y lint 4/4 fuera de Codex; no necesitó aplicar
  `corepack enable`, por lo que no acredita ese remedio. Su resultado es
  evidencia aportada, no prueba propia de este chat.

**RF-093-001 sigue Open.** Pendientes: prueba de Alejandro en PowerShell normal
fuera de Codex y corrección permanente del runtime, con su comprobación en el
PATH original. No cerrar el finding por CI verde ni por confirmar solo la consola
normal. No modificar Corepack global para fabricar un resultado equivalente.

Comandos preparados para el usuario, desde la copia de `ff2ea6b`:

```powershell
git rev-parse HEAD
where.exe pnpm
corepack pnpm exec pnpm --version
corepack pnpm lint --force
```

Origen: encargo «Implementa JUP-105 — Cerrar la epica de migracion del frontend»;
reutiliza el diagnóstico y pairing del 09–10/10. Véase el
[aporte residual](../evidence/JUP-105-residual.md) y la
[continuidad de la PR](pipeline-turbo-pnpm.md).
