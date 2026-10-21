## 1. Eventos inyectados y prueba de coherencia

- [x] 1.1 Escribir `docs/validation/JUP-130-injected-events.json` con los siete eventos del generador (servicio, día de inicio, naturaleza, detectable por diseño) a partir de `SEPTEMBER` y `EXTENSION`, sin leer la salida del detector
- [x] 1.2 Prueba que comprueba cada evento contra `anomaly_levels()` y que todo salto de aumento del generador tiene su evento; una caída (Compute el 4/10) no es evento
- [x] 1.3 Mutación de la prueba: borrar un evento, añadir uno falso o mover un día hace fallar la prueba

## 2. Medición de anomalías

- [x] 2.1 Crear `tools/memory-indicators.py` con el subcomando `anomalies`: carga el generador y `plan_detection` por ruta, ejecuta desde estado vacío con la fecha de referencia dada y empareja episodios y eventos (mismo servicio, 0 a 3 días, un episodio por evento)
- [x] 2.2 Calcular precisión, recall de todos los eventos, recall de los detectables por diseño, retraso y recuentos; precisión `not_measured` con denominador 0 si no hay episodios
- [x] 2.3 Emitir el informe `rows-v1` (fuente `JUP-130-anomalies`, grupo `anomaly_detection`, tipo A, juicio automático) y la tabla Markdown con el comando y los límites
- [x] 2.4 Pruebas: caso real a 2026-09-21 y 2026-10-30 con recuentos esperados escritos a mano, episodio sin evento, dos eventos y un episodio, sin episodios, y salida idéntica en dos ejecuciones
- [x] 2.5 Ejecutar la medición, versionar el informe y la tabla en `docs/evidence/JUP-130/` y registrar como hallazgo cualquier evento detectable no detectado

## 3. Medición de datos

- [x] 3.1 Subcomando `data`: frescura por inquilino a partir del último día con datos y la fecha de referencia, sin contar días sin registro como cero
- [x] 3.2 Reconciliación por divisa: suma decimal exacta del CSV del generador frente al total del API de resumen, diferencia en unidades menores y `reconciled`
- [x] 3.3 Sin API o sin datos, filas `not_measured`; nunca `reconciled` verdadero sin comparación
- [x] 3.4 Pruebas: totales iguales, diferencia de un céntimo, dos divisas sin compensación, API caída, inquilino sin datos y datos atrasados
- [x] 3.5 Ejecutar contra la pila real, versionar informe y tabla en `docs/evidence/JUP-130/`

## 4. Medición de coste de IA

- [x] 4.1 Subcomando `ai-cost`: cliente de `/spend/logs` con la clave de administración leída de entorno o fichero, sin imprimirla, y ventana indicada
- [x] 4.2 Comprobado con el gateway real (924 filas): las filas de chat traen el identificador `gen-…` de OpenRouter en `request_id` y las de embeddings no; los 429 son del límite por clave del gateway y los fallos del proveedor son 500. Spec y diseño ajustados
- [x] 4.3 Agregar consultas de chat, coste estimado, por alias de modelo, embeddings aparte, consultas con gasto cero, y las tasas de rechazo del gateway (429) y de error del proveedor (5xx) con numerador y denominador
- [x] 4.4 Cliente de solo lectura de `GET /api/v1/generation` con la clave de OpenRouter leída de entorno o fichero, tope de generaciones por ejecución y sin imprimir identificadores; calcular coste facturado, cobertura y diferencia con la estimación sobre las confirmadas
- [x] 4.5 Gateway caído, OpenRouter caído, claves ausentes, 404 y ventana sin consultas dan filas `not_measured` o cobertura reducida, nunca coste 0; `/api/v1/key` no se usa como coste de la ventana
- [x] 4.6 Pruebas con un gateway y un OpenRouter simulados: todo confirmado, una generación 404, fila sin identificador, sin consultas, sin 429, ambos caídos, claves ausentes, y comprobación de que las claves de prueba y los identificadores de generación no aparecen en informe, tabla ni salida
- [x] 4.7 Ejecutar con el gateway aislado y gasto real registrado, versionar informe y tabla; si no hay gasto disponible, documentar «Sin datos» y la causa

## 5. Carga y paneles

- [x] 5.1 Añadir los informes al manifiesto `docs/validation/evaluation-runs.json` y comprobar con `evaluation-dashboard:rows` que pasan el contrato `rows-v1`
- [x] 5.2 Panel de anomalías (sección A) con «Mide:» y «No demuestra:», un solo datasource y filtro por su fuente `JUP-130-anomalies`
- [x] 5.3 Paneles de coste de IA y de calidad de datos (sección B) con las mismas reglas y «Sin datos» / «No medido» cuando falten
- [x] 5.4 Actualizar las pruebas estructurales del dashboard y la conciliación con los informes; carga repetida deja los mismos datos
- [x] 5.5 Comprobar en el navegador con la pila real y `evaluation-dashboard:load`, sin pasos manuales nuevos, que los tres paneles muestran datos, y guardar capturas en `docs/evidence/JUP-130/`

## 6. Documentación

- [x] 6.1 Actualizar `docs/validation/evaluation-dashboard.md` con las tres fuentes, los grupos y la nota que amplía ADR-0022 sobre la lectura de `/spend/logs`
- [x] 6.2 Actualizar `docs/continuidad/README.md` y escribir la nota del tema con estado, límites y pendientes
- [x] 6.3 Entregar a quien redacta JUP-109 las tablas de la memoria con su comando y sus límites, sin copiar la memoria al repositorio

## 7. Cierre y verificación

- [ ] 7.1 Ejecutar la batería completa: `corepack pnpm build`, `lint`, `test`, `openspec:validate`, `jup:check -- --change jup-130-indicadores-memoria`, `jup:cleanup:check` y `evaluation-dashboard:test`
- [ ] 7.2 Revisión adversarial con el agente `adversarial-reviewer` sobre la spec y el diff hasta obtener `accept`
- [ ] 7.3 Escribir `review.md` con la evidencia por tarea y el resultado de la revisión adversarial
- [ ] 7.4 Reunir la evidencia del código de producto tocado en `docs/evidence/JUP-130-validation.md`
- [ ] 7.5 Dejar la sección `## Human Approval` posterior a la revisión para Lucia
- [ ] 7.6 Archivar el change en el mismo PR y abrir el PR contra `develop`
