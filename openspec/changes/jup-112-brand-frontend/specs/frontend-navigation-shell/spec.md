## REMOVED Requirements

### Requirement: La unificación de colores no altera el aspecto de las pantallas

**Reason**: JUP-099 conservaba deliberadamente los píxeles de la interfaz original.
JUP-112 autoriza adaptar el aspecto a la guía de Economicon.
**Migration**: Conservar contratos funcionales y tokens semánticos; comprobar
la identidad y legibilidad en lugar de igualdad visual con el diseño oscuro.

## MODIFIED Requirements

### Requirement: El tema define una única paleta activa

El tema SHALL definir una única paleta clara de Economicon, activa sin depender
de clases, atributos ni preferencias de color del sistema. NO SHALL existir
una segunda paleta ni estilos oscuros activados por la preferencia del usuario.

#### Scenario: La paleta no depende de un ámbito declarado

- **WHEN** se carga la aplicación sin ninguna clase de tema en el documento
- **THEN** pantallas y componentes compartidos se presentan con la paleta clara de Economicon

#### Scenario: No hay paleta paralela

- **WHEN** se inspecciona la definición del tema
- **THEN** cada token de color tiene una sola definición
- **AND** no existe un bloque alternativo de tokens para otro tema

#### Scenario: La paleta clara no depende del sistema

- **WHEN** se carga la aplicación con preferencia de sistema clara u oscura
- **THEN** se muestran las mismas superficies claras y colores de Economicon
- **AND** cada token de color tiene una sola definición

## ADDED Requirements

### Requirement: La interfaz utiliza la identidad de Economicon

La aplicación SHALL utilizar índigo profundo para identidad, blanco roto como
base, lila en superficies suaves y texto casi negro. El violeta SHALL reservarse
a acciones sin dominar la pantalla y el coral a ahorro e insights. Los estados
y gráficas MAY usar tonos derivados para legibilidad sin depender solo del color.

#### Scenario: Marca coherente en acceso y pantallas autenticadas

- **WHEN** se abre el acceso o una pantalla del menú
- **THEN** aparece la identidad Economicon y se consumen los mismos tokens
- **AND** datos, rutas y operaciones mantienen su contrato previo

### Requirement: Tipografías y logotipos se sirven localmente

La interfaz SHALL usar Inter para cuerpo y Space Grotesk para titulares y marca,
con alternativas del sistema. SHALL servir fuentes y logotipos oficiales desde
la aplicación, conservando atribuciones y licencias. Un logotipo junto al nombre
SHALL ser decorativo para no duplicar su lectura por tecnología asistiva.

#### Scenario: Recursos de identidad disponibles sin CDN externo

- **WHEN** la aplicación renderiza marca y titulares
- **THEN** las fuentes y los PNG oficiales se cargan desde el propio origen
- **AND** no se requiere contactar un proveedor de fuentes externo

### Requirement: La adaptación mantiene legibilidad y navegación adaptable

Texto normal SHALL alcanzar contraste de al menos 4.5:1 sobre sus superficies.
Navegación y controles SHALL poder alcanzarse con teclado y mostrar foco visible.
Cabecera y contenido SHALL adaptarse a 320 píxeles sin desbordar el documento;
tablas o gráficos anchos MAY desplazar su contenido dentro de una región acotada.

#### Scenario: Pantalla estrecha con teclado

- **WHEN** el operador navega a 320 píxeles usando el teclado
- **THEN** puede alcanzar los enlaces y controles con foco visible
- **AND** la cabecera y el documento no requieren desplazamiento horizontal global

#### Scenario: Acción y estado sobre superficies claras

- **WHEN** se muestra una acción primaria o un aviso de error, carga o vacío
- **THEN** el texto conserva contraste legible y describe el estado sin depender del color
