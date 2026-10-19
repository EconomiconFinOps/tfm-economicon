# Memoria: solución de IA

Corte documental: 2026-10-19. JUP-063, base `f444ba11e38203b6cfd645a098fd9946d55955e3`.
[Estado y responsables en Trello](https://trello.com/c/sRKGpYEy).

Los apartados e/g aprobados e incorporados al documento colaborativo contienen
28 párrafos, dos tablas y un diagrama. La memoria y sus extractos no se guardan
en Git. [Evidencia, cobertura, hashes y límites](../evidence/JUP-063-validation.md).

La preparación describe ingesta, chunking, embeddings, recuperación híbrida,
chat y expresiones verificadas. Separa capacidades del código, activación por
tenant, datos sintéticos y mediciones de RAG/modelos. Conserva fallos y campañas
parciales; no convierte valoración de Agente en aprobación humana.

El extracto fechado de e/g está bajo custodia externa en
`materiales/06-entregables/JUP-063-2026-10-19-eg/`. PDF local de cinco páginas,
no exportación nativa ni prueba del límite global de 20 páginas.

Guion oficial leído en su referencia suministrada: cobertura de entregables,
requisitos técnicos/funcionales y evaluación contrastada.

Primer candidato: revisión local REVIEW_PASS (19/10/2026 18:26:00, Canarias),
SHA-256 `f6ca921acdcfa2dff1d7f353c608582d9d5ce90b09817ec28f607b72ee76ada8`;
validación local VALIDATION_PASS (19/10/2026 18:29:19),
SHA-256 `56352f6c86e259404eaaa1744fa4046fcbe2d9423ab2f530cf152a4800912152`.
Retorno confirmado por coordinación sobre las referencias originales. Estos
dictámenes no son aceptación humana. Adendas r2 favorables del 19/10:
revisión 18:42:49, SHA `fce15c52851b12623c3e90238ba83cbb292ae00e5f2d08cd75ae5938f59e0653`;
validación 18:42:42, SHA `d06d759a7fc34fdd4524aa9379d4108adaf828e901372fbd3a6bcc8cfe7febb9`.
Cubren sus huellas exactas; no se atribuyen a esta actualización posterior.

La evidencia incluye los cinco criterios exactos de Trello y separa lo local
de lo pendiente en fuentes oficiales. Pairing: NO_ACREDITADO. Coordinación
comprobó por orden de Paris el PDF nativo actual: 18 páginas, incluidas portada,
índice y fuentes; SHA `a359b74a855a13e9ac8dc7b0dc42444a7fda6a6411cb0d81fe06a86ae25f15b4`.
Cumple el máximo de 20 en este corte, no acredita una extensión final:
«c y h siguen pendientes; i está parcialmente redactado». El índice global
requiere actualización final. Observación aprobada adicional:
«d describe una versión antigua del chat que debe armonizarse con e/g».
No se corrigen esos apartados. Presentación Grafana local comprobada por el PM,
sin nuevas mediciones ni evaluación semántica.

Paris autoriza el cierre de esta entrega e/g y una PR nueva, sin tocar PR #141.
Persisten comentarios humanos Doc/Trello con fecha/hash, reviews humanas
y versión final revisada; no se atribuyen esas participaciones.
La PR revisada/vinculada y sus reviews humanas son hitos de PR/merge, no
requisitos anteriores a abrir la primera PR. El archivo requiere autorización
específica y corresponde antes de las reviews según CONTRIBUTING.

El change
[jup-063-ai-memory](../../openspec/changes/archive/2026-10-19-jup-063-ai-memory/proposal.md)
se archivó el 19/10 con autorización expresa de Paris para esta entrega.
Se promovió la especificación ai-memory sin cambiar sus requisitos.
Archivo no equivale a aceptación humana ni cierre de JUP-063.
No hay cambios de producto ni nuevas llamadas a modelos.

La [comparación del 16/10](../evidence/JUP-063-model-selection.md) y su PR #141
conservan su historia independiente. La PR #95 cerrada sin integrar no acredita
el cierre actual.
