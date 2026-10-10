# Taxonomía de etiquetas y costes — JUP-015

Verificado: 10/10/2026, Europe/Paris. Origen: encargo «JUP-015 — Diseñar taxonomía
mínima de tagging y costes», delegado desde chat
`01a1248a-4e9e-7963-a891-5d8cb49345a6`; identificador receptor no disponible.

[Trello](https://trello.com/c/UDIyjTyl), ID `69da3d703335fb5f4c55a31d`.
Copia propia `tfm-economicon-jup015`, rama `docs/JUP-015-tagging-taxonomy`, base
`c2995a118d419dfe725247bac9c6f219a3f0ea77`. Checkout compartido intacto.

[PR #88](https://github.com/EconomiconFinOps/tfm-economicon/pull/88) draft contra
develop, MERGEABLE. Entrega técnica `c638b4c`; CI técnica 7/7 verde en
[run 38034907273](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/38034907273).
Gate JUP reviews pendiente humano. Trello enlazado por el puente oficial,
action `6ac9eb50c8c89dfec635a3e7`, 10/10 07:37:52Z; sin mover tarjeta.

## Conclusiones y decisiones

[Taxonomía canónica](../architecture/tagging-taxonomy.md),
[ADR-0018 Proposed](../adr/ADR-0018-tagging-taxonomy.md) y
[evidencia por criterio](../evidence/JUP-015-validation.md) reúnen la entrega.
Se conserva `economicon-minimum-v1` de JUP-017 y se define una capa separada
`economicon-catalog-v1`, por tenant/versión/vigencia. No se equiparan proyecto con
aplicación ni organización con equipo/unidad. Membresía y mapeo son explícitos.

Confirmado por Trello oficial y código el 10/10: la PR66/JUP017 usa reglas
sintácticas sin catálogo corporativo; head `6e25b308d9a890f9b73e4df7a55d904ae34b0065`.
Owner/application sólo se promueven desde Tags serializado. Escalares de origen
se convierten a texto; el verificador no acredita tipos originales ni dato real.
Se entrega plantilla draft, catálogo example y verificador offline; no consumidores.

## Verificación y siguiente paso

26 pruebas y 22 casos sintéticos pasan; OpenSpec 56/56 y gobernanza 95/95; detalle, comandos y
limitaciones en evidencia. Pruebas de contrato/CLI y paridad v1 se registran allí.
La inspección de agentes es QA técnica, no revisión atribuida a una persona.

Paris liderazgo, Victor pairing, Alejandro revisión, Lucia validación continúan
como asignados. Pairing, reviews, catálogo real/aprobación y adopción de los
consumidores están pendientes. Antes de ready, liderazgo debe resolver la
independencia autor/revisor si la cuenta de publicación coincide con Alejandro.
No se cambia la tarjeta de columna ni se declara cierre. No se envía Discord.
