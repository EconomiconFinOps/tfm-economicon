# JUP-048 — Cierre de la revision de `setup/open-spec`

Fecha inicial: 2026-08-08. Reconciliacion final: 2026-08-26.

## Decision

No se integro `setup/open-spec` como fuente de planificacion ni se adopto su
inventario `HU-*`. Se seleccionaron sus cambios utiles, posteriormente
reconciliados y limpiados mediante JUP-082. El `develop` actual conserva
OpenSpec oficial, ADR, pruebas de health, credenciales demo coherentes y el
flujo Trello/JUP; excluye binarios de Engram, configuracion personal de agentes
y numeracion paralela.

La rama `setup/open-spec` es ahora ancestro de `develop`, pero su estado
historico no debe usarse como base de trabajo. Trello sigue siendo la fuente
operativa y OpenSpec la evidencia tecnica versionada.

## Hallazgos resueltos

- Las referencias rotas al antiguo plan OpenSpec/HU fueron eliminadas.
- `tools/engram/engram.exe` y el tooling no portable fueron retirados.
- Las propuestas `HU-*` dejaron de presentarse como trabajo implementado.
- `jup:check` valida la correspondencia entre Trello y OpenSpec.
- `jup:cleanup:check` impide reintroducir configuracion personal, binarios de
  plataforma o namespaces de tareas paralelos.
- El CI ejecuta estos validadores en cada pull request.

## Trabajo deliberadamente separado

- Los 49 errores heredados de `react/prop-types` siguen registrados como
  `RF-082-002` y necesitan su propia tarjeta.
- `setup/sdd` no esta integrada y necesita una revision independiente antes de
  recuperar o descartar sus cambios.
- Los accesos y owners de la organizacion se verifican como gobernanza remota;
  no se deducen de la visibilidad publica del repositorio.

Esta revision sustituye la propuesta local antigua de publicar
`chore/JUP-048-integrate-open-spec`: esa rama estaba basada en el `main` inicial
y sus cambios validos ya quedaron incorporados por tareas posteriores.
