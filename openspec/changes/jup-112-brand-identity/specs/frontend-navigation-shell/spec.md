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

## REMOVED Requirements

### Requirement: La unificación de colores no altera el aspecto de las pantallas

**Reason**: Era un requisito de la migración de JUP-099 (sustituir colores literales por tokens sin cambiar píxeles). JUP-112 cambia a propósito la paleta y el aspecto, así que ese criterio ya no puede cumplirse ni aplica a un cambio de marca.

**Migration**: La coherencia visual pasa a verificarse con los requisitos de `frontend-brand-identity` (paleta, contraste, tipografía y revisión en pantalla); la evidencia previa de JUP-099 queda como histórica.
