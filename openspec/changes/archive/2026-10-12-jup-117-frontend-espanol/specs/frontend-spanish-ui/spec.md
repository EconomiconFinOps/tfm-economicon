## ADDED Requirements

### Requirement: Textos visibles en español
El frontend SHALL mostrar en español todo texto que la persona usuaria pueda ver o que lea una tecnología de apoyo: títulos de página y de sección, botones, etiquetas y marcadores de campo, textos de ayuda, estados de carga, estados vacíos, mensajes de error, mensajes de éxito, etiquetas de accesibilidad (`aria-label`, `title`, `alt`) y el título del documento. Esto SHALL aplicarse a todas las pantallas y componentes de `apps/frontend/src`. Los mensajes de error internos que lanzan los servicios y los hooks sin llegar a mostrarse como texto propio de la interfaz quedan fuera.

#### Scenario: Pantalla de conversaciones
- **WHEN** se abre la pantalla de conversaciones con y sin cliente activo
- **THEN** el título, la ayuda, el campo de nuevo título, los estados de carga y vacío y los mensajes de error propios de la interfaz se muestran en español

#### Scenario: Pantalla de acceso
- **WHEN** se abre la pantalla de acceso, se envía el formulario y mientras la sesión se está iniciando
- **THEN** el encabezado, la descripción, el botón en reposo y el botón en curso se muestran en español

#### Scenario: Error al cargar los clientes
- **WHEN** falla la carga de clientes al arrancar la sesión
- **THEN** el título, el encabezado y el botón de restablecer sesión se muestran en español

#### Scenario: Etiquetas de accesibilidad
- **WHEN** un componente declara `aria-label`, `title` o `alt`
- **THEN** el valor está en español, salvo excepción del glosario

### Requirement: Excepciones técnicas justificadas
El frontend MAY mantener en inglés un término técnico únicamente si figura en el glosario `apps/frontend/GLOSARIO.md` con su motivo. Un término que no figura en el glosario SHALL mostrarse en español. El glosario SHALL indicar, para cada concepto con varias formas posibles, el nombre único que usa la interfaz.

#### Scenario: Término técnico conservado
- **WHEN** la interfaz muestra un término en inglés como nombre propio de producto o concepto sin traducción de uso habitual
- **THEN** ese término aparece en el glosario con su motivo

#### Scenario: Concepto con un solo nombre
- **WHEN** el mismo concepto aparece en dos o más pantallas
- **THEN** se escribe igual en todas, según el nombre fijado en el glosario

### Requirement: Valores de la API sin traducir
El frontend SHALL mostrar tal cual los valores que llegan de la API o de la persona usuaria (nombres de servicios de Azure, etiquetas de coste, títulos de conversaciones, contenido de documentos y mensajes del asistente). El cambio de idioma SHALL aplicarse solo a los textos propios de la interfaz. Las etiquetas que la interfaz pone sobre un valor cerrado de la API (rol del mensaje y estado de servicio) SHALL estar en el glosario, y un valor que no esté en él SHALL mostrarse sin traducir. Los datos de demostración fijos de las pantallas de maqueta (`src/data/demo`) se tratan como valores de datos.

#### Scenario: Rol del mensaje y estado de servicio
- **WHEN** un mensaje llega con el rol `user` o `assistant`, o un servicio con estado `ok`, `degraded`, `failed` o `unknown`
- **THEN** la interfaz muestra la etiqueta en español de la tabla del glosario
- **AND** un rol o un estado que no está en la tabla se muestra tal cual, sin error

#### Scenario: Nombre de servicio de Azure
- **WHEN** una tabla muestra el servicio `Virtual Machines` devuelto por la API
- **THEN** se muestra `Virtual Machines` sin modificar, aunque el resto de la tabla esté en español

### Requirement: Sin regresión a inglés
El repositorio SHALL incluir una prueba automática que recorra los ficheros de interfaz de `apps/frontend/src` y falle si encuentra, como texto visible, una de las frases o palabras en inglés ya traducidas por este change. La prueba SHALL ignorar comentarios, imports, nombres de variables, rutas, claves de objeto, ficheros de prueba y los términos del glosario.

#### Scenario: Reaparece un texto en inglés
- **WHEN** se añade a una página un botón con el texto `Sign in`
- **THEN** la prueba falla indicando el fichero y el texto

#### Scenario: Término del glosario
- **WHEN** una página usa un término que el glosario conserva en inglés
- **THEN** la prueba no falla

#### Scenario: Comentario o identificador en inglés
- **WHEN** hay una palabra en inglés en un comentario, una variable o una ruta
- **THEN** la prueba no falla
