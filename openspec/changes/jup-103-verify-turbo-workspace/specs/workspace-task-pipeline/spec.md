## Purpose

Los scripts de la raíz del monorepo (`lint`, `build`, `test`, `typecheck` y `dev`) orquestan las
tareas de cada paquete con la versión del gestor de paquetes que fija el repositorio, de forma
reproducible en las máquinas del equipo y en CI, con el frontend como un paquete más del pipeline.

## ADDED Requirements

### Requirement: Los scripts de la raíz usan la versión fijada del gestor de paquetes

Los scripts de la raíz que orquestan tareas por paquete (`lint`, `build`, `test` y `typecheck`) SHALL
lanzar cada tarea con la versión del gestor de paquetes que declara el repositorio, tanto en el
proceso que inicia la orquestación como en los subprocesos de cada paquete.

#### Scenario: Batería desde la raíz en una máquina preparada

- **WHEN** una persona con el gestor de paquetes activado como indica la documentación del
  repositorio ejecuta `lint`, `build`, `test` y `typecheck` desde la raíz con la invocación
  documentada
- **THEN** cada paquete que declara el script recibe su tarea
- **AND** ninguna tarea termina con un error de versión del gestor de paquetes

#### Scenario: Integración continua

- **WHEN** un job de CI prepara el gestor de paquetes y ejecuta un script de la raíz
- **THEN** el script se completa sin error de versión del gestor de paquetes

### Requirement: El requisito previo del gestor de paquetes está documentado y se puede diagnosticar

La documentación de arranque del repositorio SHALL indicar el paso que hay que dar una vez por
máquina para que el gestor de paquetes fijado sea el que encuentran los subprocesos, y SHALL ofrecer
un comando de diagnóstico que distinga una máquina preparada de una que no lo está.

#### Scenario: Máquina preparada

- **WHEN** una persona ejecuta el comando de diagnóstico documentado desde la raíz en una máquina
  preparada
- **THEN** el comando termina con éxito
- **AND** muestra la versión del gestor de paquetes que fija el repositorio

#### Scenario: Máquina con otro gestor de paquetes por delante en la ruta de búsqueda

- **WHEN** una persona ejecuta el comando de diagnóstico en una máquina donde un gestor de paquetes
  de otra versión se resuelve antes que el fijado
- **THEN** el comando no imprime la versión que fija el repositorio: termina con un error de versión
  o imprime otra versión, según la del gestor de paquetes que se resuelva
- **AND** la documentación indica que cualquier salida distinta de la versión fijada significa que
  falta preparar la máquina y qué hacer para corregirlo

#### Scenario: Acción requerida al equipo

- **WHEN** una persona del equipo consulta la documentación de arranque
- **THEN** encuentra si tiene que hacer algo en su máquina, qué y cómo comprobar que ha funcionado

### Requirement: El script de desarrollo arranca las aplicaciones en paralelo

El script `dev` de la raíz SHALL arrancar en una misma ejecución el proceso de desarrollo de cada
aplicación del workspace que lo declara: frontend, backend, processor y Azure Cost API.

#### Scenario: Arranque conjunto

- **WHEN** una persona con las dependencias de cada aplicación instaladas, y con la configuración de
  cada aplicación disponible para su proceso, ejecuta `dev` desde la raíz
- **THEN** se inician los procesos de desarrollo de frontend, backend, processor y Azure Cost API sin
  esperar unos a otros
- **AND** el frontend atiende en el puerto 5173

### Requirement: El frontend participa en el grafo de tareas del workspace

El paquete del frontend SHALL formar parte del grafo de tareas del workspace con una tarea por cada
script orquestado desde la raíz, y la tarea `build` de cualquier paquete SHALL ejecutarse después de
la de los paquetes del workspace de los que depende.

#### Scenario: Tareas del frontend en el plan de ejecución

- **WHEN** se consulta el plan de ejecución de `lint`, `build`, `test`, `typecheck` y `dev` sin
  ejecutarlo
- **THEN** el frontend aparece con una tarea para cada uno de los cinco scripts

#### Scenario: Orden de build con dependencias internas

- **WHEN** un paquete del workspace declara como dependencia a otro paquete del workspace que tiene
  tarea `build`
- **THEN** el plan de ejecución coloca el `build` de la dependencia antes que el suyo
