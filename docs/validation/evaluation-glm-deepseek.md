# Comparación local GLM/DeepSeek en Grafana — JUP-121 / JUP-063

El informe [comparison.json](../evidence/JUP-063/glm-deepseek-20261016/comparison.json)
es la fuente histórica. No se ejecuta una campaña nueva ni se acepta un modelo.
`PAIRED_LOCAL_PROVISIONAL_COMPARISON` y `NOT_ASSESSED` conservan su significado.
Los requisitos y las salidas completas del replay no se copian a la base.

## Contrato y límites

El adaptador `jup-063-paired-v1` añade un formato a los cinco anteriores sin
cambiarlos. [El manifiesto suplementario](evaluation-glm-deepseek-runs.json) no
modifica los cinco hitos del manifiesto histórico. Genera **una ejecución del
informe**, con dos modelos en `behavior` y nueve filas por modelo:

- `provisional_pass`, `provisional_fail`, `pending`: recuentos 77/6/1 y 82/2/0,
  denominador 84. `judgment=null` porque no hay adjudicación humana independiente
  ni checks automáticos de calidad acreditados. Son rúbrica **local provisional**.
  El validador permite ese nulo exclusivamente para esos tres identificadores en
  `paired_local_provisional`. No se emiten `cases/pass`, ACC-1 ni tasas aceptadas.
- `sample_size`: 84 por modelo, no 168 preguntas distintas.
- `reported_phase_cost_usd`: suma reportada de fases draft/final, 0.176012028 y
  0.3470654625 USD; no coste total de cuenta. No tiene denominador de respuestas.
- `unknown_cost_phases`: contador explícito de fases cuyo coste no se conoce.
- `generation_seconds_p50`, `generation_seconds_p95`, `generation_seconds_max`:
  segundos de generación, sin arranque, recursos, preflight ni scheduler. Los
  valores y unidades se copian; no se convierten en latencia E2E ni se mezclan con
  la campaña canónica o el benchmark de JUP-078.

Las seis medidas técnicas por modelo son `automatic`; los tres juicios locales
no lo son. El panel 25 muestra expresamente la provisionalidad. `null` en coste o
latencia significa «No medido». Un estado de juicio omitido solo se convierte en
cero después de comprobar que los recuentos forman una partición del total.
El adaptador rechaza tamaños desiguales, recuentos incoherentes, NaN/Infinity,
unidades/alcances no admitidos y aceptación distinta de `NOT_ASSESSED`.

Fecha de observación del agregador no equivale a fecha de ejecución: `run_at`
queda `null`, igual que commit, hashes de batería/corpus/prompt, configuración y
modelo único (el informe contiene dos). No genera evoluciones temporales. La
clasificación `real` describe llamadas de proveedor de esta fuente, nunca
aceptación, atribución independiente ni comparabilidad con el runtime actual.
La identidad estable es el sha256 canónico del JSON parseado; difiere del hash
de bytes del informe exacto por serialización, sin cambiar sus valores.

## Preparación offline

Desde la raíz del repositorio, sin credenciales ni servicios:

```sh
python tools/evaluation-dashboard.py rows --manifest docs/validation/evaluation-glm-deepseek-runs.json --output /tmp/evaluation-with-comparison.json
python tools/evaluation-dashboard.py sql --no-versioned --manifest docs/validation/evaluation-glm-deepseek-runs.json --preserve-existing --output /tmp/evaluation-comparison-scoped.sql
```

El primer comando combina cinco hitos y esta comparación (6 ejecuciones). El
segundo prepara **solo la comparación**, en una transacción, sin `TRUNCATE`, DDL,
roles ni permisos. Reemplaza su mismo `run_id` únicamente si coinciden fuente y
huella completa; si el mismo identificador pertenece a otra huella/fuente,
colisiona la clave primaria y se deshace todo. Otros runs y filas se conservan.
No admite el conjunto completo ni identificadores impuestos que no sean el
derivado de esa fuente y huella. Dos cargas del mismo informe dejan lo mismo.

## Destino y aplicación tras verificarlo

El destino **de configuración del repositorio** es el servicio Compose
`postgres-pgvector`, base `embeddings`, esquema `evaluation`. Grafana lee con el
datasource `evaluation-postgres`, usuario `grafana_evaluation_reader`, URL interna
`postgres-pgvector:5432`. Dashboard UID `economicon-assistant-evaluation`; su JSON
es `apps/monitoring/grafana/dashboards/assistant-evaluation.json`. El proveedor de
archivos comprueba cambios cada 30 segundos si ese fichero está montado.

Esto no identifica por sí mismo un stack remoto activo. Antes de aplicar, el
operador debe acreditar proyecto/contenedores/datasource y fichero efectivos,
que las tablas y el rol ya existen y que ese destino es el autorizado. No elegir
entre stacks históricos por intuición ni cambiar claves para hacerlos encajar.
Con el proyecto existente **ya identificado**, el comando de datos es:

```sh
docker compose exec -T -e PGCLIENTENCODING=UTF8 postgres-pgvector psql -U postgres -d embeddings -v ON_ERROR_STOP=1 -X -q < /tmp/evaluation-comparison-scoped.sql
```

Ese script no crea roles ni migra esquema ni necesita la contraseña de Grafana.
No usar `load` normal ni `--no-versioned` sin `--preserve-existing` contra una
proyección compartida: la carga histórica vacía ambas tablas y cambia el rol.
Si no existe este dashboard/datasource en el destino, preparar el despliegue es
un pendiente separado; no afirmar que la tabla se ve en Grafana por haber
generado SQL o publicado el JSON. Verificar luego las dos filas del panel y
comparar huellas de los otros runs antes/después.

## Comprobación

`test_evaluation_adapter_jup063.py` concilia la fuente, rechazo/atomicidad offline,
NULL provisional, aislamiento, determinismo y la consulta real del panel con SQL
en memoria. `check_evaluation_paired_postgres.py` es una prueba **opt-in** para un
daemon autorizado: un contenedor propio, 1 CPU/1 GB, sin red/puertos ni volúmenes,
con retirada en `finally`; comprueba PostgreSQL, idempotencia, sentinel inmutable,
error tras borrado/inserción, colisión de huella y consulta del panel. No descarga
imágenes y exige `pgvector/pgvector:pg17` existente.

La ejecución remota de esa prueba y la visibilidad del dashboard son pendientes
hasta disponer de sus recibos. Soporte offline no significa carga live realizada.
