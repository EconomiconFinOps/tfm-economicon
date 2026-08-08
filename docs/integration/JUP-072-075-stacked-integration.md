# Integración futura de JUP-072 a JUP-075

Estado: preparada localmente; publicación pendiente de confirmar el repositorio
de trabajo del equipo.

En la auditoría del 2026-08-08, `origin` apunta a
`https://github.com/ParisArcos/tfm-economicon.git`, `origin/main` coincide con
el `main` local y no existe `origin/develop`. Esta observación no demuestra que
sea el remoto definitivo ni autoriza publicar. Si el equipo confirma este
repositorio, deberá acordar y crear `develop` antes del PR, manteniendo la regla
de no integrar trabajo directamente sobre `main`.

## Cadena verificada

```text
main (4aee5d7)
  └─ JUP-072  40daa7c + 61262c9  dataset y auditoría
       └─ JUP-073  e4d34e6       contrato Azure Cost Query
            └─ JUP-074  9dae75c  servicio FastAPI normal
                 └─ JUP-075  8592829  resiliencia, auth y paginación
```

Ramas locales:

- `docs/JUP-072-audit-azure-dataset`;
- `docs/JUP-073-azure-cost-query-contract`;
- `feat/JUP-074-azure-cost-api`;
- `feat/JUP-075-azure-api-resilience`.

Cada rama contiene íntegramente las anteriores. No deben abrirse cuatro PR
independientes contra `main` con todos los commits repetidos.

## Estrategia recomendada al confirmar el remoto

La opción preferida es un único PR integrador desde
`feat/JUP-075-azure-api-resilience` hacia `develop`. Conserva la historia por
JUP, permite revisar el recorrido completo y evita depender del merge de cuatro
PR encadenados. El título propuesto es:

```text
feat(azure-cost): integrate public fixture and resilient fake API (JUP-072..075)
```

Antes de publicarlo:

1. obtener el remoto confirmado y ejecutar `git fetch --prune`;
2. comprobar que `origin/develop` existe y que su commit base sigue siendo
   `4aee5d7`; si no coincide, rebasar la pila completa una sola vez;
3. ejecutar las pruebas y el smoke test Docker desde la cabeza de JUP-075;
4. publicar únicamente la rama integradora;
5. abrir un draft PR hacia `develop`, nunca hacia `main`;
6. enlazar JUP-072, JUP-073, JUP-074 y JUP-075, sus evidencias y el despliegue
   de prueba en `dockerserver`;
7. solicitar la revisión humana según los roles rotatorios de cada tarjeta.

Comandos orientativos, que no deben ejecutarse hasta confirmar el remoto:

```bash
git fetch --prune origin
git log --oneline --reverse origin/develop..feat/JUP-075-azure-api-resilience
git diff --check origin/develop...feat/JUP-075-azure-api-resilience
git push -u origin feat/JUP-075-azure-api-resilience
```

## Alternativa: PR apilados

Si el equipo exige un PR por tarjeta, las bases deben encadenarse así:

| PR | Base | Head |
| --- | --- | --- |
| JUP-072 | `develop` | `docs/JUP-072-audit-azure-dataset` |
| JUP-073 | JUP-072 | `docs/JUP-073-azure-cost-query-contract` |
| JUP-074 | JUP-073 | `feat/JUP-074-azure-cost-api` |
| JUP-075 | JUP-074 | `feat/JUP-075-azure-api-resilience` |

Tras cada merge se cambia la base del siguiente PR. Esta alternativa ofrece
revisiones más pequeñas, pero exige más coordinación y puede producir ruido al
actualizar las bases.

## Gates de integración

- worktree limpio y sin secretos reales;
- `python -m unittest discover -s scripts/tests -v` en verde;
- `python -m pytest tests -v` en `apps/azure-cost-api` en verde;
- OpenAPI válido con Redocly;
- imagen y servicio Compose `healthy` en `dockerserver`;
- recorrido completo de todas las páginas sin duplicados;
- comprobación externa de `401`, `403`, `429`, `500`, timeout, página vacía y
  datos inválidos;
- aprobación humana y evidencia de participación de los cuatro miembros.

No se considera integrada ninguna tarea hasta completar estos gates y fusionar
el PR acordado. Las ramas locales y Trello son trazabilidad, no sustituyen la
revisión del equipo.
