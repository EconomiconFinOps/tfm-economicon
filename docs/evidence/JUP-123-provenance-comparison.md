# JUP-123: comparación auditada entre revisiones de procedencia

Fecha: 16/10/2026. Origen: chat `01a1270c-e332-7462-9c90-706d49ade92c`.
Encargo: continuar la implementación de B después del análisis de modelos.

## Cambio y motivo

La N3 de5119 usa el banco1.0.0 y la de a7 el1.0.1. El comparador anterior rechaza
correctamente sus hashes distintos. Faltaba una operación explícita para
comparar las etiquetas originales por requisito sin falsear compatibilidad de
corpus, reescribir hashes o atribuir mediciones antiguas a la versión actual.

`tools/chat-eval-compare-provenance.py` implementa esa operación separada. Sólo
admite cambios en versión/fuentes del banco y la referencia de versión de las
reglas; todo el contenido restante debe ser idéntico. Mantiene la comparación
estricta anterior intacta. El nuevo comando exige informes y auditorías ligados
por hash, criterios originales y juicios ligados a evidencia y respuesta/contexto.
Los fallos técnicos o de verificación, ausencias y pares sin contraparte son
explícitos. Nunca devuelve aceptación automática ni transfiere etiquetas.

La implementación modifica únicamente herramientas/documentación. Las aplicaciones,
prompts, corpus y banco permanecen idénticos a la fuente a7 ya medida. No hay nuevas
inferencias, reservas, claves, builds o cambios de servicios por esta entrega.

## Resultado real offline

| Grupo | Transiciones |
| --- | --- |
| Banco original | 327 PASS→PASS |
| Calidad adicional | 165 PASS→PASS, 2 FAIL→PASS, 1 incierto→PASS |
| Respuestas emparejadas | 84 |
| Muestras ausentes o pares excluidos | 0 |
| Respuestas con regresión observada | 0 |

Los dos criterios FAIL→PASS pertenecen al mismo defecto de012r1; incierto→PASS
corresponde a023r3. Se mantienen los juicios antiguos, incluidos fallo y duda.
Esto compara sistemas que cambian código/corpus/modelo; no atribuye causalidad
ni demuestra generalización, adjudicación independiente o aceptación del equipo.
La N5 de a7 sigue sin ejecutar y sus criterios/alcance siguen pendientes.

Informe externo: `B-N3-5119-to-a7-provenance-comparison-v1.json`, SHA
`4da6964ac124baf635b5f7889d254519d871e0f75cca3519528e7a77eb8a38af`,
en `../materiales/07-evidencias/PR121-local-evaluation/` desde la raíz del proyecto.
Contiene los ocho hashes de entrada y el hash del código del comparador. El
operador `run-B-provenance-comparison-v1.py` conserva el comando exacto.

## Verificación

Doce pruebas nuevas ejercitan cambios semánticos del banco/reglas, juicios
obsoletos, hashes/partición, criterios omitidos o forjados, duplicados, exclusión
de técnicos/evidencia incompleta y regresiones correlacionadas. Diecisiete
pruebas existentes del evaluador estricto pasan. El primer intento del nuevo
conjunto dio11PASS y un error de permisos del temporal de Windows, incluido su
cleanup; no fue un fallo del comparador. El mismo código pasó12/12 al disponer
de acceso normal a su propio temporal. Se conserva ese incidente y los logs
de la pasada completa; no se relajan aserciones por el entorno.

Guía y contrato: [evaluación de recibos](../validation/JUP-035-receipt-evaluation.md)
y [OpenSpec](../../openspec/changes/jup-123-chat-semantic/specs/chat-semantic-evaluation/spec.md).
Los resultados de ingeniería/API/UI previos mantienen su fuente y alcance;
no se presentan como una nueva batería de las aplicaciones.
