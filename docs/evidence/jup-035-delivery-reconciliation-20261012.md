# JUP-035 — Cierre documental de entrega — 12/10/2026

## Fuente y alcance

Proceso vigente: CONTRIBUTING.md, 2026-09-30 (JUP-100). PM verificó el 12/10
la tarjeta BJfABykd: Paris Arcos liderazgo, Víctor Méndez pairing, Alejandro
Aguado revisión, Lucía Mateo validación. Son asignaciones humanas; los informes
internos no demuestran que sus reviews hayan sido publicadas.

PM trasladó la autorización expresa de Paris para incorporar RAG/batería,
commitear y crear feat/JUP-035-chat-delivery. Checkpoint de importación:
42e9ff073bcc3380aeb9b8bda1315a092cbbc4b0, sobre base conciliada
281440320a5c39b077726d507691c6f955bf9105 que contiene develop
8035a3de08fcf8c4c5f825aeba0a07e7e8c4311f y el HEAD histórico 954b4429.
El delta aprobado se preservó en el commit fuente 9df21fd y fue incorporado
por PM; sólo se notificó auto-merge de docs/continuidad/README.md. TL confirmó
HEAD, rama, estado limpio de entrada y common Git directory del repositorio.

Este documento consolida evidencia existente. La normalización editorial de
finales de línea/EOF corresponde al ejecutor autorizado, sin cambios de lógica,
dependencias o tests nuevos. Entrega editorial recibida12/10 a12:18:12Canary:
siete rutas, bytes normalizados idénticos, seis AST Python idénticos y553 tokens
TypeScript no-trivia idénticos, parse sin diagnósticos. Guards editoriales de
producto3 y tests4 conformes; perfiles son fronteras de permiso, no Red/Green
de comportamiento. Sin ejecución de tests ni lógica nueva. Recibo report.md
SHAf9d57545beaf4bdee4b1155039735d94ae927fa26ae7ecd2241ccea91f70f498,
expediente externo jup035-line-ending-editorial-20261012.
Diffcheck mergebase/develop hacia copia de trabajo y diff local:exit0.
El rango exacto origin/develop...HEAD sigue exit2 histórico hasta el commit
de estos cambios; no se declara PASS entre refs antes de ese commit.
PM conserva commit, nueva referencia original antes
de lectores independientes, control de retorno/prepublicación y publicación.
La referencia histórica 46fc8e44 permanece intacta: no se reemplaza para atribuir
PASS a un estado que no examinó.

## Evidencia que se conserva y cómo se reutiliza

| Evidencia | Resultado observado | Vigencia y límite |
| --- | --- | --- |
| [Batería final y focales](jup-035-battery-final-focal-acceptance.md) | full28i: 25 favorables y tres fallos; focales posteriores 019/022 y 024 favorables | Ensayos distintos. No 28 PASS en una ejecución de la revisión final; no repetir batería por edición documental. |
| [Recuperación documental real](jup-035-required-tool-retrieval-20261012.md) | REVIEW_PASS conninfo; VALIDATION_PASS mínimo010, 16,703 s, dos LLM y un embedding, SQL real, par/reapertura | Evidencia del delta congelado original; reutilización exige comprobar integridad funcional de backend/processor importados. Sin nuevo gasto por defecto. |
| Conciliación frontend, recibos originales inspeccionados | 882 PASS/72 archivos; 339 focales incluidas/19 archivos, tipos/build/lint satisfactorios con avisos | No sumar 339 a 882. Conservar recibo, fuente y entorno originales; comprobar que la importación/editorial no cambia comportamiento de frontend conciliado. |
| Gobernanza conciliada, recibos originales inspeccionados | 66 especificaciones/0 FAIL y 95 pruebas de herramientas/0 FAIL | Conservar recibos y corte originales. Nueva documentación requiere checks documentales/traceabilidad afectados; no presentar este texto como ejecución nueva. |
| [Archivo autorizado](../../openspec/changes/archive/2026-10-11-jup-035-conversational-web-interface/archive-delivery.md) | Archivo realizado el 11/10 bajo autorización explícita | Archivo no significa merge ni revisión humana ni cierre de todas las casillas amplias. |

Recibos de conciliación: reconcile-jup035-develop-20261012-REPORT.md y logs
frontend-full, frontend-focused-corrected, frontend-typecheck, frontend-build,
frontend-lint, openspec y governance del expediente externo corrections-runtime.
Se ejecutaron sobre el merge aún pendiente de commit de HEAD954b4429 con
develop8035a3d, luego consolidado por PM en2814403. El focal original338PASS/1FAIL
por expectativa de navegación fue conservado; focal corregido339PASS.
Lint: cero errores y un warning de dependencia current en ChatPresentation;
build: avisos de chunk grande y módulo API importado dinámica/estáticamente.
La reconciliación preserva chat/ScreenCaptureProvider junto a marca/ThemeToggle,
ocho pestañas sin asistente ficticio y la unión de dependencias/lock ya existentes.

Los informes y recibos originales no se alteran. P3 de sensibilidad del wrapper
de diagnóstico conservado como mejora no bloqueante, sin lógica nueva. JUP-036
permanece en espera; no incorpora aquí sus 70 rutas ni cuatro adaptaciones.

El informe original remaining-validation/report-48-50.md fue inspeccionado
completo: VALIDATION_PASS de la matriz JSONB asignada48/50, sobre954b4429 el11/10.
94 focales offline y cinco deadlines; cuatro casos Cockroach reales distintos:
rollback por fallo de unicidad/Stop tardío, concurrencia idempotente, ACK perdido
después de COMMIT observado y migración con precisión/checkpoint. Reutiliza
212PASS/3SKIP de compresión con17/17 hashes vigentes y compara artefactos3/30/6;
no repitió la migración histórica ni cinco productores LLM reales. Deadline y
scope tenant/user son pruebas fixtures, no nueva batería nativa adversarial.
El informe acredita criterios48/50 dentro de esos límites; no aceptación de
toda035 ni review humana. La revisión49 favorable sólo figura como comunicación
del padre en ese informe; no sustituye su informe técnico original.

Originales PM históricos inspeccionados y SHA256 verificados:
JUP-035-remaining-review-original-954b442.json,
9ff66090068550fefe10e8217e3ef204271c8e4230a188d8075da042630db902;
JUP-035-remaining-validation-original-954b442.json,
d8aea18e0a304189c0ede5d98928ece3ef8b2e9fa6cc2849a33b92ddbe0b3d2d.
created_at:11/10/2026 20:05:46.359078 y20:05:47.641742 UTC,
equivalentes a21:05:46/47 Atlantic/Canary, anteriores al retorno20:42:23 UTC
documentado por Validador. No se reconstruyeron ahora; no se verifican contra
commits posteriores para convertir un cambio autorizado en un fallo histórico.

## Comprobaciones del checkpoint final

| Área | Comprobación aplicable | Estado de este corte |
| --- | --- | --- |
| Editorial | Equivalencia bytes normalizados/AST y diffcheck de la entrega | Recibo editorial conforme; diffcheck de copia de trabajo exit0. Pendiente commit PM y rango exacto entre refs. No sustituye revisión independiente. |
| Importación backend/processor | Contrastar delta aprobado y equivalencia tras finales de línea; revisión afectada de protocolos, recursos y persistencia | Pendiente sobre nueva referencia original PM; la aceptación real010 original se conserva. |
| Frontend sobre brand/demo | Revisión y revalidación afectada de conciliación, reutilizando 882/339 cuando su fuente sea vigente | Pendiente del checkpoint final; sin otra fullsuite rutinaria. |
| Documentación/OpenSpec | Enlaces, reconciliación de tareas, OpenSpec estricto y traceabilidad vigente | Documento preparado; resultados nuevos aún no acreditados. |
| CI técnica | OpenSpec/gobernanza; Python azure-cost-api/backend/processor; frontend lint/test/build y typecheck | No acreditada para el SHA final todavía. Los resultados locales históricos no son CI remota. |
| Política PR | Identificador/rama, plantilla, roles y base develop | Rama local conforme; título y evento PR se comprobarán al publicar por PM. |
| Reviews humanas | Revision JUP-035 y Validacion JUP-035 separadas; hacia develop Comment primero, Approve segundo si ambas satisfechas | Pendientes como gates humanos de merge; no sustituidas por agentes. |

La CI de develop incorpora synthetic-demo:test y synthetic-anomalies:test,
además de la gobernanza existente; estos comandos no se omiten por usar una
definición histórica. CONTRIBUTING enumera jup:check:all, pr:check:test,
ci:check:test, repository:governance:test, openspec:validate, test y build como
checks locales aplicables. Cada equivalencia/reutilización debe indicar recibo,
revisión, entorno y alcance; no hay PASS global otorgado por esta consolidación.

## Casillas históricas y límites de publicación

La [matriz de tareas](../../openspec/changes/archive/2026-10-11-jup-035-conversational-web-interface/task-evidence-reconciliation.md)
mantiene siete casillas amplias abiertas. Sus pendencias de fuente específica
se distinguen de los estados históricos ya superados y de reviews humanas
futuras; no se inventan referencias, pruebas o dispensas.

Antes de publicar: terminar editorial/documentación, commit y nuevo checkpoint
PM, revisión/revalidación afectada, comprobaciones aplicables y CI del SHA final,
control independiente y coherencia del borrador. PM resuelve las referencias
históricas no localizadas o eleva una decisión humana explícita. Si la publicación
se realiza con pendientes propios, rige la doble confirmación explícita separada
para su lista concreta; la autorización general de PR no los elimina.
