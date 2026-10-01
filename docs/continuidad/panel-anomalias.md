# Panel de anomalías — JUP-057

Verificación: 2026-10-01. Origen: «JUP-057 — Panel de anomalías y alertas», chat
`01a0f8e2-c058-7630-bea7-784f50bfac6a`.

## Alcance y decisiones

Preparar interfaz para criticidad, impacto y anomalías abiertas con datos de
prueba. [Trello](https://trello.com/c/29e5Pisa), tarjeta `69da430ef83c793fae057c79`.
Consulta mediante DockerServer `/home/danteadmin/economicon-collaboration`,
`docker compose run --rm collaboration sync`, snapshot `snapshot-20261001T191458Z.json`.
Roles: Alejandro liderazgo, Lucia pairing, Paris revisión, Victor validación.

Base `de0d62e`, rama `feat/JUP-057-anomalies-panel`, checkout
`tfm-economicon-jup057`. La pantalla ya existía; sus métricas anunciaban 23
detecciones y 87% de resolución frente a cinco filas. Tres abiertas suman
30.700 EUR; dos abiertas tienen criticidad alta. Se conservan los ejemplos,
con indicadores derivados, filtros y procedencia demo explícita.

Especificación: [change JUP-057](../../openspec/changes/jup-057-anomalies-panel/proposal.md).
Código: `apps/frontend/src/pages/AnomaliesPanel.tsx` y `src/data/demo/anomaliesPanel.ts`.
JUP-030/C5, RF-091-003 y RF-095-002 siguen pendientes: preparar UI no implementa
detección, notificaciones ni datos reales por tenant. JUP-099 no está incorporada
a esta base; evitar una migración global de estilos.

## Estado

Interfaz implementada con filtros combinados, ordenación, vacío/restablecimiento,
exportación de la selección con procedencia demo e indicadores derivados. Se retira
el gráfico engañoso en tiempo real. Sin cambios de backend ni Layout.

[Evidencia](../evidence/JUP-057-validation.md): 46 suites/269 tests PASS, cinco
pruebas focalizadas, typecheck/lint/build, OpenSpec 36/36, trazabilidad e higiene.
Navegador real con sesión simulada verifica métricas, filtros, CSV descargado,
vacío/reset y móvil, cero pageerror. Panel 390 px sin overflow propio; shell
heredado 1026 px (RF-026-002), pendiente y fuera de la corrección. No afirmar
aprobación visual global móvil. Evaluación independiente del panel PASS.

Evidencias locales: `materiales/07-evidencias/JUP-057-panel-2026-10-01/` en el
workspace padre (capturas, resultados, script y log completo). La ejecución usa
`corepack pnpm --filter @finops/frontend dev` y `/anomalies` con sesión demo.

Entrega: [PR #62](https://github.com/EconomiconFinOps/tfm-economicon/pull/62) abierta
hacia develop, implementación `c6015a3`. Enlace y evidencia añadidos conservando
la descripción anterior de Trello; movida a **40 — En revisión** y lectura
posterior verificada el 01/10/2026 21:29 Europe/Paris, mediante el puente autorizado.
Resultado local `trello-after.json`; no se envían comentarios ni Discord.

Pendientes: revisión Paris, pairing Lucia y validación Victor según roles
vigentes. No se atribuyen aprobaciones humanas ni se hace merge.
Integración real futura depende de JUP-030. No se envían mensajes a Discord.
