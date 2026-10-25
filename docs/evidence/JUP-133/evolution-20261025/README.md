# Evolución observada: viernes 23 y domingo 25 de octubre de 2026

JUP-133 · [Trello](https://trello.com/c/Yv1ETc2G). Publicación de evidencia existente,
sin nuevas consultas al modelo, nuevo juicio, despliegue ni aceptación de RC.
Origen: HAL 9000, `01a1270c-e332-7462-9c90-706d49ade92c`, petición del 25/10.

La referencia solicitada es **el viernes 23**, no la primera pasada del domingo.
El domingo publicado es la validación integral tras PR164, producto
`390721f92d60d29358de62e9cebf99ee028190a2`. El develop usado para preparar esta PR
es `1c4eda8a70ddd9412238f0c2b4fdef8073a9e10d`: sus cambios posteriores **no se
presentan como ensayados**. El commit de producto del viernes no fue atestado;
se conservan las identidades de imagen registradas.

## Comparación operativa

| Medida | Viernes 23 | Domingo 25 |
| --- | ---: | ---: |
| Casos distintos comunes | 44 | 44 |
| Repeticiones por caso | 3 | 1 |
| Operaciones | 132 | 44 |
| Completadas técnicamente | 119 (90,2 %) | 41 (93,2 %) |
| Operaciones con reintentos | 35 (26,5 %) | 4 (9,1 %) |
| Intentos | 201 | 53 |
| Mediana observada | 20,128 s | 12,020 s |
| P95 observado | 148,796 s | 49,485 s |
| Máximo observado | 314,653 s | 65,892 s |

Son 28 preguntas generales y 16 perturbaciones. De las 171 operaciones del
viernes se excluyen las 13 referencias repetidas en cada una de las tres pasadas
de robustez (39). De las 50 del domingo se excluyen cuatro consultas reportadas
y dos controles con pantalla. **No se seleccionan sólo respuestas favorables.**
Las perturbaciones completan el **87,5 % en ambos días**; el agregado no implica
que todos los bancos mejoren.

La pregunta y el escenario coinciden en los 132 pares cotejados; el texto
envolvente y orden del prompt difieren. Sin datos de pantalla en los 44 comunes.
Viernes mide POST de generación hasta observación terminal; domingo incluye
creación de conversación y recogida posterior de evidencia. Se incluyen fallos y
reintentos; P95 por rango más próximo `ceil(0,95*n)`, mediana convencional. Arnés,
carga y número de repeticiones distintos: descripción de observaciones, **no A/B,
efecto causal del fix ni estabilidad demostrada**.

## Campaña completa del domingo

50 operaciones, 47 completadas, 61 intentos. Juicio funcional por agentes:
**39 conformes, 7 parciales y 4 fallos**. Una respuesta completada puede fallar
funcionalmente. No es una revisión humana ni una aceptación formal.

- 069-003 sigue omitiendo investigar por servicio/recurso.
- 069-012 y 071-014 agotan intentos por validación interna; 071-015 termina con
  HTTP 520. Los fallos tempranos también reducen los tiempos observados.
- Analytics conserva los importes mensuales, pero omite el total y presenta
  problemas de composición. Variación compara períodos solapados.
- Sigue el fallo técnico HTTP 413 de captura grande. Suites: backend
  2731 PASS / 1 FAIL / 369 SKIP, processor 2676 PASS / 150 SKIP, frontend
  1427 PASS, Azure 81 PASS. No sumar suites solapadas ni declarar toda la app verde.

La puntuación por puntos semánticos del viernes y la clasificación funcional del
domingo son instrumentos distintos. **No se calcula una mejora homogénea de
calidad**, ni se sustituye la puntuación original del viernes.

Coste de los 44 comunes: viernes **0,4435138808 USD** de atribución liquidada del
gateway, incluidos embeddings; domingo **0,0727486368 USD** observados de chat,
con uso incompleto y sin embeddings asignados. Toda la campaña nueva registra
**0,0808892056 USD**, también incompletos. Ninguno es factura confirmada. No se
calcula porcentaje de ahorro. El incremento global del ledger puede incluir
actividad concurrente y no se atribuye a estos casos.

## Datos y lectura en Grafana

- [observations.json](observations.json): 171 observaciones históricas y 50
  nuevas, reducidas a IDs de caso, estados, tiempos, intentos, costes y dictamen.
  Sin preguntas, respuestas, conversaciones, identificadores operativos ni secretos.
- [summary.json](summary.json): agregados reproducibles por población.
- [friday.rows.json](friday.rows.json) y [sunday.rows.json](sunday.rows.json):
  dos **proyecciones derivadas**, 130 filas del contrato `rows-v1`; no son dos
  campañas ejecutadas de nuevo. Fuente JUP-133 separada de JUP-070/JUP-071 para
  no duplicar sus denominadores ni reemplazar sus instrumentos originales.
- El manifiesto pasa de 18/1670 a **20 representaciones / 1800 filas**. Las 18
  anteriores permanecen idénticas. Las representaciones no se suman como
  operaciones independientes: se solapan las poblaciones full/common/general/etc.
- Modelo/proveedor/cuántización declarados: DeepSeek V4.1 Flash, DeepInfra FP8
  vía OpenRouter; upstream no atestado independientemente. Alias/hashes no
  acreditados se conservan nulos. Protocolo `polling-v1` / `client-capture-v1`:
  claves de comparabilidad diferentes; no se fuerza una serie comparable.

En **Asistente y evidencia**, sección 2, se añaden cuatro paneles (8400–8403):
método, terminación/reintentos por banco, mediana/P95 observados y resultado
completo del domingo. Es un bloque de **fechas fijas**, independiente de los
selectores superiores. Conserva UID, cinco secciones, paneles y selectores
anteriores y los otros dos dashboards. No une los períodos con una curva de
tendencia causal. Si falta la carga, se muestra Sin datos, nunca un cero supuesto.

Los datos de negocio/corpus de los ensayos son sintéticos. La medición se hizo
por ruta privada de DockerDevelop; no acredita equivalencia autenticada con el
acceso público de Cloudflare. Los registros privados/ZIP permanecen fuera de Git;
`source_sha256` permite cotejarlos. ZIP nuevo sellado:
`d182fedcd92226acfea6369515429284f15d35b7a8eb679e7c24eba5a908e7ff`.

## Reproducción y carga posterior

```sh
python tools/evaluation-evolution.py --check
python -m unittest discover -s scripts/tests -p test_evaluation_evolution.py -v
```

Sin `--check`, el generador regenera sólo estos JSON/SQL desde observaciones
públicas; no accede a red ni bases. El manifiesto suplementario es
`docs/validation/evaluation-evolution-runs.json`.

Para una instalación existente, usar **[append.sql](append.sql)**, tras backup y
revisión del responsable del despliegue, con `psql -v ON_ERROR_STOP=1 -f ...` sobre
el esquema `evaluation` ya existente. La PR **no lo ejecuta**. Adquiere bloqueo
acotado (15 s), prepara las dos identidades, compara todos los metadatos y todas
las filas de cualquier identidad existente y aborta la transacción si difieren,
faltan o sobran filas. Sólo inserta identidades ausentes. Repetirlo no cambia
nada. Conserva campañas extra del servidor, roles y credenciales; no vacía tablas.

**No usar el importador general `evaluation-dashboard:load` en una base
compartida para añadir este suplemento:** su contrato reemplaza el dataset y
podría eliminar ejecuciones adicionales no versionadas. El importador general
sigue siendo válido para fixtures y bases nuevas/desechables.

Revisión humana de la PR, integración, carga y verificación visual en el Grafana
compartido quedan pendientes; publicar los datos no acepta la RC.

## Validación de esta incorporación — 25/10/2026

Pruebas ejecutadas por el asistente de Alejandro; no sustituyen las revisiones
humanas asignadas. **625 pruebas conformes, 0 fallos, 0 omisiones, 80,055 s**:

```sh
PYTHONPATH=scripts/tests python -m unittest \
  test_evaluation_evolution test_evaluation_composition \
  test_evaluation_manifest test_evaluation_infra_manifest \
  test_evaluation_classification test_evaluation_classification_gaps \
  test_evaluation_model_identity test_evaluation_rows_contract \
  test_evaluation_sql test_evaluation_dashboard_structure \
  test_evaluation_views test_evaluation_pr156
```

Incluye 12 pruebas nuevas de denominadores, coste, datos ausentes, colisiones y
carga aditiva en PostgreSQL desechable. Las consultas del bloque nuevo devuelven
las cifras publicadas. Las 18 fuentes anteriores, sus entradas de manifiesto y
el contenido de los paneles previos permanecen idénticos (salvo desplazamiento
vertical). Las dos claves nuevas no crean una serie comparable en las vistas
estrictas existentes.

`evaluation-evolution.py --check`, `jup-check`, `jup-cleanup-check` y
`git diff --check` conformes; OpenSpec `validate --all --strict`: **93 válidos**.
Nueve pruebas adicionales de salud/promtool **no pudieron ejecutarse**: Docker
remoto rechaza el montaje de la ruta temporal Windows (`invalid volume
specification`). No se cuentan como aprobadas. Sus pruebas y las consultas
Prometheus no cambiaron; queda pendiente ejecutarlas en un entorno con montajes
compatibles. No se afirma una suite global de la aplicación verde ni una
verificación visual del Grafana compartido.

Antes de publicar se cotejó el avance remoto de `develop` a `da43f408`: modifica
la retirada de AWS y su documentación, sin cambios en estas fuentes, contratos
o dashboards. La base inicial de implementación sigue siendo `1c4eda8a`; la
versión medida de la campaña del domingo sigue siendo `390721f9`.
