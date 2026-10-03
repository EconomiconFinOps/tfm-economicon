## 1. Preparacion y dependencias

- [ ] 1.1 Comprobar en `develop` el estado de JUP-023 (cliente del processor), JUP-021 (vigilancia de dimension) y JUP-025 (reescritura de `search_chunks` y de la ruta del asistente); aplicar el codigo despues de JUP-025 o coordinar la rama, y anotar en `design.md` lo que se encuentre.
- [x] 1.2 Fijar con tests el comportamiento actual de `search_chunks` (4 resultados, sin umbral, orden por distancia) para detectar cambios no previstos al refactorizar.

## 2. Configuracion y secretos del backend

- [x] 2.1 RED: tests de configuracion para proveedor, alias, URL del gateway, clave virtual (`SecretStr`, sin valor por defecto), tiempo maximo, reintentos, `top_k` y distancia maxima: rangos validos e invalidos, `mock` fuera de `development` y `test`, `litellm` sin clave; comprobar que fallan.
- [x] 2.2 GREEN: implementar la configuracion; variables nuevas en `docker-compose.yml`, `.env.example` (clave vacia), README y tests de topologia.
- [x] 2.3 Test con un valor centinela: la clave no aparece en logs, `repr`, mensajes de error ni respuestas.
- [x] 2.4 RED y GREEN: una linea de log al arrancar con proveedor, alias y dimension activos (sin la clave), con test para los dos proveedores.

## 3. Proveedor de embeddings de la consulta

- [x] 3.1 RED: tests del proveedor `litellm` del backend contra un upstream simulado local: exito, forma incorrecta, valor no finito, longitud distinta, mas de un vector, redireccion, reintentos acotados solo en fallos transitorios y categorias de error.
- [x] 3.2 GREEN: implementar el proveedor con biblioteca estandar, sin seguir redirecciones y con las mismas categorias que el processor.
- [x] 3.3 Proveedor determinista de pruebas (vector por palabra normalizada, suma y normalizacion) con tests de similitud por palabras compartidas y de determinismo.
- [x] 3.4 Prueba de paridad backend y processor sobre alias, dimension y categorias de error; comprobar que falla si uno cambia solo.

## 4. Contrato de recuperacion

- [x] 4.1 RED: tests de `top_k`, distancia maxima, orden por distancia y despues por identificador con empates en el mismo y en distinto documento, resultado vacio (tenant sin documentos y todo fuera del umbral), `top_k` mayor que los disponibles combinado con umbral, y aislamiento por tenant con un fragmento mas cercano de otro tenant.
- [x] 4.2 GREEN: implementar el filtro, el orden y el resultado vacio en `search_chunks`, y el estado sin contexto en el asistente.
- [x] 4.3 Ejecutar con pgvector real y opt-in (`*_TEST_URL`) los tests de orden y de umbral, y registrar el resultado en la evidencia.
- [x] 4.4 Mutantes sobre el codigo tocado (quitar el desempate, invertir la comparacion del umbral, quitar el filtro de tenant): cada uno debe hacer fallar algun test.

## 5. Compatibilidad y fallos

- [x] 5.1 RED y GREEN: comparar al arrancar la dimension de la columna con la del proveedor (mensaje fijo que indica reindexar), verificar la longitud del vector de la pregunta antes de buscar y filtrar por `provider`; test de indice mixto.
- [x] 5.2 RED y GREEN: traducir los fallos del proveedor y del almacen en un 503 con cuerpo fijo; cubrir autenticacion, limite de tasa, tiempo agotado, base no disponible y la combinacion fallo mas tenant vacio.

## 6. Trazabilidad

- [ ] 6.1 Evento estructurado por recuperacion y contadores con etiquetas acotadas; tests de que no contiene la pregunta ni el contenido y de que las etiquetas salen de un conjunto fijo.

## 7. Calibracion

- [x] 7.1 RED y GREEN: validador del fichero de etiquetas que reutiliza `digest` del validador del banco (caso desconocido o sin etiquetar, fuente no declarada, encabezado inexistente o ambiguo, huella cambiada, etiqueta duplicada, cobertura incoherente, finales de linea, banco intacto), con script en `package.json`, paso en la CI y su registro en `tools/ci-workflow.test.mjs`.
- [x] 7.2 Redactar las etiquetas por seccion de las 28 preguntas en `docs/validation/` como borrador y dejarlas revisadas por Lucia.
- [x] 7.3 Script de calibracion en dos fases, en memoria (misma funcion y parametros de troceado que la ingesta, distancia coseno propia, sin conexion a base de datos), con tope de llamadas, ejecucion explicita, sin secretos en las salidas y probado con un proveedor simulado; test de que la distancia coincide con la de pgvector dentro de una tolerancia.
- [x] 7.4 Ejecutar la calibracion con el modelo real, versionar el JSON y el informe en `docs/spikes/` y fijar `top_k` y la distancia maxima por defecto en un punto del barrido, con la regla de seleccion escrita.

## 8. Documentacion y decisiones

- [x] 8.1 Registrar el ADR del embedding de la consulta con clave propia en el backend (enlaza ADR-0002 y ADR-0006), con su numero asignado al crearlo, y enlazarlo desde `design.md`.
- [x] 8.2 Actualizar `docs/architecture.md`, el README del backend y el runbook con la guia de reindexado a `vector(1536)`; registrar en el backlog el finding de cambio de modelo con la misma dimension.

## 9. Cierre y verificacion

- [ ] 9.1 Bateria completa: tests del backend y del processor, tests de `tools/` y de la CI, `openspec:validate`, `jup:check`, `jup:cleanup:check`; registrar comandos y resultados.
- [ ] 9.2 Revision adversarial con el agente `adversarial-reviewer` hasta veredicto `accept`, o findings restantes aceptados explicitamente por Lucia.
- [ ] 9.3 `review.md` con resumen, decisiones, validacion, pasadas adversariales, barrido de patrones, riesgos, findings y aplicabilidad de ADR.
- [ ] 9.4 `docs/evidence/JUP-022-validation.md` con los comandos y resultados, incluida la calibracion real.
- [ ] 9.5 Bloque `## Human Approval` en `review.md` tras la aprobacion explicita de Lucia.
- [ ] 9.6 Archivar el change en la misma rama.
- [ ] 9.7 Abrir el PR hacia `develop`.
