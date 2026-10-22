## MODIFIED Requirements

### Requirement: El usuario puede cambiar de tema desde el armazón

El armazón SHALL ofrecer un control accesible para alternar entre el tema claro y el oscuro, con nombre accesible y estado actual indicados sin depender solo del color, y el cambio SHALL aplicarse a toda la interfaz sin recargar la página. El texto visible del control SHALL nombrar el tema activo: «Tema claro» con el tema claro y «Tema oscuro» con el oscuro, junto a un icono que también lo represente. El nombre accesible del control SHALL coincidir con ese texto visible en ambos estados.

#### Scenario: Alternar tema

- **WHEN** el usuario activa el control de tema
- **THEN** todas las pantallas, las gráficas y los diálogos pasan al otro tema sin recargar
- **AND** el control indica cuál es el tema activo

#### Scenario: Texto del control con el tema claro activo

- **WHEN** la aplicación se presenta en tema claro, por preferencia del sistema o por elección guardada
- **THEN** el control muestra el texto «Tema claro» y el icono del sol
- **AND** no muestra el texto «Tema oscuro»

#### Scenario: Texto del control con el tema oscuro activo

- **WHEN** la aplicación se presenta en tema oscuro, por preferencia del sistema o por elección guardada
- **THEN** el control muestra el texto «Tema oscuro» y el icono de la luna

#### Scenario: El texto sigue al tema al alternar y al recargar

- **WHEN** el usuario alterna el tema y después recarga la página
- **THEN** tras alternar, el texto pasa a nombrar el nuevo tema activo sin recargar
- **AND** tras recargar, el texto nombra el tema guardado

#### Scenario: Nombre accesible igual al texto visible

- **WHEN** una tecnología de apoyo lee el control en cualquiera de los dos temas
- **THEN** su nombre accesible es exactamente el texto visible, «Tema claro» o «Tema oscuro»
