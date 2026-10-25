JUP: JUP-139
Trello: https://trello.com/c/npVVicNQ

# Cinco secciones de métricas en Grafana

## Why
«Asistente y evidencia» destaca sólo parte de los indicadores disponibles. La tabla genérica conserva filas, pero no identifica la ejecución ni la unidad de cada resultado. La defensa necesita una composición comprensible que separe negocio, calidad, recuperación, rendimiento del chat y operación, con fuentes y límites visibles.

## What Changes
- Evolucionar el UID existente `economicon-assistant-evidence` a cinco secciones, conservando los dos dashboards previos y el aspecto visual.
- Hacer visibles las medidas existentes de robustez, recuperación/citas, coste/rendimiento y operación según el inventario fuente/panel; conservar el diagnóstico extenso plegable.
- Identificar en cada panel si usa la campaña seleccionada, una referencia histórica fija o tráfico en vivo. Conservar identidad servida del modelo cuando conste y ausencia explícita cuando no.
- Completar la identificación de ejecución y unidades del detalle, conservando intervalos existentes donde sean aplicables.
- Usar los datos existentes ya cargados para la propuesta y la entrega. Por decisión de Paris del 23/10/2026, la actualización de campañas se realizará después de publicar el dashboard y no bloquea esta entrega; se conserva el mecanismo de carga existente.
- Preparar primero la composición en Grafana local aislado y mostrar capturas a Paris; el diseño concreto se aprueba antes de modificar el dashboard versionado.

## Impact
Dashboard de composición, pruebas focales, guía, continuidad y evidencia. La actualización de campañas, incluidos los originales pendientes del 22/10, queda diferida y fuera de esta entrega. No se modifican el manifiesto ni los informes para actualizar sus resultados. Se reutilizan Grafana, PostgreSQL, Prometheus, loader, datasources y Compose. Sin nuevas métricas, dependencias de producción, permisos, modelos, campañas, despliegue compartido, gasto ni modificaciones de los dashboards anteriores.

## Preparación y aprobación visual
Rama feat/JUP-139-grafana-five-sections desde develop 84b53b74. Paris confirma liderazgo Paris, pairing Alejandro, revisión Lucía y validación Víctor el 23/10/2026. Propuesta visual en Grafana aislado autorizada; composición v4 aprobada e implementación autorizada por Paris el 23/10/2026; resultados pendientes de evaluación independiente y aprobación final. La excepción de una copia adicional está autorizada; no se hereda ninguna dispensa de pairing.

## Ampliación aprobada el 23/10/2026
Paris autoriza incorporar las tres evoluciones existentes: métricas automáticas y juicio registrado como humano/sólo hitos en Calidad y robustez; mediana/p95 total de campaña en Coste y rendimiento. Se conservan consultas, comparabilidad, unidades y anotaciones existentes. No se amplía a nuevas mediciones ni se autoriza eliminar los dashboards anteriores.

## Ajuste de puntos aprobado el 23/10/2026
Paris autoriza conservar cada observación aislada como punto y conectar únicamente las comparables. Las tres consultas leen evaluation.runs porque la vista comparable_runs también excluye ejecuciones sin pareja; la vista y los otros dos UID permanecen intactos. Un catálogo común de claves identifica la misma cohorte entre las tres gráficas; una clave nula/vacía se aísla por ejecución. La serie incluye métrica, variante, grupo, unidad y origen del juicio, y la transformación nativa particiona por esa identidad. Puntos siempre visibles, interpolación lineal sólo dentro de cada serie y sin puentear nulos. Sin fecha o valor no se inventa un punto: el registro sigue en Diagnóstico.

Datos ya cargados:196observaciones automáticas,28de juicio registrado sólo hitos y6de latencia; cada serie tiene una observación y no se conectan cohortes. Se conservan los casos SQL de un punto, dos compatibles, dos incompatibles, fecha/valor ausentes, hitos, unidades y tipos de juicio. No se simulan campañas en las capturas de resultados.

## Adaptación aprobada a las seis campañas existentes — 23/10/2026

Paris autoriza por coordinación PM a las19:31:44Atlantic/Canary adaptar esta composición a PR156, cargar únicamente el entorno local propio y evaluar de forma independiente el delta antes de mostrar resultados/capturas y subir nada. La base fue reconciliada por PM a db8f69ab5e2d4a42931cd6dc7412b99e855f0148. Esto sustituye la decisión previa de diferir exclusivamente esas seis campañas ya recogidas; no autoriza nuevas generaciones, gasto, importación del CSV financiero, archivo, commit/push/PR o retirada de dashboards. Los originales R1–R4 y sus dictámenes corresponden a sus candidatos históricos y se conservan sin extensión automática.

Se conserva la composición de cinco secciones,16tarjetas principales y tres evoluciones. La lectura visible de casos elige instrumento original o juez IA provisional cuando existe; no se rellenan filas humanas con IA. Cobertura mantiene respuestas previstas/disponibles/criterios y ausencia humana separadas. Las tablas traducen métricas/variantes y ocultan sus identificadores originales para conciliación. Los pares comparan grupo,identificador,variante,estado y unidad iguales, además de fuente/clave/orden temporal.

Coste reportado de completadas, gasto liquidado de todas las operaciones y factura histórica son poblaciones distintas. Las latencias distinguen terminal de todas las operaciones, terminal sólo completadas y etapa total histórica; ninguna sustituye generación o HTTP ni reconstruye etapas ausentes. Las series conservan esta población,el juicio y la cohorte; la igualdad de modelo declarado no conecta histórico. Los tiempos y costes permanecen medidas existentes,sin puntuación nueva.

Carga nativa local comprobada:19ejecuciones/1688resultados (18/1670versionados+suplemento histórico1/18). Snapshot13/665ySQLrecuperable conservados; aborto transaccional demuestra rollback íntegro antes de la carga efectiva; los13runs/665resultados previos permanecen exactos. No otras bases,modelos o gasto. El CSV1370es una instantánea y no se importa.


## Refinamiento visual v6 aprobado el 23/10/2026

Paris aprueba la propuesta v6/versión temporal 12 y autoriza implementarla
conservando todas las métricas, con revisión técnica y validación funcional
independientes de lo afectado y resultados/capturas antes de subir nada. Esta
composición sustituye la presentación de puntos y anillo de los cortes anteriores:
matrices automáticas, hitos humanos, cambios Antes/Ahora/Diferencia y barras de
mediana/p95; cada observación histórica y cada configuración permanecen en el
detalle de su sección. Las cinco secciones se abren desplegadas.

Base estable 93624f77, GENERAL 19/1688 reutilizado sin recarga. No nuevas campañas,
modelos, claves, gasto, archivo, Git de escritura, publicación ni retirada de los
otros dashboards. Roles humanos vigentes y proceso 18/10 se conservan. La aprobación
visual no sustituye aceptación final, evaluaciones independientes ni reviews humanas.
