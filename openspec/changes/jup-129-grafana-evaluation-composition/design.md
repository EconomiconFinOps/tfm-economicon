JUP: JUP-129

# Diseño aprobado y adaptación al producto

Paris aprueba la composición y la corrección de lenguaje el 21/10/2026, y autoriza implementación local con revisión y validación independientes antes de subir. No se repite la aprobación del mismo diseño. La entrega de presentación se conserva fuera del producto, identificada por SHA256 en la evidencia.

## D1. Una entrada narrativa, compatibilidad preservada
`assistant-evidence.json`, UID `economicon-assistant-evidence`, es la lectura principal. Se revisan los dos dashboards originales como origen: evaluación para resultados/informes y técnico para señales Prometheus. Sus UID, archivos y contratos permanecen para auditoría, enlaces existentes y operaciones. No se copian todos sus paneles a la lectura principal.

## D2. Contrato y datos existentes
PostgreSQL nativo `evaluation-postgres`, rol lector existente; Prometheus sólo en salud. No se cambia provisioning, rol, SQL de carga, dataset por defecto ni `rows-v1`. La base bc94 carga ocho ejecuciones/308 filas; no incluye la campaña experimental de 136 filas ni el suplemento de comparación histórica. Esas ausencias deben verse, no sustituirse por los números del prototipo. Las referencias históricas y los indicadores de pruebas se fijan a una identidad de informe para impedir máximos entre campañas distintas.

## D3. Selección y límites
Selector con nombres funcionales y valor interno exacto, escapado mediante `sqlstring`; sin interpolación raw. La cabecera describe la ejecución realmente seleccionada. Los contadores y el anillo usan una sola campaña; las categorías son un subconjunto. Sin datos no significa cero. Los 7/29 experimentales, cuando se carga su informe, no se esconden detrás de la cobertura de citas. La muestra conocida tiene una repetición/persona evaluadora y modelo sin verificar; no se atribuye aceptación o despliegue.

## D4. Cuatro familias
Core: rúbrica y diagnósticos existentes, sin atribuir relevancia/fidelidad con aceptación independiente. Recuperación: documento/sección y calibración histórica, sin causalidad entre corpus distintos. Rendimiento: coste y p95 de una misma cohorte y salud aparte. Conversación/usuario: proxy de petición de rúbrica mixta; usuarios reales no medidos. Sin nuevas métricas o score compuesto.

## D5. Comparación honesta
Dos selectores, campaña y referencia. Se exige distinta identidad, fechas registradas y referencia anterior, misma fuente y clave de comparabilidad (batería, corpus, modelo, prompt, recuperación y motivos de no realidad). La disponibilidad no certifica superioridad. El detalle pone lado a lado las mismas filas/unidades, con igualdad exacta (tolerancia cero), aumento o disminución observados; no orienta indicadores desconocidos como mejoras. No se trazan tendencias, intervalos inventados ni líneas entre experimentos. El gráfico de modelos mantiene sólo dos puntos de la misma cohorte histórica; coste de fases no es facturación operativa.

## D6. Evidencia y límites
La integración se prueba con el JSON del candidato, Grafana real y PostgreSQL lector en espacios propios: manifiesto real bc94 y proyección experimental verificada por separado. Sin llamadas a modelos ni servicios compartidos. Se conservan capturas antes/después y conciliación. La prueba de lectura exige una persona ajena al dashboard: los agentes no la sustituyen. Revisor y Validador independientes, controles originales del PM antes de evaluarlos y sin publicación automática.
