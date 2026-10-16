## 1. Cambios de Paris y verificación de Grafana

- [x] 1.1 Parche de `tools/local-doctor.test.mjs` con la variable `GRAFANA_EVALUATION_DB_PASSWORD` (fixtures, lista esperada y casos de ausencia o vacía), aplicado por el usuario porque el hook congela el test; comprobar `node --test tools/local-doctor.test.mjs`
- [ ] 1.2 Comprobar con un Grafana 11.3.0 real si `groupingToMatrix` admite celdas de texto (decisión D3) y fijar la transformación o la alternativa SQL

## 2. Sección C

- [ ] 2.1 Tasa de error con numerador `or vector(0)` (D1) y latencia p95 rotulada «todas las rutas» (D2); parche a las pruebas congeladas que fijan estas expresiones y títulos; comprobar con `promtool test rules`

## 3. Lectura de la sección A

- [ ] 3.1 Tabla «Resultados por métrica y ejecución» con nombres legibles del catálogo, intervalo de confianza y «No medido» (D3, D5), con prueba de que el `CASE` cubre todas las métricas del catálogo y conciliación con los informes originales
- [ ] 3.2 Resumen de la última campaña (D4)
- [ ] 3.3 Etiquetas: «Tipo de ejecución», columna de resultado fuera cuando todo está medido y variantes traducidas en las tablas de detalle (D5)
- [ ] 3.4 Panel de evolución de la latencia de la campaña (D8)
- [ ] 3.5 Ajustes visuales hallados al validar con Grafana real (D10): altura de la matriz y de las tablas de ejecuciones y de estado, zona horaria UTC en todo el dashboard, cabecera «Tipo de ejecución» sin cortar y variantes de la sección B en español

## 4. Sección B y textos

- [ ] 4.1 Numerador y denominador con unidad legible en la sección B (D6)
- [ ] 4.2 «Cómo leer la sección A» en tres viñetas y «qué no demuestra» a la vista en cada sección (D7)

## 5. Documentación y validación

- [ ] 5.1 Apartado «Calculado y no mostrado» y lectura del dashboard en `docs/validation/evaluation-dashboard.md`; actualizar `docs/evidence/JUP-121-validation.md`
- [ ] 5.2 Validación con la pila real (capturas de la sección A rehecha), `evaluation-dashboard:test`, `openspec:validate`, `jup:check`, `jup:cleanup:check`, y `review.md` con la evidencia
