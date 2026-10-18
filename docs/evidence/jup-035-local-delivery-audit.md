# Entrega local JUP-035 / PR-121

13/10/2026. Objetivo: paquete local reproducible para reencauzar la PR; no su
aprobación, publicación ni validación con proveedor. Origen: chat
`01a1270c-e332-7462-9c90-706d49ade92c`.

## Entregas

| Rama local | Commit útil | Resultado |
| --- | --- | --- |
| `local/JUP-035-evaluation` | `5a2bc473` | Seis fixtures corregidos sin relajar garantías;38PASS. |
| `local/JUP-035-cd-hmac` | `ba778bb6` | CD/HMAC separado sobre develop `bfaf3983`;16PASS unitarias. |
| `local/JUP-035-evaluation` | `41fdca67` | Scorer offline, rúbrica, partición y11 pruebas PASS. |
| `local/JUP-035-evaluation` | `d83e9f48` | Adjudicación histórica y diagnóstico inicial de suite. |
| `local/JUP-035-evaluation` | `97e8e043` | Cancelación del resumen;90PASS+4socket+3TLS. |
| `local/JUP-035-evaluation` | `5dce752e` | Preparador de planes repetidos, sin inferencias. |

Los checkouts están en `tfm-economicon-jup035-local` y
`tfm-economicon-jup035-cd-local`, hermanos del checkout documental original.
Los tres parches de fixtures/CD/cancelación están también en el directorio
externo de evidencias, `local-patches/`, con hashes. **No son una sola serie**:
CD parte de develop; los otros requieren la base de chat existente.

## Auditoría del objetivo

| Punto | Evidencia y decisión |
| --- | --- |
| 1. Aislar y corregir fixtures | Base exacta `fc0f4697`, rama aislada;38PASS. No se modifica el banco para hacer pasar casos. |
| 2. Separar ingeniería | CD aplicado y probado sobre develop; chat permanece en su base existente, con68PASS backend de operaciones/metadatos. La ausencia del subsistema en develop impide trasladarlo como un parche pequeño. No se decide la base de integración del equipo. |
| Decisión truncada | `551fb81` pertenece a decisión nativa histórica; no aplica a develop sin chat. El flujo actual v4 y sus pruebas se mantienen separados de esa afirmación histórica. |
| 3. Revisar etiquetas/reserva |44 respuestas completas,253 controles,9 inciertos;12 intentos sin respuesta conservados como técnicos. Partición por familias y congelación previa a reserva, sin fingir conjunto ciego independiente. |
| 4. Scorer/rúbrica | Requisitos/hash/evidencia/causalidad separados. Heurísticas numéricas y prohibiciones son indicios, no juicio semántico automático. No hay juez LLM que declarar calibrado. La cobertura, el significado de números y las citas mantienen adjudicación explícita donde no hay garantía automática. |
| 5. Base N=3 | Plan de84 muestras preparado y verificado, **NOT_RUN**. Docker Desktop sin daemon local, WSL sin distribución; contexto Docker apunta al servidor compartido que este objetivo no autoriza modificar/desplegar. No se sustituye el candidato por un runtime anterior ni por replay de respuestas. |
| 6. Cambios semánticos medidos | No ejecutados: falta base repetida del candidato. No se rehace la eliminación de tools de v4 ni se añade otro prompt/router sin medición. Único cambio de producto local: transporte de cancelación de resumen, probado aisladamente. |
| 7. Comparación/N=5 | Comparación histórica N=1 descriptiva reproducible; no prueba mejora causal. Plan N=5 de140 muestras preparado, **NOT_RUN**. No se han consumido las dos iteraciones de cambios semánticos. |
| Coste y límites | Cero nuevas inferencias. Último acumulado confirmado0,957927619USD, tope2USD; ningún plan admite gasto con ese balance histórico sin lectura viva. Sin publicación ni despliegue. |

Las mediciones reales no ejecutables se entregan identificadas, como permite el
objetivo; no se cuentan como pruebas superadas. No hay claim de CI integral verde:
la suite completa inicial tuvo1454PASS/13FAIL/4ERROR/96SKIP. La revisión por grupos
resolvió diez incidencias de dependencias (10PASS) y cinco de cancelación (incluidas
en90PASS). Dos pruebas symlink Windows siguen sin validación local por WinError1314.
No se suman las repeticiones parciales para inventar una nueva fullsuite verde.

## Evidencia reproducible

[Informe detallado](jup-035-local-offline-review.md) y
[comandos/rúbrica](../validation/JUP-035-receipt-evaluation.md).
Directorio externo: `materiales/07-evidencias/PR121-local-evaluation/`, en el
workspace padre. Contiene juicios, recibos, logs, congelación, parches y manifest.

- Plan N=3: `baseline-n3-plan.json`, SHA256
  `f34082487290f78a81af60fb04d23072e211f3128a30282872844466fb40beee`.
- Plan N=5: `confirmation-n5-plan.json`, SHA256
  `9fba7b60659449f0dcaceb5e49e1703fbfa9bed61e0546c3dcb6fcf447a13cfb`.
- Ambos verifican304 archivos y todas sus entradas contra el banco original;
  registran commit `5dce752e94e5d89574e4bbfc59ec09f418d7a902` y conservan NOT_RUN.
- `completion-audit-provenance.json` comprueba la referencia congelada. La
  partición tiene CRLF en Windows y LF en Git: se verificó el contenido exacto
  reconstruyendo esa conversión; no se ocultó la primera discrepancia de bytes.
- El hash del corpus coincide en3/3 documentos. El diff de producto frente a
  `fc0f469` sólo contiene `apps/processor/app/clients/summary_gateway.py`.

## Decisiones para la siguiente fase

El equipo debe acordar la base del chat y los criterios de aceptación. Cuando
haya entorno aislado autorizado, se ejecutarán las campañas preparadas con
contabilidad viva, procedencia completa y adaptación del colector al API actual;
el scorer histórico no es ese colector. Las dudas semánticas requieren un segundo
juicio independiente, no otro parche para subir la puntuación. Sólo entonces se
compararán cambios de arquitectura. PR-121 sigue sin aceptación demostrada por
este paquete; la review oficial y su estado remoto no se alteran.
