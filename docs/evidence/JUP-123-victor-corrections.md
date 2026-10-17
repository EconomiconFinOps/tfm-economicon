# JUP-123: correcciones de la revisión de Víctor en PR140

Fecha de comprobación: 2026-10-17. Base del delta: `4c833e1dee2eda624e5a1e4eb565f82f88f0cf21`.
[Revisión de origen](https://github.com/EconomiconFinOps/tfm-economicon/pull/140#pullrequestreview-5559901207).
Los resultados de esta corrección no reetiquetan la N5 histórica de f3ec760d.

## 1. Trabajo acotado antes de admitir el contexto

`quantities()` admite como máximo 512 candidatos antes de analizarlos, también
cuando son repetidos, cardinales, demasiado grandes o de precisión rechazada.
Con 513 devuelve un catálogo vacío completo; no conserva una selección parcial.
Mantiene el límite independiente de 128 cantidades distintas. La regla se aplica
también con `explicit_only=True` y las dos copias son idénticas.

El tope se escogió después de reproducir el recorrido real
`BackendChatResources.count_messages`, que compila el catálogo antes de aplicar
el presupuesto. Se acotan además las búsquedas de prefijos al ancho máximo de
una unidad y las etiquetas a su entrada y longitud admitida. Los separadores
se localizan directamente, sin construir otra vez todas las entradas precedentes.
Esto evita también retroceso adversario con un solo número y muchos espacios;
los matches de prefijo conservan su span en el texto original.

Comprobación propia en Windows con tokenizer 0.22.1: por servicio, 3.000 preguntas
deterministas × ambos modos (6.000 comparaciones), las 140 preguntas completas
realmente enviadas y variantes de todas las unidades/prefijos con espacios,
tabulaciones y saltos. Catálogos idénticos dentro del alcance admitido.
Sesenta sondas por servicio en doce familias hasta 16.384 caracteres, incluyendo
512 candidatos con líneas vacías y prefijos de un solo número con 16.000 espacios:
máximo backend 0,732 s y processor 0,615 s en esta ejecución. Son sondas locales,
no una garantía universal de latencia ni una prueba de carga.

## 2. Índice ADR

La fila de Grafana vuelve a enlazar `ADR-0022-assistant-evaluation-results-in-grafana.md`,
cuyo destino existe. El ADR del modelo sigue numerado 0023.

## 3. Contrato y tareas OpenSpec

La especificación consolidada y el delta de `jup-035-auto-documentation` describen
`server-documentation-v4`: consulta derivada por el servidor, una recuperación
autenticada, plan privado de hasta 1.000 tokens y final de hasta 2.200; plazo común,
uso de ambas fases y rechazo de llamadas nativas del proveedor. Se elimina la
contradicción de una sola generación y se conserva una sola respuesta pública.

Se reconcilian las casillas técnicas ejecutadas y se conservan las pendientes
de aceptación, proveedor real/navegador y dictámenes. La lista de JUP-123 distingue
la medición histórica y el nuevo delta, sin repetir cortes antiguos como estados
actuales. El usuario autorizó expresamente el archivo técnico con la respuesta
«Tienes autorizacion para registrar la excepcion y seguir procediendo» en este
chat `01a143ae-b740-7043-aedb-1a8a65b4b585`. Autoridad y límites quedan en las tareas
archivadas: no completa aceptación, reviews, navegador, campañas ni autoriza merge.

Los changes están archivados técnicamente como
`2026-10-17-jup-123-chat-semantic` y `2026-10-17-jup-035-auto-documentation`.
El segundo conserva **11 tareas abiertas de 43** y las declara como pendientes,
sin transformarlas en PASS. Su requisito de evidencia ya presente se reconcilió
como MODIFIED; se conservó el escenario previo de llamadas nativas, adaptado al
rechazo de cualquier llamada del proveedor en v4. Enlaces relativos reconciliados.

## 4. Procedencia real de la N5

[Auditoría por operación y fase](JUP-123-n5-request-provenance.json) y
[configuración sin secretos](JUP-123-n5-gateway.sanitized.json).

| Evidencia | Hecho y límite |
| --- | --- |
| Fuente processor f3ec760d, SHA256 `071c50c295de2bb16af7d954c5aff114675cb4dfd3e41bd60ad9641beda16273` | Forwarding `reasoning={effort: high, exclude: true}`, `provider.order=[deepinfra/fp4]`, temperatura 0. No se cambia para fabricar igualdad retrospectiva. |
| Configuración del gateway aislado, SHA256 `592674dfeaf2ec184ba580af99a820226c327bd1f920c59297bb721d3a4b3044` | DeepSeek V4.1 Flash; `provider.only=[deepinfra/fp8]`, ZDR, deny, sin fallback; `reasoning.enabled=false`. Original identificado en el JSON de procedencia; la copia elimina credenciales. |
| 140 recibos correlacionados con las vistas congeladas | 136 operaciones con un intento, dos con dos y dos con tres. No son 140 peticiones HTTP. |
| Comprobantes de uso | 289 hashes de fase observados (145 draft, 144 final), incluidos intentos previos. 139 operaciones tienen informe de su intento final; 008-r5 no lo tiene. Se conserva esa ausencia. |
| Información no capturada | Los cuerpos HTTP upstream y la combinación efectiva de campos tras LiteLLM; el proveedor/precisión efectiva y razonamiento interno no están observados independientemente. `exclude` no demuestra desactivación del razonamiento. |

El gateway de ejemplo versionado sigue siendo GLM/FP4 y **el repositorio por sí
solo no reproduce la N5**. El ADR-0023, el informe y la descripción de PR se
reconcilian con estos límites. CoreWeave es antecedente, no la configuración del
gateway final. Los 497 archivos congelados se verificaron sin modificarlos;
manifest SHA256 `4838711dac437ce7f63f5e68aa382dc9e8dd0343c4e8f3024579d39346c32984`.
El desajuste entre capas se debe a que los campos de processor están fijados en
su código y el operador cambió la configuración del gateway aislado, conservando
esa fuente del producto. No se presenta una precedencia de LiteLLM no observada
como prueba del payload upstream. No se han cambiado ledger, reservas, claves
ni contadores, ni ejecutado inferencias.

## 5. Barreras y sensibilidad de las pruebas

`test_chat_guards_jup123.py` comprueba unidades en subtract, relative_change y
compare, el buffer exacto de 16.384 y su primer exceso, magnitud 1e12 y su exceso,
12 decimales y el decimotercero, tasa diaria frente a total, fronteras inclusivas
y exclusivas y el código propio de división por cero. Son casos adaptados de las
sondas propuestas por Víctor, con atribución a su revisión.

`test_chat_shared_modules_jup123.py` compara todos los módulos chat compartidos,
y detecta también nombres ausentes en una copia. Excluye `chat_resources.py`,
que empaqueta/verifica recursos de servicio diferentes, y permite únicamente
`chat_admission.py` como exclusivo de processor por su gate de concurrencia.

Contrafactuales finales en copia temporal: **16/16 detectados**, incluyendo nueve
guardas de la revisión, la frontera superior inclusiva, retirar/relajar el límite
de candidatos, quitar las cotas de prefijos/etiquetas y divergencias sólo en backend
de `chat_missing_spend` y `chat_premises`. Las guardas
se alteraron a la vez en ambas copias para evitar que muriesen sólo por paridad.
Baseline y restauración: **34/34 PASS**. Hashes del checkout originales intactos;
temporales retirados. No se mutó el árbol de trabajo ni el paquete histórico.

La prueba del esquema de ahorro exige ahora la forma normalizada cerrada exacta,
además de los positivos/negativos anteriores; ya no basta con dos rechazos elegidos.

## Notas no bloqueantes: disposición

| Nota | Disposición |
| --- | --- |
| Escaneo de política por tenant sin índice | Se conserva el alcance MVP. Los tiempos comunicados son de Víctor en pgvector real, no una ejecución propia nueva. No se cambia SQL ni arquitectura; optimización pendiente de priorización. |
| Historial y tokenizer eliminado | Squash recomendado al custodio de merge para evitar trasladar el historial de 253 commits. Esta corrección no reescribe historia ni fusiona. |
| Prueba de esquema más débil | Corregida con igualdad de la forma normalizada cerrada de `answer`. |
| Legibilidad y continuidad extensa | Tareas de JUP-123 reducidas a estado trazable con espacios y enlaces; no se reescribe masivamente la historia ni evidencia original. |
| Cifras N5 del banco conocido | Se conservan como cobertura local del banco utilizado durante desarrollo; no calidad general, causalidad ni evaluación ciega. |
| Línea final sobrante | Retirada de `chat-checkpoints-historicos.md`; comprobar con `git diff --check`. |

RF-123-001 sigue **Open**: herramientas de evaluación sin selección CI. La cobertura
pgvector real también se ejecuta fuera de CI; `Chat engineering SQL` cubre
CockroachDB, no pgvector. La revisión de Víctor aporta evidencia nativa pgvector
con fecha/SHA propios, no una ejecución nueva de este delta. No se cierra el
finding ni se amplía el pipeline.

## Reproducción y estado de verificación

Desde `apps/processor`:

```sh
python -m pytest tests/test_chat_guards_jup123.py tests/test_chat_quantity_work_jup123.py tests/test_chat_shared_modules_jup123.py tests/test_chat_savings_realization_jup123.py -q
```

Ejecución focal final Windows: **78 PASS**. Linux/Python 3.12.13: **174 processor
+ 1 backend PASS**, con fuente comprobada por hash, tokenizer 0.22.1 y sin red
ni servicios de datos. Son selecciones solapadas, no se suman como pruebas únicas.
OpenSpec estricto: **77/77** después de archivar dos changes y añadir una spec;
trazabilidad e higiene se comprueban antes de publicar.

La pasada amplia previa al último ajuste de búsqueda se conserva por su identidad:
Linux 698 backend/1399 processor PASS con 52/6 SKIP; Windows 696/1397 PASS y dos
fallos de privilegio symlink por servicio. No se atribuye esa pasada amplia al
código final ni se convierten omisiones SQL/pgvector en pruebas cubiertas. La CI
posterior comprobará las suites completas sobre el commit publicado.

Arneses y resultados extensos fuera de Git en
`materiales/07-evidencias/JUP-123-collector/PR140-victor-20261017/`, respecto al
workspace coordinador: `mutation-check-final.py` / `final-mutations.json`,
`verify-quantity-work-final.py` / `quantity-work-final-{backend,processor}.json`,
`windows-final.json/.log/.xml`, `linux-resumed-final.json` y logs por lote.
Los arneses iniciales fallidos y el corte PAUSED permanecen; no son resultados
PASS. El paquete por SHA y los enlaces de CI se publican en la conversación de
PR140. No hay nueva campaña ni medición con proveedor real del código corregido.
