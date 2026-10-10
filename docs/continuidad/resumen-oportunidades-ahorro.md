# Resumen de oportunidades de ahorro — JUP-039

Verificado: 2026-10-10. Encargo «Implementa JUP-039 — Resumir oportunidades de
ahorro»; chat `01a124a5-d06b-7e12-a656-f4b26b84d749` (contexto del workspace).
Tarjeta https://trello.com/c/ojFr6fCU, ID `69da40893598f86e4762f2c8`.

## Alcance y decisiones confirmadas

Lectura Trello únicamente mediante DockerServer:
`/home/danteadmin/economicon-collaboration`, cliente `TrelloClient.get_cards()`
del contenedor oficial. Coincide con backlog-dispatch-source.json del 10/10.
P1 Valor FinOps; Paris liderazgo, Victor pairing, Alejandro revisión y Lucia
validación. Sin modificación de roles, prioridad, fechas ni aceptación.

No existían rama ni PR039 remotas. Copia Git propia `tfm-economicon-jup039`,
rama `feat/JUP-039-savings-summary`, base origin/develop `c2995a1`.
No se edita el checkout compartido ni ramas de otros chats.

Entrega publicada: [PR #98 draft](https://github.com/EconomiconFinOps/tfm-economicon/pull/98),
contra develop; implementación en `863f8ab`, seguida de cierre documental.
Se solicitó adjuntar la PR al chat, pero la herramienta de la aplicación no
devolvió confirmación; el enlace GitHub está verificado. Es contribución para
liderazgo, no revisión propia.

PR y evidencias vinculadas mediante comentario oficial Trello
`6ac9ece9a408960336ce0489`, 10/10. Respuesta del cliente confirma tarjeta correcta
y lista `10 — Backlog`; no se mueven estados ni se marcan criterios humanos.

Servicio determinista, selección explícita y comando `/ahorro inicio fin`.
Fuentes y supuestos completos en metadata.savings_evidence. Sin confundir
estimaciones con ahorro realizado, sin mezclar monedas ni sumar solapamientos.
Adapter033/034 consume loaders internos; el runtime sin proveedor devuelve503.
No se incorpora una fixture al runtime ni se afirma integración financiera real.

Las copias033/034 examinadas tienen contratos distintos:033 genera candidatos
por proyecto sin savings;034 evalúa escenarios hipotéticos con scopes atómicos.
No inferir estos scopes ni ahorros a partir del coste observado. Totales034
originales se preservan, sin recalcularlos desde filas redondeadas.

## Archivos y comprobaciones

- [Contrato](../api/savings-summary.md).
- [Evidencia y comandos](../evidence/JUP-039-validation.md).
- OpenSpec: `openspec/changes/jup-039-savings-summary/`.
- Código: `apps/backend/app/{schemas/savings.py,services/savings_summary.py,services/savings_sources.py}` y entrada del asistente.

Servicio/schema85 y adapter44 pasan. API/regresiones118 pasan y2 CockroachDB
omitidas por falta de URL externa. Smoke local con funciones reales033/034
correcto sobre datos sintéticos; hashes en evidencia. OpenSpec56/56, políticas
PR/gobernanza70 y CI12, trazabilidad9/9, higiene y compileall correctos.
Tres bordes hallados en auditoría técnica interna (controles vacíos, fechas epoch,
serialización no JSON) corregidos y cubiertos; las7 regresiones HTTP finales
pasan. No equivale a revisión humana.
GitHub Iber1to/autor Git Alejandro: entrega como contribución propia para Paris,
no se acredita revisión independiente de Alejandro ni reasignación implícita.
Control remoto `JUP reviews` comprobado: faltan ambas reviews tituladas, esperado
en este borrador. CI técnico remoto aún sin resultado definitivo en el corte;
las ejecuciones canceladas por nuevos eventos no cuentan como evidencia verde.
Pendiente real: loaders servidor033/034 integrados y comprobados, pairing
efectivo, Revision JUP-039 y Validacion JUP-039. No merge, cierre de tarjeta,
mensajes Discord ni archivo del chat.
