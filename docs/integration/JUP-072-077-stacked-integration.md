# Integración del recorrido JUP-072 a JUP-077

Repositorio oficial: `https://github.com/EconomiconFinOps/tfm-economicon`.
Rama común: `develop`. Cada tarea se desarrolla en su rama `JUP-*` y se
integra mediante un pull request independiente; nunca se trabaja sobre `main`.

## Cadena integrada

| Tarjeta | Responsabilidad | Pull request hacia `develop` |
| --- | --- | --- |
| JUP-072 | Dataset público Microsoft y auditoría reproducible | [#4](https://github.com/EconomiconFinOps/tfm-economicon/pull/4) |
| JUP-073 | Contrato versionado Azure Cost Management Query | [#5](https://github.com/EconomiconFinOps/tfm-economicon/pull/5) |
| JUP-074 | API simulada y consulta contractual | [#6](https://github.com/EconomiconFinOps/tfm-economicon/pull/6) |
| JUP-075 | Autenticación local, paginación y resiliencia | [#7](https://github.com/EconomiconFinOps/tfm-economicon/pull/7) |
| JUP-076 | Cliente de ingesta seguro, paginado y resiliente | [#8](https://github.com/EconomiconFinOps/tfm-economicon/pull/8) |
| JUP-077 | Normalización, persistencia e integración E2E | Rama `test/JUP-077-azure-cost-e2e` |

El recorrido resultante es:

```text
fixture público de Microsoft
  → API simulada Azure Cost Management Query
  → cliente HTTP paginado y resiliente
  → normalización de importes, divisas, fechas y dimensiones
  → ejecuciones y registros aislados por tenant en CockroachDB
```

No se necesitan tenant Azure, credenciales Microsoft ni anonimización del
dataset, que ya es público. Trello mantiene las responsabilidades y el estado
operativo; OpenSpec recoge requisitos, diseño y escenarios; GitHub conserva el
código, la evidencia y la revisión de cada pull request.

## Validaciones de integración

1. Actualizar la rama de tarea desde `origin/develop` y conservar las mejoras
   de autenticación, contrato, resiliencia y paginación previamente integradas.
2. Ejecutar las suites del simulador, processor, backend, contrato compartido,
   frontend, OpenSpec, trazabilidad `JUP-*` e higiene del repositorio.
3. Ejecutar contra Docker en `dockerserver` la ingesta paginada de 30 filas,
   su repetición idempotente, el aislamiento por tenant y el `401` controlado.
4. Publicar exclusivamente la rama de JUP-077, abrir su PR hacia `develop`,
   enlazar la evidencia en Trello y verificar de nuevo el commit integrado.
