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
- `packages/shared-config`

Y ademas hay dos servicios de infraestructura:

- `CockroachDB`
- `RabbitMQ`

Cada pieza tiene una responsabilidad distinta.

## 3. Que hace cada submodulo

### `apps/frontend`

Es la parte visual del sistema.

Es la aplicacion que ve el usuario en el navegador. Su trabajo principal es:

- mostrar informacion
- pedir datos al backend
- enseñar el estado general del sistema

El frontend **no habla directamente** con la base de datos ni con RabbitMQ.
Siempre pasa por el backend.

## `apps/backend`

Es la API principal del sistema.

Su trabajo es recibir peticiones HTTP, validar datos y coordinar operaciones.

Por ejemplo, el backend:

- responde al frontend
- consulta o guarda datos en la base de datos
- crea jobs de procesamiento
- envia esos jobs a RabbitMQ

El backend es como el punto central de entrada para las peticiones normales de la aplicacion.

### `apps/processor`

Es el servicio que hace trabajo en segundo plano.

No esta pensado para que el usuario hable con el directamente desde la interfaz. Su trabajo es:

- escuchar jobs pendientes en RabbitMQ
- procesarlos
- ejecutar el pipeline interno
- guardar resultados o actualizar estados en la base de datos

Esto permite que las tareas pesadas o lentas no bloqueen al backend.

### `packages/shared-config`

Es un paquete compartido del monorepo.

Ahora mismo es pequeño, pero su objetivo es ser un lugar comun para poner:

- configuraciones compartidas
- constantes
- convenciones del workspace
- utilidades comunes del lado JavaScript

No es un servicio que se ejecute solo. Es una pieza de apoyo.

## 4. Que papel tienen RabbitMQ y CockroachDB

### CockroachDB

Es la base de datos principal del sistema.

Aqui se guarda la informacion importante, por ejemplo:

- tenants
- jobs
- estados de ejecucion
- resultados de procesamiento

Piensa en CockroachDB como la memoria permanente del sistema.

### RabbitMQ

Es el sistema de colas.

Sirve para pasar trabajo del backend al processor sin que ambos tengan que hacer todo al mismo tiempo.

Piensa en RabbitMQ como una bandeja de tareas pendientes:

- el backend deja un trabajo en la cola
- el processor recoge ese trabajo
- el processor lo procesa cuando le toca

Esto desacopla servicios y hace la arquitectura mas robusta.

## 5. Relacion entre los submodulos

La relacion principal entre las piezas es esta:

1. El usuario usa el `frontend`
2. El `frontend` llama al `backend` por HTTP
3. El `backend` guarda o consulta datos en `CockroachDB`
4. Si hace falta procesamiento asincrono, el `backend` publica un job en `RabbitMQ`
5. El `processor` consume ese job desde `RabbitMQ`
6. El `processor` procesa el trabajo y actualiza `CockroachDB`
7. El `backend` puede devolver despues informacion actualizada al `frontend`

## 6. Flujo simplificado

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
                         |
                         v
                    CockroachDB
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

### El processor esta separado porque:

- puede dedicarse solo a trabajos pesados o largos
- no bloquea las respuestas HTTP del backend
- permite escalar el procesamiento de forma independiente en el futuro

## 8. Diferencia entre backend y processor

Es una duda muy comun al empezar.

La diferencia simple es:

- el `backend` responde a peticiones
- el `processor` ejecuta trabajos en segundo plano

Ejemplo mental:

- `backend`: "He recibido tu solicitud"
- `processor`: "Ahora hago el trabajo interno necesario"

Separarlos mejora el orden del codigo y evita que una sola app haga demasiado.

## 9. Como pensar el sistema como junior

Una buena forma de entenderlo es verlo por capas:

- **capa de interfaz**: `frontend`
- **capa de API y coordinacion**: `backend`
- **capa de procesamiento**: `processor`
- **capa de infraestructura**: `RabbitMQ` y `CockroachDB`

Si te preguntas "donde va esta logica", puedes usar estas reglas:

- si es interfaz o experiencia visual, va en `frontend`
- si es endpoint, validacion o coordinacion de peticiones, va en `backend`
- si es trabajo asincrono o pipeline interno, va en `processor`
- si es almacenamiento persistente, va en la base de datos
- si es paso de trabajos entre servicios, va en RabbitMQ

## 10. Ejemplo real dentro de este repo

Un caso tipico seria este:

1. El frontend pide crear un job de ingesta.
2. El backend recibe la peticion.
3. El backend crea el registro del job en la base de datos.
4. El backend publica ese job en RabbitMQ.
5. El processor recoge el job.
6. El processor ejecuta el pipeline.
7. El processor actualiza el estado del job en la base de datos.
8. El frontend puede consultar despues el estado actualizado a traves del backend.

## 11. Resumen rapido

La arquitectura de este proyecto se basa en dividir responsabilidades:

- `frontend` muestra la interfaz
- `backend` expone la API y coordina
- `processor` procesa trabajos en segundo plano
- `RabbitMQ` mueve jobs entre servicios
- `CockroachDB` guarda la informacion del sistema

Si recuerdas solo una idea, que sea esta:

**cada submodulo tiene una responsabilidad concreta, y se comunican entre si para formar una sola aplicacion completa.**
