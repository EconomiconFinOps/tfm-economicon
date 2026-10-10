# Panel de recomendaciones — JUP-058

## Preparación e implementación — 2026-10-10

Encargo: «Implementa JUP-058 — Diseñar panel de recomendaciones», chat
`01a124a6-fe91-7882-bc5e-b86fb557b9a6`; origen delegado
`01a1248a-4e9e-7963-a891-5d8cb49345a6`. Tarjeta
https://trello.com/c/kU8swHK1, P1 Valor FinOps.

Consulta oficial realizada el 10/10 mediante DockerServer,
`/home/danteadmin/economicon-collaboration`, `TrelloClient.get_cards()` dentro
del contenedor. La descripción conserva el objetivo de clasificación por tipo,
ahorro estimado y dificultad y cinco criterios mínimos. Roles: Lucía liderazgo,
Paris pairing, Victor revisión, Alejandro validación. No se inventa actividad
humana ni se alteran asignaciones, prioridad o fechas.

No se encontró PR JUP-058 ni rama previa en el remoto. Se creó copia Git
independiente en `tfm-economicon-jup058`, rama
`feat/JUP-058-recommendations`, desde origin/develop
`c2995a118d419dfe725247bac9c6f219a3f0ea77`. El checkout compartido contenía
cambios ajenos y se preservó sin editarlo.

Hallazgo confirmado: panel anterior exclusivamente estático, ejemplos AWS,
estadísticas no derivadas y botón Implementar sin acción. Contratos 033/034 no
integrados en base; propuestas locales leídas sin modificar sus copias.
Decisión: adaptar dichos contratos, reutilizar datos/estilos existentes y
mantener demo, costes observados y ahorro potencial claramente diferenciados.

Diseño y frontera: [arquitectura](../architecture/recommendations-panel.md).
OpenSpec: `jup-058-recommendations-panel`. No se duplica motor 033,
evaluador 034 ni marca 112. No se enviaron mensajes Discord.

## Entrega técnica comprobada — 2026-10-10

Panel funcional en `/recommendations`: clasificación, orden exacto por moneda,
mensual/anual, detalle accesible, evidencia y CSV visible seguro. Demo explícita;
modo cliente con sesión/tenant/mes y GET propuesto JUP-033, sin fallback demo.
JUP-034 sólo se adapta como informe de entrada; no se invoca ni duplica motor.

Ver [evidencia por criterio y comandos](../validation/jup058/README.md): 644/644
tests frontend, typecheck/lint correctos, build frontend y Turbo 4/4 (shim
temporal Corepack/pnpm9 ante fallo NO_TTY del shim del runtime), gobernanza
82/82, contratos Python 9/9. OpenSpec 56/56 antes y después del archivo técnico
`openspec/changes/archive/2026-10-10-jup-058-recommendations-panel/`.
Chromium con dobles HTTP: filtros, vacío, teclado, CSV descargado y 503/reintento
sin fallback; sin errores JavaScript. Evaluación visual asistida PASS.

El shell heredado sigue desbordando en móvil a 1134 px; el panel no añade
overflow propio. No se probó backend desplegado, autorización real con dos
tenants, Azure, generación/ejecución de recomendaciones ni CSV en Excel.
Las propuestas dependientes ya se publicaron como PR #97 (JUP-033,
`1c8dabf62c99a7ec55a0367d3e1c418a5c05733f`) y #96 (JUP-034,
`61001a2227d0d1609987de02ffc8a54d8b7f5f96`); sus contratos coinciden con los
hashes comprobados, pero ninguna está integrada en la base.

La cuenta GitHub `Iber1to` y el autor Git configurado corresponden a Alejandro,
asignado a validación. Entrega en rama propia para Lucía, sin reasignar roles
ni acreditar pairing o dictámenes humanos. No debe validarse el propio cambio;
el liderazgo resolverá autoría/independencia antes de aceptación formal.

Pendiente de publicación del borrador y enlace en Trello. Después: integración
033/034, contraste con backend, pairing, revisiones independientes y aceptación.
