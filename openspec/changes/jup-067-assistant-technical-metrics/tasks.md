## 1. Preparacion

- [ ] 1.1 Comprobar en `develop` el estado de los PR #67 (JUP-022, etiquetas y calibracion), #55 (JUP-025, citas) y de la generacion de respuesta con modelo, y anotar en `design.md` que dato existe y cual no.
- [ ] 1.2 Leer la bateria JUP-069, su validador y el protocolo de `docs/validation/README.md` para reutilizar estados, rubricas y el normalizado CRLF a LF; no modificar la bateria ni las etiquetas.

## 2. Catalogo de metricas

- [ ] 2.1 RED: pruebas del validador del catalogo (campos obligatorios, identificadores unicos, familias permitidas, version, una metrica calculada que falta en el catalogo y al reves).
- [ ] 2.2 GREEN: `docs/validation/JUP-067-metrics-catalogue.json` con ACC-1 a 3, REL-1 a 4, GRD-1 a 3, LAT-1 a 4, STR-1 y 2 y AVL-1, y el validador.
- [ ] 2.3 Documento `docs/validation/JUP-067-metrics.md` con el por que de cada familia, la tabla de origen de los datos y las limitaciones de la muestra.

## 3. Formato de resultados

- [ ] 3.1 RED: pruebas del validador de resultados (campos y estados, campos prohibidos por nombre sin imprimir el valor, caso desconocido, hash de la bateria distinto, categoria de fallo fuera del conjunto fijo, comprobaciones juzgadas sin `decided_by`).
- [ ] 3.2 GREEN: validador de resultados y ficheros de ejemplo sinteticos, marcados como tales, en `tools/fixtures/assistant-metrics/`.

## 4. Calculo

- [ ] 4.1 RED y GREEN: poblaciones y estados (`blocked` y `not_run` fuera de los denominadores y contados), grupos `answer`, `clarify` y `abstain` separados, tasa como `k de n` con intervalo de Wilson, con valores calculados a mano.
- [ ] 4.2 RED y GREEN: exactitud (todos los `required`, ningun `forbidden`, `numbers` con tolerancia absoluta, unidad y etiqueta), tasa objetiva y juzgada por separado.
- [ ] 4.3 RED y GREEN: relevancia (acierto de documento y de seccion, cobertura `none` fuera y listada, vacios, condiciones de medicion en el informe) y confianza REL-4 (similitud = 1 menos distancia, mediana y cuartiles, vacios fuera, marca de proveedor `mock`, valores calculados a mano).
- [ ] 4.4 RED y GREEN: fundamento (citas validas, cifras sin rastro y casos criticos, integridad de referencias de evidencia).
- [ ] 4.5 RED y GREEN: latencia (rango mas cercano, minimo de observaciones, fallos aparte, etiqueta de llamadas correctas).
- [ ] 4.6 RED y GREEN: robustez (respuestas que cumplen el esquema, fallos por categoria) y disponibilidad AVL-1 (errores 5xx frente a 4xx, intervalo de Wilson, ejecucion sin peticiones como no disponible).
- [ ] 4.7 RED y GREEN: objetivos provisionales junto a cada valor con su origen, sin veredicto de aceptacion.
- [ ] 4.8 RED y GREEN: tamano del corpus en la cabecera y junto a la latencia del informe; informe JSON y Markdown, determinismo con `--generated-at`, ausencia de red y de texto sensible, errores que nombran el campo y no el valor.
- [ ] 4.9 Mutantes sobre el calculador (denominador, estado `blocked`, extremos del intervalo, percentil, tolerancia, grupo `clarify`, similitud con signo cambiado, 4xx contado como error del servidor) y controles negativos; cada uno debe hacer fallar alguna prueba.

## 5. Integracion

- [ ] 5.1 Script `assistant-metrics:test` en `package.json`, paso en la CI y entrada en `tools/ci-workflow.test.mjs`.
- [ ] 5.2 Ejemplo trabajado en el documento con los ficheros sinteticos; dejar anotado que el ejemplo con la calibracion real de JUP-022 se anade cuando #67 este en `develop`.

## 6. Cierre y verificacion

- [ ] 6.1 Bateria completa: pruebas de herramientas y de la CI, `openspec:validate`, `jup:check`, `jup:cleanup:check`; registrar comandos y resultados.
- [ ] 6.2 Revision adversarial con el agente `adversarial-reviewer` hasta veredicto `accept`, o findings restantes aceptados explicitamente por Lucia.
- [ ] 6.3 `review.md` con resumen, decisiones, validacion, pasadas adversariales, barrido de patrones, riesgos, findings y aplicabilidad de ADR (no aplica, con motivo).
- [ ] 6.4 `docs/evidence/JUP-067-validation.md` con los comandos y resultados.
- [ ] 6.5 Bloque `## Human Approval` en `review.md` tras la aprobacion explicita de Lucia.
- [ ] 6.6 Archivar el change en la misma rama.
- [ ] 6.7 Abrir el PR hacia `develop`.
