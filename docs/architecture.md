# Arquitectura del proyecto

## 1. Para que sirve este documento

Este documento explica la arquitectura del proyecto de una forma simple, pensando en personas junior o en gente que no ha trabajado antes con sistemas separados en varios servicios.

La idea principal es esta:

**este repo no es una sola aplicacion, sino varias piezas que trabajan juntas.**

## 2. Vista general

En este proyecto hay varios submodulos importantes:

- `apps/frontend`
- `apps/backend`
- `apps/processor`
- `apps/azure-cost-api`
- `packages/shared-config`

Y ademas hay tres servicios de infraestructura:

- `CockroachDB`
- `RabbitMQ`
- `Postgres + pgvector`

Cada pieza tiene una responsabilidad distinta.

## 3. Que hace cada submodulo

### `apps/frontend`

Es la parte visual del sistema.

Es la aplicacion que ve el usuario en el navegador. Su trabajo principal es:

- mostrar informacion
- pedir datos al backend
- ensenar el estado general del sistema

El frontend **no habla directamente** con las bases de datos ni con RabbitMQ.
Siempre pasa por el backend.

### `apps/backend`

Es la API principal del sistema.

Su trabajo es recibir peticiones HTTP, validar datos y coordinar operaciones.

Por ejemplo, el backend:

- responde al frontend
- gestiona autenticacion basica y el usuario seed local de desarrollo
- valida el tenant activo usando `X-Tenant-Id`
- consulta o guarda datos en la base de datos operativa
- devuelve resumenes de billing
- crea jobs de procesamiento
- envia esos jobs a RabbitMQ
- gestiona conversaciones del asistente
- consulta `Postgres + pgvector` para buscar contexto en `/assistant`

El backend es como el punto central de entrada para las peticiones normales de la aplicacion.

### `apps/processor`

Es el servicio que hace trabajo en segundo plano.

No esta pensado para que el usuario hable con el directamente desde la interfaz. Su trabajo es:

- escuchar jobs pendientes en RabbitMQ
- procesarlos
- dividir `text_content` en chunks
- generar embeddings
- guardar esos embeddings en pgvector
- ejecutar el pipeline interno
- guardar resultados o actualizar estados en la base de datos operativa

Ademas, el processor expone una API operativa interna en `:8001/health`.
En Docker y en local, `app.run_all` levanta dos cosas dentro del mismo servicio:

- el worker que consume RabbitMQ
- una API FastAPI pequena para healthcheck operativo

Esa API del processor no es una API de producto para el frontend.
El frontend sigue hablando solo con el backend.

Esto permite que las tareas pesadas o lentas no bloqueen al backend, y tambien permite comprobar si el processor esta vivo.

### `apps/azure-cost-api`

Es un servicio FastAPI independiente que simula el subconjunto de Azure Cost
Management Query aprobado en JUP-073. Lee exclusivamente el fixture público
`EA-Cost-Actual.sample.csv`, expone healthcheck en `:8002/health` y responde con
la estructura posicional `columns`/`rows` utilizada por Azure.

No se conecta a un tenant ni valida credenciales Azure reales. Su función es
proporcionar un endpoint HTTP reproducible para el futuro cliente de ingesta.
JUP-075 incorporará paginación y fallos deterministas; JUP-076 conectará el
processor con este servicio mediante configuración.

### `packages/shared-config`

Es un paquete compartido del monorepo.

Ahora mismo es pequeno, pero su objetivo es ser un lugar comun para poner:

- configuraciones compartidas
- constantes
- convenciones del workspace
- utilidades comunes del lado JavaScript

No es un servicio que se ejecute solo. Es una pieza de apoyo.

## 4. Que papel tienen RabbitMQ, CockroachDB y pgvector

### CockroachDB

Es la base de datos principal del sistema.

Aqui se guarda la informacion operativa importante, por ejemplo:

- users
- tenants
- user_tenants
- jobs
- conversations
- messages
- estados de ejecucion
- resultados de procesamiento

Piensa en CockroachDB como la memoria permanente del sistema para la parte transaccional.

### RabbitMQ

Es el sistema de colas.

Sirve para pasar trabajo del backend al processor sin que ambos tengan que hacer todo al mismo tiempo.

Piensa en RabbitMQ como una bandeja de tareas pendientes:

- el backend deja un job de procesamiento en la cola
- el processor recoge ese trabajo
- el processor lo procesa cuando le toca

RabbitMQ no guarda datos de negocio ni sustituye a la base de datos.
Solo transporta jobs de procesamiento entre servicios.

Esto desacopla servicios y hace la arquitectura mas robusta.

### Postgres + pgvector

Es el almacenamiento vectorial del sistema.

Aqui se guardan:

- documentos procesados
- chunks de texto
- embeddings de cada chunk

El `processor` escribe estos documentos, chunks y embeddings durante la ingesta.
Despues, el `backend` consulta esos chunks cuando responde al asistente en `/assistant`.

Piensa en `pgvector` como una base especializada para busqueda semantica y RAG.
No sustituye a CockroachDB: CockroachDB guarda el estado operativo y pgvector guarda el indice vectorial.

## 5. Relacion entre los submodulos

Hay dos relaciones principales entre las piezas.

La primera es el flujo de ingesta:

1. El usuario usa el `frontend`
2. El `frontend` llama al `backend` por HTTP
3. El `backend` guarda o consulta datos en `CockroachDB`
4. Si hace falta procesamiento asincrono, el `backend` publica un job en `RabbitMQ`
5. El `processor` consume ese job desde `RabbitMQ`
6. El `processor` procesa el trabajo, guarda embeddings en `Postgres + pgvector` y actualiza `CockroachDB`
7. El `backend` puede devolver despues informacion actualizada al `frontend`

La segunda es el flujo de chat con retrieval:

1. El usuario escribe en el asistente desde el `frontend`
2. El `frontend` llama al `backend` por HTTP
3. El `backend` valida usuario y tenant
4. El `backend` genera un embedding de la pregunta
5. El `backend` consulta `Postgres + pgvector` para recuperar chunks relevantes del mismo tenant
6. El `backend` guarda la conversacion y mensajes en `CockroachDB`
7. El `backend` devuelve la respuesta al `frontend`

## 6. Flujo simplificado

### Ingesta asincrona

```text
Usuario
  |
  v
Frontend (React)
  |
  v
Backend (FastAPI)
  | \
  |  \--> CockroachDB
  |
  \----> RabbitMQ ----> Processor
                         | \
                         |  \--> Postgres + pgvector
                         |
                         v
                    CockroachDB
```

### Chat con retrieval

```text
Usuario
  |
  v
Frontend (React)
  |
  v
Backend (FastAPI)
  | \
  |  \--> CockroachDB
  |
  \----> Postgres + pgvector
          ^
          |
    chunks y embeddings
    escritos por Processor
```

## 7. Por que esta separado asi

Este tipo de arquitectura se usa porque no todas las tareas tienen la misma naturaleza.

### El frontend esta separado porque:

- su trabajo es mostrar interfaz
- no debe contener logica de base de datos
- no debe ejecutar procesamiento interno

### El backend esta separado porque:

- centraliza la API
- controla acceso a datos
- decide cuando una tarea debe ejecutarse en segundo plano
- consulta pgvector cuando necesita contexto semantico para el asistente

### El processor esta separado porque:

- puede dedicarse solo a trabajos pesados o largos
- no bloquea las respuestas HTTP del backend
- permite escalar el procesamiento de forma independiente en el futuro
- expone un healthcheck operativo sin convertirse en la API publica del producto

## 8. Diferencia entre backend y processor

Es una duda muy comun al empezar.

La diferencia simple es:

- el `backend` responde a peticiones
- el `processor` ejecuta trabajos en segundo plano y expone un healthcheck interno

Ejemplo mental:

- `backend`: "He recibido tu solicitud"
- `processor`: "Ahora hago el trabajo interno necesario"

Separarlos mejora el orden del codigo y evita que una sola app haga demasiado.

## 9. Como pensar el sistema como junior

Una buena forma de entenderlo es verlo por capas:

- **capa de interfaz**: `frontend`
- **capa de API y coordinacion**: `backend`
- **capa de procesamiento**: `processor`
- **capa de infraestructura**: `RabbitMQ`, `CockroachDB` y `Postgres + pgvector`

Si te preguntas "donde va esta logica", puedes usar estas reglas:

- si es interfaz o experiencia visual, va en `frontend`
- si es endpoint, validacion o coordinacion de peticiones, va en `backend`
- si es retrieval del asistente contra chunks ya indexados, lo coordina el `backend`
- si es trabajo asincrono o pipeline interno, va en `processor`
- si es almacenamiento transaccional, va en `CockroachDB`
- si es paso de trabajos entre servicios, va en `RabbitMQ`
- si es almacenamiento vectorial para embeddings, va en `Postgres + pgvector`

## 10. Ejemplo real dentro de este repo

Un caso tipico de ingesta seria este:

1. El frontend pide crear un job de ingesta.
2. El backend recibe la peticion.
3. El backend crea el registro del job en la base de datos.
4. El backend publica ese job en RabbitMQ.
5. El processor recoge el job.
6. El processor ejecuta el pipeline.
7. El processor genera chunks y embeddings.
8. El processor guarda los embeddings en `Postgres + pgvector`.
9. El processor actualiza el estado del job en la base de datos.
10. El frontend puede consultar despues el estado actualizado a traves del backend.

Un caso tipico de chat con retrieval seria este:

1. El frontend envia un mensaje del usuario al backend.
2. El backend valida autenticacion y tenant.
3. El backend guarda o carga la conversacion desde CockroachDB.
4. El backend genera un embedding de la pregunta.
5. El backend busca chunks relevantes en `Postgres + pgvector`.
6. El backend construye la respuesta del asistente usando ese contexto.
7. El backend guarda los mensajes en CockroachDB.
8. El frontend muestra la respuesta.

## 11. Resumen rapido

La arquitectura de este proyecto se basa en dividir responsabilidades:

- `frontend` muestra la interfaz
- `backend` expone la API, coordina y consulta pgvector para el asistente
- `processor` procesa trabajos en segundo plano
- `processor` tambien expone un healthcheck interno
- `RabbitMQ` mueve jobs de procesamiento entre servicios
- `CockroachDB` guarda la informacion operativa del sistema
- `Postgres + pgvector` guarda embeddings y chunks

Si recuerdas solo una idea, que sea esta:

**cada submodulo tiene una responsabilidad concreta, y se comunican entre si para formar una sola aplicacion completa.**
