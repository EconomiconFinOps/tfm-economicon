# JUP-056 · comprobaciones de frontend

Fecha: 2026-10-10. Copia aislada `tfm-economicon-jup056`; contribución técnica automatizada, sin atribuir revisión o validación a los responsables humanos.

Entorno observado: Windows, Node.js `v24.14.1`, pnpm `9.0.0`, Vite `5.4.21`, Vitest `3.2.7`.

Resultado de referencia: [CI del commit `f1e0dd6f5231276b19e685203fda2c3a8c3b2f4a`](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/38035433148), completada con éxito. En Ubuntu / Node `v22.23.3`, [Frontend build](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/38035433148/job/114164767414) ejecutó lint, **55 archivos / 640 pruebas PASS** (54.69 s) y build PASS (4.18 s). [Frontend type check](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/38035433148/job/114164767353) también terminó con éxito. Logs y SHA consultados mediante `gh api repos/EconomiconFinOps/tfm-economicon/actions/jobs/114164767414/logs` y `gh api repos/EconomiconFinOps/tfm-economicon/actions/runs/38035433148`.

| Comprobación | Resultado observado |
| --- | --- |
| `corepack pnpm --filter @finops/frontend typecheck` | PASS, exit 0: TypeScript de aplicación, configuración y pruebas. |
| `corepack pnpm --filter @finops/frontend lint` | PASS, exit 0. |
| `corepack pnpm --filter @finops/frontend build` | PASS, exit 0; 2484 módulos, 7m31s. Aviso de chunk JS de 787.94 kB (227.10 kB gzip), superior a 500 kB. Ejecutado antes de retirar dos alias de tema sin consumidores; la retirada se verifica con la prueba del tema. |
| `corepack pnpm --filter @finops/frontend test -- src/pages/OperationalCostDashboard.test.tsx src/lib/operationalCostDashboard.test.ts` | Primera ejecución con permisos de subprocess: 14/15 PASS; la espera inicial de tabla de una prueba agotó el límite de 1 segundo. La prueba nueva usa ahora espera de disponibilidad de hasta 10 segundos, sin alterar el comportamiento del producto. |
| `corepack pnpm --filter @finops/frontend test -- --maxWorkers=2 --testTimeout=20000 --hookTimeout=20000` | Ejecución local completa: 55 archivos, 632 pruebas PASS / 12 FAIL, 795.41 s. Incluye la versión del tema anterior a la retirada de alias. No se presenta como una ejecución local verde. |
| Control dirigido de tema y sesión (comando debajo) | Tema corregido: 108/108 PASS. Caso de sesión pendiente: 1 FAIL; 138 casos omitidos por el selector. No se considera resuelto localmente. |

La primera invocación de Vitest dentro del sandbox no pudo iniciar esbuild (`spawn EPERM`); las ejecuciones de Vitest y la compilación se repitieron con los permisos de procesos necesarios. No se cambió configuración del producto para sortearlo.

La suite completa detectó dos consumidores de tema retirados al sustituir la demostración: `--color-attention-foreground` y `--color-chart-5`. Se eliminaron exactamente esos dos alias de `@theme inline`; se conservaron sus variables de paleta y los demás estilos. No cambia ningún color visible ni se adelanta el trabajo de marca de JUP-112. La retirada elimina cuatro casos parametrizados de contrato de tema: por eso la ejecución local anterior contiene 644 pruebas y la CI definitiva contiene 640.

Comando del control local dirigido:

```powershell
corepack pnpm --filter @finops/frontend test -- src/test/theme-palette.test.ts tests/auth-session.test.tsx --maxWorkers=1 --testTimeout=20000 --hookTimeout=20000 -t 'different server id discards pending old tenant results|theme.css|búsqueda de consumidores|parser de theme.css|index.html'
```

Los otros diez fallos de la ejecución completa fueron esperas/timeouts en suites existentes: `auth-session` (1, identidad distinta con tenants anteriores pendientes), `login-session-expired-notice` (1, 401 en vuelo), `tenant-switching` (4, conversaciones/ingesta), `ExecutiveCostDashboard.isolated-month.jup055` (1, bootstrap del primer caso), `conversations` (1, reintento de mensaje), y los casos `history-replace` y `pending-attempt` del aviso de sesión (1 cada uno). El caso `auth-session` también falló en el control dirigido esperando `Monthly Spend`. La carga/latencia local es una hipótesis consistente con los tiempos observados; no se ha acreditado una causa única. No se modificaron esas pruebas ni su producto. La CI fresca, con esperas predeterminadas y el código final, pasa todos esos casos. No se ejecutó el control opcional con esperas globales aumentadas tras obtener esa evidencia completa de CI.

Las tres suites de JUP-056 pasaron tanto en la ejecución local completa como en CI: `OperationalCostDashboard.test.tsx` **5/5**, `operationalCostDashboard.test.ts` **10/10** y `useCostKpis.test.tsx` **1/1**. Ejercitan filtros simultáneos y serialización, aislamiento de caché por los cinco filtros/fechas/agrupación/etiqueta/cliente/generación de sesión, aplicar/limpiar, estados parciales/vacíos/error/carga, fechas y etiquetas inválidas, cancelación de consultas obsoletas, cambio de cliente, importes grandes/negativos/cero y exportación CSV escapada. Comprueban también el rechazo de un backend que ignore filtros o devuelva metadatos incompatibles. Los importes permanecen como cadenas decimales.

Estas comprobaciones usan dobles HTTP sintéticos explícitos; no acreditan conectividad Azure, cobertura de ingesta ni aceptación humana. La evidencia de navegador con dobles está en [browser-double-results.json](browser-double-results.json); la comprobación de backend se registra aparte en [backend-results.md](backend-results.md).
