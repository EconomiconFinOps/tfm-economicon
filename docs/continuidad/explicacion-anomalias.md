# Explicación de anomalías — JUP-038

Verificación: 2026-10-10. Origen: encargo «JUP-038 — Explicar anomalías detectadas»;
identificador del chat no confirmado.
[Trello](https://trello.com/c/QzkjVY7P), ID `69da4073c57a3979fcaab180`.
Registro completo del dispatch contrastado por cliente oficial desplegado en
DockerServer `/home/danteadmin/economicon-collaboration`: sin cambio de roles,
prioridad P1, criterios o fecha. No hay mensajes Discord.

## Entrega y decisiones

Copia aislada `tfm-economicon-jup038`, rama `feat/JUP-038-explain-anomalies`,
base `origin/develop` `c2995a1`. No se alteró el checkout compartido ni la rama
del detector JUP-030. Contribución independiente para liderazgo de Lucía;
Paris pairing, Víctor revisión y Alejandro validación siguen siendo roles
asignados, sin acreditarlos como realizados ni asumirlos por inferencia.

[PR #94 en borrador](https://github.com/EconomiconFinOps/tfm-economicon/pull/94)
publicada contra develop. Implementación `e7132a7`; sin merge ni solicitudes
de aprobación formal mientras no se resuelvan integración y roles efectivos.

El servicio explica reglas con Decimal y conserva evidencia v1. Ruta propia
`POST /assistant/conversations/{id}/anomaly-explanations`, sesión/tenant/propiedad
antes de leer costes; IDs y definición como entrada, sin importes del cliente.
Fotografía distinta produce 409; error o datos incompatibles no escriben chat.
La metadata del historial preserva números, periodos, fuente y límites.

No se atribuye causa ni ahorro. Available/evaluated no significa completo.
Base ausente/no positiva, calidad provisional, redondeo y separación de
lecturas se explicitan. JUP-035/036 no se modifica: [contrato de integración](../contracts/JUP-038-anomaly-explanations.md).

## Evidencia y siguiente paso

[Informe reproducible](../evidence/JUP-038-validation.md),
[OpenSpec activo](../../openspec/changes/jup-038-explain-anomalies/).
Pruebas nuevas 50/50 (26 explicador y 24 API/adaptador), gobernanza82/82,
OpenSpec56/56 y probe real de módulos
candidatos JUP-030 7/7, con facturación sintética. Hashes y versiones en informe.

La dependencia JUP-030 no está integrada en develop de partida: el runtime
actual devuelve 503, sin fixture de demostración. Revalidar después de integrar
su contrato y con SQL de coste real. La entrada libre/selector visual
JUP-035/036 y las reviews humanas siguen pendientes. No cerrar tarjeta,
archivar chat ni acreditar aceptación por estas pruebas técnicas.
