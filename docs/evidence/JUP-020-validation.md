# JUP-020: correccion del contrato de ingesta documental

- Tarjeta: https://trello.com/c/Mi3kPCOD
- Rama: `fix/JUP-020-ingestion-contract`, basada en `develop` `1ff8e07`.
- Fecha: 2026-09-10.
- Alcance: incidencia de contrato registrada en JUP-020 y RF-053-004.
- PR: https://github.com/EconomiconFinOps/tfm-economicon/pull/34,
  contra `develop`; preparada para revision de Lucia Mateo (`lmatsan`).
  Aprobacion, validacion asignada e integracion pendientes.

## Correccion

`POST /jobs/ingest` publica el objeto real de `Database.create_job`: `id`,
identidad del tenant y documento anidado en `payload`. `IngestTask` ahora
extrae el texto y los metadatos y transforma `id` en `job_id` antes de
invocar el grafo. La identidad del envoltorio tiene precedencia sobre
campos homonimos en el documento. El mensaje original no se modifica.

La API, formato AMQP, esquema SQL y politica de reintentos no cambian.
Los fallos conservan el motivo persistido `ingestion_failed` y la causa para
los logs saneados; el worker conserva su contexto de `request_id`.

## Regresion automatizada

La prueba ejecuta el productor real del backend en un interprete separado:
`IngestJobRequest` → ruta → `Database.create_job` → serializacion de
`RabbitMQQueue.publish`. Solo simula SQL y la conexion al broker. Consume
ese JSON con el task, grafo compilado y chunker reales; el modelo y el
almacen externo se sustituyen por dobles de prueba.

La separacion evita colisiones entre los dos paquetes Python `app`. PyJWT
se añade solo a las dependencias de pruebas del processor para poder
importar el productor del backend en el entorno CI de ese servicio.

Se verifican dos tenants, metadatos, precedencia de identidad, campos
opcionales, fragmentos/vectores, entrada invalida y reintento con fallo de
almacenamiento seguido de exito. Las pruebas de saneado heredadas usan un
envoltorio valido para seguir alcanzando el fallo deliberado del grafo.

La misma regresion, ejecutada con `IngestTask` de `origin/develop` cargado
en memoria, falla con `KeyError: text_content`. No se cambio el archivo de
producto para realizar esa comparacion.

Resultados locales:

| Comprobacion | Resultado |
| --- | --- |
| Backend: `python -m pytest tests -q` | 115 passed |
| Processor: `python -m pytest tests -q` | 263 passed, 34 skipped |
| Regresion contra task anterior | 2 failed, ambos con `KeyError: text_content` |
| OpenSpec estricto | 30 passed |
| Topologia Docker | 27 passed |
| Trazabilidad JUP y limpieza de repositorio | Correctas |

Las 34 pruebas omitidas pertenecen a la suite especifica de integracion
CockroachDB. El smoke funcional adicional si usa servicios reales; no
convierte esas pruebas omitidas en ejecutadas. Hay advertencias heredadas
de dependencias en la suite backend, sin fallos.

## Validacion funcional

Entorno desechable exclusivo en DockerServer: `jup020-validation-20260910`.
RabbitMQ, CockroachDB y PostgreSQL/pgvector reales; backend y processor
construidos del codigo probado. Puertos de aplicacion publicados solo en
loopback. Credenciales sinteticas nuevas, excluidas de las evidencias.

Se inicia backend antes que processor para separar la carrera entre
migraciones registrada en JUP-096. Esta prueba no declara resuelta esa
carrera. Los proveedores LLM y embeddings son `mock`, sin llamadas a APIs
externas; fragmentos de 500 caracteres, overlap de 50 y vectores de 8
dimensiones. Se usa el documento completo
`docs/assistant-corpus/finops/azure-finops-mvp.md`.

El baseline recibe HTTP 202 pero el job
`250876b1-342b-4b63-8c92-9c6106bfa4b5` termina `failed`, con
`KeyError: text_content`. El mensaje RabbitMQ observado y los logs
conservan `request_id` `5d698aeb-7d9a-4738-a692-c32f754f23ff`.

Con el processor corregido, el mismo mensaje retenido se recupera sin
modificar su contenido y alcanza `completed`. Dos peticiones HTTP nuevas
para `tenant-core` y `tenant-growth` tambien llegan a `completed`.

| Comprobacion funcional | Resultado |
| --- | --- |
| Jobs completados | 3, incluido el job fallido del baseline |
| Documentos persistidos | 3, cada uno con su job y tenant correctos |
| Fragmentos | 57: 19 por documento, contenido exacto segun 500/50 |
| Embeddings | 57, uno por fragmento, dimension 8, proveedor mock |
| Metadatos | Payload y resultado del job conservados |
| Correlacion | `request_id` de backend y worker coincide por job |
| Cola final | 0 mensajes disponibles, 0 pendientes de confirmacion |

Las comprobaciones consultan los datos realmente persistidos en ambas
bases. La observacion del mensaje AMQP confirma el envoltorio original;
no se aplanaron ni inyectaron campos para conseguir el exito.

[Resultados funcionales verificables](JUP-020-functional-results.json):
identificadores y correlacion por job, recuentos, hashes del codigo probado
y prueba de retirada del entorno. El SHA-256 de `ingest.py` coincide con
el archivo de esta entrega: `45bc3c1d52c4f0a36d14b5bda7629579e945e371085eb58042875e33b296688e`.
Se retiraron los cinco contenedores, dos volumenes y la red exclusivos;
se elimino el archivo de secretos sinteticos. No se afectaron otros proyectos.

## Reproduccion

En un entorno desechable ya configurado segun el README raiz, con
`DATABASE_URL`, `VECTOR_DATABASE_URL` y `DEMO_PASSWORD` disponibles para el
proceso de validacion, instalar las dependencias Python del backend y
ejecutar desde la raiz:

```sh
python scripts/smoke_document_ingestion.py \
  --base-url http://127.0.0.1:8000 \
  --document docs/assistant-corpus/finops/azure-finops-mvp.md \
  --tenant tenant-core --tenant tenant-growth
```

Adaptar URL y conexiones al entorno seleccionado. El script crea un job
nuevo por tenant, consulta ambas bases de datos y comprueba el contenido
de los fragmentos, dimensiones, identificadores y metadatos del resultado.
La correlacion se contrasta adicionalmente en mensaje AMQP y logs del
backend/worker; no se deduce solo de un HTTP 202.

## Limites y seguimiento

Esta entrega acredita el contrato de transporte y persistencia, no calidad
semantica de embeddings. Siguen pendientes en JUP-020 el proveedor real,
la carga completa/versionada del corpus, metadatos por chunk y la politica
de idempotencia/reprocesado. Conservar metadatos en el resultado del job no
equivale a persistirlos en cada chunk.

Trello conserva liderazgo de Victor Mendez, pairing de Alejandro Aguado,
revision asignada a Lucia Mateo y validacion asignada a Paris Arcos Martin.
Las comprobaciones automatizadas de esta entrega no se atribuyen a esos
revisores ni sustituyen la revision humana o su validacion asignada.

El avance, la PR y las evidencias se enlazaron y releyeron en la tarjeta
oficial mediante la integracion Economicon de DockerServer. JUP-020 permanece
En curso; se conservan los miembros y sus roles.
