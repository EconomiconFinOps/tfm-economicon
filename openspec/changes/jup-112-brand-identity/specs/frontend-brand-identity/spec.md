## Purpose

Define cómo la aplicación presenta la identidad visual de Economicon (paleta, tipografía y logotipo) y cómo se comportan los colores de estado y de gráficas que la guía de marca no cubre, de forma que sean coherentes con la marca y legibles.

## ADDED Requirements

### Requirement: La aplicación usa la paleta de marca sobre fondo claro

La aplicación SHALL presentarse sobre el blanco roto `#FAFAFC` como fondo base predominante, con el casi negro `#14121F` como color del texto principal, el índigo profundo `#2B2359` en la cabecera y en el texto de marca, y el lila claro `#E4E1FB` en los fondos de tarjetas y secciones suaves. El modo oscuro NO SHALL existir en esta versión.

#### Scenario: Superficie base y texto

- **WHEN** se carga cualquier pantalla de la aplicación
- **THEN** el fondo de la página es el blanco roto y el texto principal es el casi negro
- **AND** las tarjetas y secciones suaves usan el lila claro como fondo

#### Scenario: Sin tema oscuro

- **WHEN** el navegador está configurado en modo oscuro
- **THEN** la aplicación se presenta igual que en modo claro

### Requirement: El violeta es exclusivo de botones y llamadas a la acción

El violeta medio `#5B4FE8` SHALL aplicarse solo a botones y llamadas a la acción primarias, y NO SHALL usarse como color de texto corriente, de navegación, de gráficas ni de estados. Su presencia SHALL ser un acento: como máximo el 10 % de la superficie visible de una pantalla.

#### Scenario: Botón primario

- **WHEN** una pantalla muestra un botón de acción primaria (por ejemplo, iniciar sesión, crear ingesta, enviar mensaje)
- **THEN** el botón usa el violeta como fondo y su texto tiene un contraste de al menos 4,5:1

#### Scenario: Violeta fuera de su uso

- **WHEN** se inspecciona la navegación, las gráficas, las etiquetas de estado y el texto corriente
- **THEN** ninguno de ellos usa el violeta de botones

### Requirement: El coral es el único acento cálido y marca ahorro e insights

El coral `#FF8A5B` SHALL reservarse para destacar ahorro e insights, y NO SHALL usarse para indicar avisos, errores ni alarmas. Como su contraste sobre el blanco roto es insuficiente para texto, SHALL usarse como superficie, borde o elemento gráfico, y el texto sobre él SHALL ser el casi negro.

#### Scenario: Ahorro e insights

- **WHEN** una pantalla muestra una cifra o un bloque de ahorro o una recomendación
- **THEN** se destaca con el coral como acento

#### Scenario: Estados no usan el coral

- **WHEN** una pantalla muestra un aviso, un error o una anomalía
- **THEN** su color procede de la paleta de estados y no del coral

### Requirement: Los estados tienen colores propios, distinguibles y legibles

La aplicación SHALL definir colores para los estados éxito, aviso, peligro, información y neutro, coherentes con la marca y distintos entre sí y del coral y del violeta. Cada estado SHALL tener variantes de relleno suave, de borde y de texto, y NO SHALL transmitirse solo por el color: cada indicación de estado SHALL ir acompañada de texto o de un icono. Todo texto de estado SHALL tener un contraste de al menos 4,5:1 sobre el fondo en el que se muestra, y todo elemento gráfico de estado de al menos 3:1.

#### Scenario: Contraste de los pares de estado

- **WHEN** se evalúa, para cada estado, el texto de estado sobre su relleno suave, sobre el blanco roto y sobre el lila claro
- **THEN** todos los pares alcanzan al menos 4,5:1

#### Scenario: Estado accesible sin color

- **WHEN** una etiqueta de estado se muestra en escala de grises
- **THEN** sigue indicando el estado mediante su texto o su icono

#### Scenario: Estados distinguibles entre sí

- **WHEN** se muestran a la vez un estado de éxito, uno de aviso y uno de peligro
- **THEN** los tres se distinguen por tono, no solo por luminosidad

### Requirement: Las gráficas usan una paleta propia coherente con la marca

Las series de las gráficas SHALL usar una paleta definida en el tema, con al menos cinco tonos distinguibles entre sí sobre fondo claro, y ejes y rejillas en tonos apagados; NO SHALL usar el violeta de botones. Las leyendas y los tooltips SHALL ser legibles sobre el fondo de la tarjeta.

#### Scenario: Gráfica con varias series

- **WHEN** una gráfica muestra cinco series
- **THEN** cada serie tiene un color distinto con contraste de al menos 3:1 sobre el fondo de la tarjeta
- **AND** la leyenda identifica cada serie

### Requirement: La tipografía de marca está empaquetada con la aplicación

Los titulares y el nombre de marca SHALL usar Space Grotesk, y el cuerpo, las etiquetas y los datos SHALL usar Inter, ambas servidas desde los recursos de la propia aplicación (sin petición a terceros en ejecución), con una tipografía de sistema de respaldo mientras cargan.

#### Scenario: Fuentes servidas localmente

- **WHEN** se carga la aplicación y se inspeccionan las peticiones de red
- **THEN** las fuentes proceden del mismo origen que la aplicación

#### Scenario: Jerarquía tipográfica

- **WHEN** se muestra el título de una pantalla principal, un encabezado de sección y un párrafo
- **THEN** el título y el encabezado usan Space Grotesk en negrita y el párrafo usa Inter en peso regular

### Requirement: El monograma E identifica la aplicación

La cabecera SHALL mostrar el monograma E con el nombre "Economicon", usando la versión inversa sobre la cabecera índigo y la primaria sobre fondos claros (pantalla de acceso). El logotipo NO SHALL recolorearse, deformarse ni llevar efectos. El título de la pestaña del navegador SHALL contener "Economicon" y la aplicación SHALL declarar un favicon de marca.

#### Scenario: Cabecera de marca

- **WHEN** un usuario autenticado abre cualquier pantalla
- **THEN** la cabecera índigo muestra el monograma inverso y el nombre "Economicon"

#### Scenario: Pantalla de acceso

- **WHEN** un usuario no autenticado abre la aplicación
- **THEN** la pantalla de acceso muestra el monograma primario sobre fondo claro

#### Scenario: Pestaña del navegador

- **WHEN** la aplicación está abierta en una pestaña
- **THEN** el título contiene "Economicon" y la pestaña muestra el favicon de marca

### Requirement: Las pantallas se leen en escritorio y en móvil

Cada pantalla de la aplicación SHALL mostrarse legible, sin texto cortado ni solapes y sin desplazamiento horizontal de la página, en una anchura de escritorio (1280 px) y de móvil (390 px), incluidos los estados con datos, de carga, vacío y de error.

#### Scenario: Revisión visual por pantalla

- **WHEN** se captura cada pantalla en 1280 px y en 390 px con datos, en carga, vacía y con error
- **THEN** la revisión no encuentra texto ilegible, contenido cortado ni scroll horizontal de la página
