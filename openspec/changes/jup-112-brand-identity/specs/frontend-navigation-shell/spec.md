## ADDED Requirements

### Requirement: El armazón presenta la marca de Economicon

El armazón común SHALL mostrar el nombre "Economicon" y el monograma de marca en su cabecera, y NO SHALL mostrar el nombre ni el icono del prototipo anterior ("FinOps AI Platform", "FinOps Control Tower"). La navegación activa SHALL distinguirse con tokens del tema, sin usar el violeta reservado a botones.

#### Scenario: Cabecera sin identidad antigua

- **WHEN** se abre cualquier pantalla del armazón
- **THEN** la cabecera muestra "Economicon" y el monograma
- **AND** no aparece el texto "FinOps AI Platform" ni el título de pestaña "FinOps Control Tower"

#### Scenario: Elemento de navegación activo

- **WHEN** una ruta está activa en la navegación
- **THEN** su elemento se distingue del resto con un token del tema distinto del violeta de botones
- **AND** la distinción no depende solo del color (borde o peso tipográfico)

### Requirement: El tema define una paleta clara y una oscura con los mismos tokens

El tema SHALL definir dos paletas, una clara activa por defecto y una oscura que se activa mediante un atributo del documento, y ambas SHALL declarar exactamente el mismo conjunto de tokens, cada uno con una sola definición por paleta. NO SHALL existir una tercera paleta ni tokens que solo existan en una de ellas, y cada token SHALL tener al menos un consumidor.

#### Scenario: Las dos paletas tienen los mismos tokens

- **WHEN** se inspecciona la definición del tema
- **THEN** el conjunto de tokens de color de la paleta clara es idéntico al de la oscura
- **AND** cada token está definido una sola vez en cada paleta

#### Scenario: La paleta oscura depende del atributo

- **WHEN** el documento no declara el tema oscuro
- **THEN** pantallas y componentes compartidos se presentan con la paleta clara

#### Scenario: Token sin consumidor

- **WHEN** un token declarado no lo usa ninguna pantalla, componente ni gráfica
- **THEN** la batería de pruebas del frontend falla señalando el token

## REMOVED Requirements

### Requirement: El tema define una única paleta activa

**Reason**: JUP-099 fijó una única paleta oscura. JUP-112 introduce un tema claro y uno oscuro, así que "una única paleta" deja de ser cierto.

**Migration**: Sustituido por "El tema define una paleta clara y una oscura con los mismos tokens": se conserva la garantía de que no hay tokens huérfanos ni definiciones duplicadas.

### Requirement: La unificación de colores no altera el aspecto de las pantallas

**Reason**: Era un requisito de la migración de JUP-099 (sustituir colores literales por tokens sin cambiar píxeles). JUP-112 cambia a propósito la paleta y el aspecto, así que ese criterio ya no puede cumplirse ni aplica a un cambio de marca.

**Migration**: La coherencia visual pasa a verificarse con los requisitos de `frontend-brand-identity` (paleta, contraste, tipografía y revisión en pantalla en ambos temas); la evidencia previa de JUP-099 queda como histórica.
