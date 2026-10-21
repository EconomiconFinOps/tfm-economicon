# JUP-129 — Evidencia de la composición de evaluación

21/10/2026. [Trello](https://trello.com/c/07J4M5ZN). [OpenSpec](../../openspec/changes/jup-129-grafana-evaluation-composition/). Base `bc94a4daea98e97b574d00f019d347fc61c2f915`. Implementación local autorizada, sin publicar ni archivar. Proceso `CONTRIBUTING.md` 2026-10-18; Paris liderazgo, Lucía pairing, Alejandro revisión y Víctor validación. Estos roles no acreditan participación realizada.

## Criterios y evidencia

| Criterio | Evidencia | Estado |
| --- | --- | --- |
| Revisar los dos dashboards y agrupar cuatro familias | Diseño, JSON nativo, guía: core, recuperación, rendimiento y conversación/usuario, con lo no medido declarado | Implementado; evaluación independiente pendiente |
| Hilo narrativo completo | Resultado de una campaña, diagnóstico, recuperación, modelos y secundarios plegados | Nueve capturas iniciales y dos del Compose general verificadas |
| Métricas explicadas, límites y cambio respecto a referencia | Ayudas/captions, denominadores, fechas y estado de comparación; igualdad exacta/aumento/disminución sin causalidad | 14 pruebas focales PASS con PostgreSQL real |
| Comparar dos versiones | Pareja explícita: distinta, fechada, anterior, misma fuente y clave; incompatibilidad no es mejora | Casos compatibles, incompatibles, misma/ausente/posterior referencia probados |
| Lectura de una persona ajena | Guion siguiente; ninguna persona ni respuesta atribuida a agentes | **NO VALIDADO: requiere participación humana real** |
| Guía y continuidad, antes/después | Guía y continuidad actualizadas; capturas antes/después y comparación incorporadas | Preparado; revisión independiente pendiente |

## Datos y límites

La base real carga 8 ejecuciones/308 filas; no incluye JUP-071 experimental ni el suplemento de comparación de modelos. Se usa además una proyección separada verificada de 10 ejecuciones/462 filas para comprobar compatibilidad y representación del experimento. No se incorpora su instrumento, fixtures, adaptadores o métricas al producto ni se presenta esa proyección como dataset por defecto. No hay inferencias o campañas nuevas.

La composición aprobada de presentación se conserva fuera del repositorio: JSON SHA256 `a5b9d90b4aa35d0ed7ece44ce15926f21390bb4e3bc468ca4ddd62fd72cc8927`; manifiesto `9528d1a8c32f73c8dd6930f1d9fbcb4c5442e4e58d457a50689c32f5afcedcd5`. No es una captura del producto. Las capturas de producto se obtienen del JSON del candidato.

## Guion para la prueba de lectura externa

Una persona que no conocía los dashboards recibe únicamente la vista y un máximo orientativo de cinco minutos. Registrar fecha, consentimiento para atribución o identificador anónimo acordado, conocimiento previo declarado, versión/vista de datos, tiempo aproximado y sus respuestas literales:

1. ¿Se puede afirmar que el RAG funciona bien? ¿Qué dato y qué límite sostienen tu respuesta?
2. ¿Qué familia o parte falla, y qué queda sin medir?
3. ¿La última versión es mejor o peor que la referencia? ¿Hay una pareja comparable?

No sugerir respuestas antes de registrarlas. Esperado en la proyección experimental: reconocer 7/29 favorables provisionales, 17 fallos y cinco sin medir; separar cifras/cobertura y conversación proxy de fidelidad o usuarios reales no validados; no deducir mejora de cohortes incompatibles ni del coste/tiempo. Registrar también dudas y errores de interpretación. Si no se realizó, conservar el criterio pendiente y trasladar al PM; una respuesta de agente no cuenta.

## Capturas del candidato

Todas son Grafana real provisionado desde los archivos del candidato. La comparación de forma antes/después usa la misma base de ocho ejecuciones, sin confundirla con el experimento adicional. La pantalla técnica carece de tráfico en este entorno aislado; no se inventaron series.

- Antes: [evaluación original](JUP-129/antes-evaluacion-base.png) y [métricas técnicas](JUP-129/antes-tecnica-sin-trafico.png).
- Después sobre la **misma base**: [portada de plantilla](JUP-129/despues-base-general.png), identificada como prueba sin calidad de generación, sin campaña experimental ficticia.
- Después con **proyección experimental separada**: [general](JUP-129/despues-experimental-01-general.png), [diagnóstico](JUP-129/despues-experimental-02-robustez.png), [recuperación/calibración](JUP-129/despues-experimental-03-recuperacion.png), [modelos](JUP-129/despues-experimental-04-modelos.png) y [secundarios desplegados](JUP-129/despues-experimental-05-secundarios.png).
- [Pareja no comparable](JUP-129/despues-no-comparable.png): selección real en el navegador, sin inferir mejora entre contextos distintos.

## Comprobaciones y matriz de CI

Registros completos y recibos originales custodiados fuera del producto; no se incorporan entornos, credenciales o logs masivos. No hay CI remota nueva ni publicación. Las pruebas se ejecutaron con herramientas declaradas; entorno Python 3.12 propio y recursos offline verificados, sin inferencias.

| Comprobación local / job relacionado | Resultado y límite |
| --- | --- |
| Composición focal nueva | **14 PASS**, PostgreSQL 17.11 real; casos con rollback, rol lector, valores nulos/cero, aislamiento, escape, compatibilidad y salud |
| Integración del candidato | **25 consultas de panel por cada proyección**, más cuatro consultas de selector, todas con inicio de sesión real del lector; 8/308 y 10/462 conciliados; JSON y variables efectivamente provisionados idénticos al candidato |
| Permisos lector | SELECT permitido; INSERT y CREATE en esquema denegados por privilegios efectivos; sin cambios en el contrato de permisos de producto |
| Salud Prometheus | **5 consultas válidas**, Prometheus 2.55.1 real sin targets, cero series disponibles; no se presenta como tráfico medido |
| `corepack pnpm build` | **PASS**, cuatro tareas; frontend compilado. Repetición con entorno 3.12 usa caché declarada de Turbo; no se presenta como una segunda compilación independiente |
| `pr:check:test`, `ci:check:test`, `repository:governance:test` | **PASS**; no se modifican políticas o workflows |
| `jup:check:all`, `openspec:validate`, `jup:cleanup:check` | **PASS final** tras completar el metadato OpenSpec; trazabilidad de 11 cambios, validación estricta e higiene |
| `evaluation-dashboard:test` — original Windows | Con Python 3.12: **1.679 pruebas ejecutadas, 216 errores de infraestructura, 1 omitida**, sin fallos de aserción. Docker Linux no arranca: falta el pipe de Docker Desktop. La batería general no está verde; no se cambian helpers para forzar PASS. Las consultas nuevas se cubren además en PostgreSQL nativo |
| `corepack pnpm test` — original Windows | La ejecución completa usa `pnpm run test --env-mode=loose --continue=always` para propagar el recurso offline y terminar todos los servicios. Frontend **1.380 PASS**. Azure **80 PASS / 1 FAIL** temporal. Processor **2.534 PASS / 69 FAIL / 144 SKIP**. Backend **2.428 PASS / 147 FAIL / 370 SKIP**. Sin cambios en esos servicios; no se afirma que todos los fallos tengan la misma causa |
| Linux / Docker / CI remota | Ubuntu WSL2 e integración Docker existentes autorizados expresamente. Regresión Linux y arranque del Compose general ejecutados con los resultados siguientes; **no es un PASS integral ni CI remota nueva** |
| Lectura externa y reviews humanas | **Pendientes**, no sustituidas por pruebas automatizadas |

Los primeros intentos se conservan: Python 3.10 causó errores de fechas ISO con Z y faltaban dependencias; se resolvió la preparación con Python 3.12 y requisitos declarados. Turbo estricto no propagaba el archivo de tokenización externo; se usó su opción de entorno documentada. El temporal compartido de pytest devolvía WinError5; se pasó a un temporal propio. Persisten ejemplos de WinError1314 para symlinks, un umbral temporal de Azure y fallos de protocolos/dobles en servicios no modificados. No se reparan ni reducen pruebas ajenas unilateralmente. La limitación y alternativas se elevaron al PM antes del cierre, conservando los resultados originales.

## Evaluación y publicación

Revisión y validación independientes todavía no lanzadas: antes se fijará candidato y el PM conservará sus referencias originales. La prueba humana, pairing y reviews humanas no se sustituyen. Sin autorización de archivo, commit, push, PR o merge.

## Regresión Linux y arranque general — 21/10/2026

Tras la espera inicial, Paris autorizó Ubuntu WSL2 y la integración Docker ya existentes, con recursos privados y sin instalaciones globales ni cambios de configuración. Se usaron Python 3.12.15, Node 22 y dependencias declaradas. La base permanece en `bc94a4d`; el avance posterior de develop no se incorpora durante estas comprobaciones.

| Comprobación | Resultado conservado |
| --- | --- |
| PostgreSQL y rutas WSL | Consulta real por localhost y lectura exacta del montaje temporal: **PASS**; recurso desechable retirado |
| Evaluación completa Linux | **1.890 pruebas: 1.886 PASS, 4 FAIL, 0 SKIP**. Los cuatro fallos son los casos promtool de `test_evaluation_readability_section_c.py`, que no pueden leer el archivo temporal; siguen siendo FAIL en esta batería |
| Discriminante focal promtool | UID del contenedor 65534 frente a propietario 1000. El mismo YAML con las cuatro situaciones falla con directorio 700; pasa con UID 1000 o directorio 755. No se cambian pruebas ni helpers y estos ensayos no sustituyen el resultado original |
| Frontend Linux | **1.380 PASS**, 92 archivos |
| Azure Linux | **81 PASS** |
| Processor Linux, batería completa | **2.599 PASS, 4 FAIL, 144 SKIP**. Fallan OCR de PDF scanned/mixed/hybrid y extracción de DOC. Se conserva la ejecución original |
| Processor, reevaluación focal autorizada | **4 PASS** sobre los mismos cuatro casos y fuentes de solo lectura, en imagen Linux propia con usuario 1000 y red desactivada. El worker usa un PATH fijo que excluye las herramientas privadas de Ubuntu; en la imagen existen en las rutas esperadas. Sin cambios de código, tests o host. No es otra ejecución completa del workspace |
| Backend Linux, continuación | La interrupción deja 2.566 PASS y 327 SKIP registrados. Se ejecutan únicamente los 51 casos pendientes: **10 PASS y 41 SKIP**. Total acreditado: **2.576 PASS, 368 SKIP y un resultado anterior no registrado**, sobre 2.945 casos colectados |
| Límite del registro backend original | Un marcador falta en `test_system_health_boundaries_jup047.py` (54 colectados, 53 resultados visibles antes de avanzar a otros archivos). Colección y registro no permiten identificar inequívocamente el nodeid. En ese corte no se repitieron los 54 ni se inventó PASS |

Los SKIP se conservan como omisiones de las suites y no acreditan sus integraciones opcionales. El primer lanzamiento de Turbo no llegó a ejecutar tests porque no encontraba el binario pnpm; se habilitó únicamente el shim privado y se conservó el intento. Los registros Windows, Linux, interrupción y reensayos se preservan separados. No se declara la batería general en verde ni se acepta deuda por esta evidencia.

### Los tres dashboards en el mismo Grafana

El servicio `grafana` se levantó realmente desde el `docker-compose.yml` general y su provisioning original, con un override temporal limitado a recursos y puertos propios. Se iniciaron Grafana, Prometheus y PostgreSQL para esta comprobación; los demás servicios de aplicación no se arrancaron y no se acredita tráfico de backend o processor.

Los tres UID servidos son `economicon-assistant-evidence`, `economicon-assistant-evaluation` y `economicon-technical-metrics`. Todos constan como provisionados y sus paneles y variables coinciden con los JSON del candidato. Se conservan las datasources `evaluation-postgres` y `prometheus`, ambas operativas. Las **25 SELECT del nuevo dashboard** se ejecutan a través de Grafana y su lector configurado, con SELECT permitido e INSERT/CREATE denegados.

La carga usa el mecanismo existente `tools/evaluation-dashboard.py load`: ocho ejecuciones y 308 filas. Provisionar definiciones no carga campañas automáticamente. No hay importación manual del dashboard, nuevo servidor de producto, nuevos pasos de registro ni cambios de Compose o provisioning.

- [Lista de los tres dashboards en el Compose general](JUP-129/three-dashboards-compose-general.png).
- [Nueva composición servida por ese mismo Grafana](JUP-129/assistant-evidence-compose-general.png).

El proyecto de prueba y su contenedor focal se retiraron tras las capturas: tres contenedores Compose, seis volúmenes y dos redes, con ausencias verificadas. Las ocho entradas de Compose/provisioning/JSON siguen idénticas a las fuentes probadas. Las previsualizaciones anteriores siguen bajo la custodia declarada; no son una propuesta de despliegue separado.

### Corrección y aclaración focal autorizadas — 21/10/2026

Paris autorizó resolver los cuatro fallos de promtool y aclarar backend sin repetir suites completas. Se conserva la batería original y el discriminante anterior. La corrección se limita al ejecutor de fixtures de `TasaDeErrorConPromtoolTests`: directorio temporal 755 y archivos YAML sintéticos 644 explícitos, con montaje de sólo lectura. No cambia consultas, aserciones, imagen, usuario del contenedor, código de producto o permisos de producción.

Los **cuatro tests reales de promtool pasan**, cero omitidos, en 4,084 segundos con umask inicial 077. Este resultado posterior acredita la corrección; los cuatro FAIL de la ejecución original siguen conservados como resultado histórico. No se ejecuta otra vez la batería de 1.890 casos.

El nodeid del marcador histórico de backend sigue sin poder recuperarse inequívocamente. Se ejecuta únicamente `test_system_health_boundaries_jup047.py`, el archivo afectado de 54 casos, con salida individual y JUnit: **54 PASS, cero FAIL y cero SKIP**, en 5,22 segundos. Cada caso se coteja con sus nodeids colectados y todas las fuentes backend siguen idénticas al archivo original. No se modifica backend ni se ejecuta su suite completa.

La reconciliación por nodeid conserva los otros resultados anteriores, reutiliza los 51 casos ya reanudados y sustituye sólo la evidencia del archivo afectado por sus 54 resultados nuevos: **2.577 PASS y 368 SKIP sobre 2.945 casos, sin resultado actual desconocido**. Es cobertura compuesta de las ejecuciones documentadas, no una nueva ejecución completa. El registro histórico incompleto permanece intacto.

### Pendientes de aceptación

Las dos limitaciones técnicas tratadas tienen revalidación focal registrada; se conservan los fallos y la interrupción originales, los SKIP y el reensayo de extracción por separado. No hay CI remota nueva ni se declara un nuevo PASS de una suite completa. La primera revisión y validación independientes terminaron con hallazgos; sus originales se conservan y la reevaluación de las correcciones requiere candidato fijo y controles previos. Lectura externa real, participación y reviews humanas, aprobación final, archivo y publicación siguen pendientes conforme al proceso del proyecto.

### Correcciones de la primera revisión y validación — 21/10/2026

| Hallazgo original | Corrección y comprobación focal propia |
| --- | --- |
| Calibración: k4–k6 podían tomar máximos de otra ejecución bajo el rótulo histórico | El WHERE externo fija toda la matriz al informe declarado. Otra campaña con valor 1 no altera ninguna columna; sin el informe fijado no aparecen filas |
| Facturación: Facturado podía pertenecer a otra ventana | Estimado y Facturado comparten el filtro externo de ejecución. Otra ventana con valor 999 no altera los resultados; sin la fijada ambas magnitudes quedan NULL |
| Tasas HTTP: tráfico sin serie 5xx se mostraba como ausencia | Fallback sólo en numerador para backend y processor. Promtool comprueba cero, 25 %, 100 % y ausencia sin tráfico en las dos expresiones |
| XY: error de renderizado con frames sin campos en la base normal | Agregados sin GROUP BY conservan columnas numéricas NULL; una transformación omite coordenadas ausentes. Una etiqueta oculta de disponibilidad del mismo informe muestra «Sin datos», «Datos parciales» o «Dos observaciones» en el título. No agrega controles visibles, métricas ni coordenadas inventadas |

Se ejecutaron **ocho pruebas focales PASS**. Con el dashboard original, esas regresiones producen seis aserciones fallidas (incluidos dos subcasos XY), conservadas separadamente. Otras **dos pruebas PASS** cubren disponibilidad ausente/parcial/completa y selectores. No se repiten las suites completas ni se modifica backend/processor.

Comprobación real del XY en Grafana 11.3.0 del Compose general, con definiciones servidas iguales al archivo: base 8/308 → «Sin datos», cero puntos y sin Err; proyección opcional 10/462 → dos puntos con coordenadas originales; vuelta por loader existente a 8/308 → «Sin datos» otra vez. Cinco consultas afectadas por fase pasan mediante el lector de Grafana. La etiqueta de modelos describe el informe histórico independiente de la campaña de la portada.

- [XY sin suplemento: ausencia explícita](JUP-129/modelos-sin-datos-corregido.png).
- [XY con suplemento: dos observaciones preservadas](JUP-129/modelos-dos-observaciones-corregido.png).

Los dos primeros intentos visuales eliminaron Err pero dejaban el área vacía sin etiqueta explícita; se completó la disponibilidad visible antes de entregar. El primer intento de recarga base omitió la variable del lector en el ejecutor temporal; se conserva el fallo y el reintento correcto, sin cambio de producto ni servicio compartido. Recursos propios retirados: tres contenedores, seis volúmenes, dos redes y credenciales. No se cargó el suplemento en el manifiesto por defecto ni se ejecutaron campañas nuevas.

Esta evidencia pertenece a la corrección propia. Los dictámenes originales siguen siendo desfavorables y no se extienden al nuevo candidato: corresponde reevaluar lo afectado con roles independientes. Lectura humana **NOT_VALIDATED**, omisiones 368 backend/144 processor y proceso final pendientes.

## Reconciliación con develop — 21/10/2026 (R3)

Paris autoriza retomar sobre el commit publicado `a542e8cb` e integrar exclusivamente `develop` `b7c8b708`. Merge `--no-commit --no-ff`, sin conflictos. Se conserva HEAD a542 hasta el commit del PM. El delta de develop modifica 33 archivos e integra robustez y sus 136 filas; no se incorpora la rama independiente del nuevo modelo. Las cifras 8/308 y resultados anteriores pertenecen a sus candidatos históricos.

La carga normal del loader existente pasa a **9 ejecuciones y 444 filas**. La portada elige la campaña experimental más reciente y muestra 7/29 favorables provisionales, 17/29 fallidos, cinco sin medir y 24/29 puntuables; mantiene una repetición/persona evaluadora y modelo sin verificar. El informe histórico de modelos no entra en default: XY «Sin datos», sin Err ni puntos inventados. Añadir únicamente su suplemento produce 10/462; su comportamiento R2 se reutiliza sólo en la cobertura que confirme cada evaluador.

| Comprobación propia del delta | Resultado |
| --- | --- |
| Composición, manifiesto, carga, conciliación e indicadores | **266 PASS**, cero FAIL/SKIP, 32,771 s, PostgreSQL desechable real; sin repetir la suite de evaluación ni backend/processor/frontend |
| Compose general, Grafana 11.3.0, PostgreSQL 17, Prometheus 2.55.1 | Tres dashboards provisionados del mismo Grafana; paneles/variables servidos coinciden con sus fuentes; carga existente 9/444; **28 consultas 200** entre paneles y variables |
| Navegador sobre default 9/444 | Portada experimental con cifras/limitaciones correctas; sólo Campaña/Referencia visibles; bloque modelos «Sin datos» sin Err/puntos |

- [Portada tras integrar el informe de robustez](JUP-129/portada-reconciliada-default.png).
- [Modelos sin suplemento en el default reconciliado](JUP-129/modelos-reconciliados-default.png).

Evidencia y recursos aislados fuera del producto, sin importación manual ni stack nuevo de producto. La verificación temporal encontró inicialmente una clave opcional ausente en el dashboard técnico; se corrigió sólo ese ejecutor, preservando el intento. La retirada comprobó primero ausencia de los recursos propios y luego listeners: un bind inmediato observó conexiones TIME_WAIT, sin servicio escuchando. No es fallo del producto ni justifica modificar el host. Recibos finales de limpieza conservados en la entrega.

R2 se conserva íntegra: revisión técnica favorable con diez pruebas y validación técnica focal favorable con nueve pruebas y15 consultas; operación CUA por el principal bajo instrucciones, inspección y dictamen del Validador. No son aprobación humana ni se extienden automáticamente al candidato reconciliado. Al fijar esta evidencia faltan nuevas referencias PM y evaluación independiente sólo de lo afectado.

Lectura humana **NOT_VALIDATED**; 368 SKIP backend/144 SKIP processor e históricos conservados. La CI push previa comunicada por PM corresponde a a542 antes de esta integración, no acredita el candidato sin commit. Aprobaciones humanas, archivo y publicación conservan su etapa y permisos.
