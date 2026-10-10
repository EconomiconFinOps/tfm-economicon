JUP: JUP-054
Trello: https://trello.com/c/ZsxwmagI

## Why

La primera pasada de JUP-054 (PR #93, integrada en `develop` en `1f57f91` el 2026-10-10) añadió
siete pruebas de integración, la matriz `docs/testing/critical-flows.md`, la evidencia
`docs/evidence/JUP-054-validation.md` y la spec `critical-flow-testing`. Su change está archivado en
`openspec/changes/archive/2026-10-10-jup-054-test-strategy-and-critical-flows/`. Se cerró por
excepción de plazo del MVP, sin pairing ni reviews humanas independientes, y la tarjeta deja
pendiente comprobar la cobertura del candidato final y cubrir los huecos.

Esa pasada eligió los límites a probar leyendo las suites, no midiendo: el repositorio no tiene
ninguna herramienta de cobertura configurada, y la matriz declara que no fija un porcentaje. Además,
el candidato ha cambiado desde entonces. `develop` está en `e1c2a8f` con cinco PR posteriores a la
#93 (JUP-037, JUP-064, JUP-105, JUP-017 y JUP-068), que añaden rutas, servicios y componentes que la
matriz no recoge. Hoy nadie puede decir qué parte de los flujos críticos del candidato ejecuta de
verdad alguna prueba.

## What Changes

- **Fijar el candidato auditado**: el SHA de `develop` sobre el que se mide, con la ejecución de CI
  que le corresponde como referencia de pruebas aprobadas, fallidas y omitidas.
- **Medir la cobertura** de `apps/backend`, `apps/processor`, `apps/azure-cost-api` y
  `apps/frontend` sobre ese SHA, como diagnóstico. La herramienta de medición no se añade al
  repositorio (ver `design.md`, decisión 1).
- **Extender la matriz riesgo/suite** a lo integrado después de la PR #93 y contrastarla con la
  medición.
- **Clasificar cada hueco** de un flujo crítico: cubierto con una prueba nueva, aceptado con su
  motivo, o diferido como hallazgo `RF-054-NNN` en `openspec/findings/backlog.md`.
- **Añadir las pruebas** de los huecos críticos, comprobando que cada una falla cuando se rompe el
  comportamiento que dice cubrir.
- **Registrar el resultado** en una sección fechada de `docs/evidence/JUP-054-validation.md`, sin
  reescribir los resultados de la primera pasada, y actualizar la matriz y la continuidad.

No se modifica código de producto, dependencias, `pnpm-lock.yaml` ni `.github/workflows/ci.yml`. No
se fija un umbral de cobertura ni se convierte en requisito de ningún check. No se reescriben ni se
duplican las pruebas de la PR #93. Si una prueba nueva revela un defecto, se registra como hallazgo
y no se corrige aquí.

## Capabilities

### New Capabilities

<!-- Ninguna. La auditoría de cobertura pertenece a la capacidad que ya publicó la primera pasada. -->

### Modified Capabilities

- `critical-flow-testing`: se añaden tres requisitos. La auditoría de cobertura de un candidato
  fijado y repetible, el tratamiento obligatorio de cada hueco detectado, y el carácter diagnóstico
  de la cifra de cobertura. Los tres requisitos vigentes (trazabilidad riesgo/suite, regresiones de
  componentes críticos y ejecución obligatoria sin caché) no cambian.

## Impact

- **Nuevo:** archivos de prueba en `apps/backend/tests/`, `apps/processor/tests/`,
  `apps/azure-cost-api/tests/` y `apps/frontend/` según los huecos críticos que apruebe la
  auditoría; filas `RF-054-NNN` en `openspec/findings/backlog.md` si queda algo diferido.
- **Modificado:** `docs/testing/critical-flows.md` (matriz extendida y comandos de medición),
  `docs/evidence/JUP-054-validation.md` (sección nueva), `docs/continuidad/README.md` y
  `docs/continuidad/pruebas-unitarias-integradas.md`; al archivar,
  `openspec/specs/critical-flow-testing/spec.md`.
- **Solo lectura:** `apps/*/app/**`, `apps/frontend/src/**` salvo archivos `*.test.*` nuevos,
  `packages/**`, `tools/**`, `.github/**`, `docker-compose.yml`, `package.json`, `pnpm-lock.yaml` y
  los tres `requirements*.txt`.
- **Fuera del repositorio:** los contenedores desechables de medición, los informes de cobertura
  generados y las versiones de la herramienta, que se anotan en la evidencia.
- **Fuera de alcance:** provisionar servicios reales en CI (`RF-096-004`), salvo que la auditoría lo
  señale como hueco crítico y se acuerde ampliarlo; Azure cloud, LLM externo, gateway LiteLLM real,
  Compose completo y navegador real; los fallos de la suite en Windows descritos en la evidencia de
  la primera pasada; la cobertura de `tools/**`, que tiene sus propias pruebas en el check
  `OpenSpec`.
- **Candidato en movimiento:** hay ramas `feat/` abiertas en `origin`. Si `develop` recibe cambios
  de aplicación antes de entregar, se repite la medición de lo afectado o se declara qué queda sin
  auditar (ver `design.md`, decisión 3).
- **Entrega:** esta pasada sigue el flujo ordinario de revisión y validación de `CONTRIBUTING.md`.
  La excepción de plazo que cerró la PR #93 no se extiende a esta rama.
- **ADR:** no aplica; no se añade ninguna dependencia ni se cambia la arquitectura (ver
  `design.md`, decisión 8).
