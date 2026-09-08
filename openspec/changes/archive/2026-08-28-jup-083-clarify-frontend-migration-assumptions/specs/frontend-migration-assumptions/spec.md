## ADDED Requirements

### Requirement: Supuestos del origen confirmados y documentados

El spike de migración del frontend SHALL tener cada supuesto del repositorio origen (marcado como
`[ASUNCION]`) confirmado contra el repositorio Economicon e inventariado en el change, de forma que
ningún supuesto quede sin verificar antes de arrancar la implementación de la épica.

#### Scenario: Inventario completo sin supuestos pendientes

- **WHEN** se completa la inspección en solo lectura de Economicon para esta HU
- **THEN** `docs/spikes/frontend-migration.md` no contiene ninguna marca `[ASUNCION]`
- **AND** cada supuesto resuelto queda respaldado por una entrada en el inventario del `design.md`
  del change

#### Scenario: Hallazgo sin equivalente en el backend

- **WHEN** la inspección detecta que Economicon consume un endpoint o capacidad que el backend de
  tfm-economicon no ofrece
- **THEN** el hallazgo se registra en el `review.md` de la HU y en `openspec/findings/backlog.md`
  con un ID `RF-083-<secuencia>`, sin resolverse dentro de esta HU
