# ADR-0015: Despliegue local reproducible y frontera de producción

- Status: Proposed
- Date: 2026-10-01
- Related JUP/OpenSpec: JUP-061, [registro de decisiones](../../openspec/changes/jup-061-architecture-decision-register/design.md)
- Trello: https://trello.com/c/qXoHFxyy
- Responsable de consolidación: Alejandro Aguado; revisión: Paris Arcos Martin; validación: Lucia Mateo; pairing previsto: Victor Mendez.
- Roles actualizados: 2026-10-03; intercambio Lucia/Victor documentado en [validación de Lucia](https://github.com/EconomiconFinOps/tfm-economicon/pull/60#pullrequestreview-5396865126). No acredita pairing realizado.
- Supersedes: none
- Superseded by: none

## Contexto

JUP-049 reconcilia la topología Docker existente y corrige el build del frontend.
Hay evidencia de un smoke de nueve servicios. Esa evidencia no selecciona hosting
productivo, alta disponibilidad ni operación multiusuario pública.

## Decisión documentada para ratificación

Conservar Docker Compose como baseline de demostración reproducible. La razón,
sintetizada del diseño JUP-049, es ejecutar las mismas aplicaciones y dependencias
con entradas de build fijadas, healthchecks y volúmenes, sin añadir un orquestador.
Los contenedores facilitan repetir pruebas; no hacen equivalentes todos los hosts.

## Alternativas y consecuencias

- Procesos instalados manualmente: menos contenedores, pero exige reproducir por
  separado versiones, dependencias y arranque; pierde el contrato único de Compose.
- Kubernetes o servicios gestionados: opciones futuras, sin comparación de coste,
  carga ni operación acreditada. No se declaran descartadas para producción.
- Migrador dedicado: alternativa tratada por JUP-096/JUP-050. El baseline
  integrado conserva el backend como dueño de jobs y bloquea el processor hasta
  que esté sano (ADR-0011); no introduce un migrador separado.

Se asumen recursos para nueve servicios y gestión explícita de persistencia y
secretos. Los digests de JUP-049 cubren cuatro bases de aplicación y tres imágenes
de infraestructura; Prometheus/Grafana conservan tags. Vite preview y la excepción
CockroachDB local no acreditan endurecimiento productivo. No se fija proveedor,
coste mensual ni garantía de recuperación productiva con este registro.

## Evidencias y aceptación pendiente

- [Diseño JUP-049](../../openspec/changes/archive/2026-09-09-jup-049-dockerize-services/design.md).
- [Evidencia de nueve servicios y límites](../evidence/JUP-049-validation.md).
- [Contrato integrado](../../openspec/specs/containerized-runtime/spec.md) y
  [Compose](../../docker-compose.yml).
- [PR #16](https://github.com/EconomiconFinOps/tfm-economicon/pull/16) y
  [cierre #32](https://github.com/EconomiconFinOps/tfm-economicon/pull/32), integradas.
- [PR #59, JUP-050](https://github.com/EconomiconFinOps/tfm-economicon/pull/59) y
  [PR #51, JUP-096](https://github.com/EconomiconFinOps/tfm-economicon/pull/51):
  integradas el 02/10 y 01/10/2026 UTC, respectivamente. El corte inicial del
  01/10 las registraba abiertas. [Evidencia JUP-050](../evidence/JUP-050-validation.md)
  y [ADR-0011](ADR-0011-single-owner-per-table.md) documentan el baseline integrado;
  sus merges no ratifican esta justificación retrospectiva.

Pendiente ratificar esta justificación retrospectiva y definir el despliegue final
en su tarea de origen; JUP-061 no elige un proveedor de producción.
