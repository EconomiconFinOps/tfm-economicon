# Integración futura de JUP-072 a JUP-077

Estado: preparada localmente; no publicar hasta confirmar el repositorio oficial
y crear o acordar la rama remota `develop`.

## Cadena local

```text
main (4aee5d7)
  └─ JUP-072  dataset público y auditoría
     └─ JUP-073  contrato Azure Cost Query
        └─ JUP-074  API falsa base
           └─ JUP-075  resiliencia, autenticación y paginación
              └─ JUP-076  cliente de ingesta resiliente
                 └─ JUP-077  normalización y persistencia E2E
```

Cabezas verificadas:

| Tarjeta | Commit |
| --- | --- |
| JUP-072 | `61262c9` |
| JUP-073 | `e4d34e6` |
| JUP-074 | `9dae75c` |
| JUP-075 | `2d2f455` |
| JUP-076 | `215f54c` |
| JUP-077 (implementación desplegada) | `e81b898` |

Ramas locales:

- `docs/JUP-072-audit-azure-dataset`;
- `docs/JUP-073-azure-cost-query-contract`;
- `feat/JUP-074-azure-cost-api`;
- `feat/JUP-075-azure-api-resilience`;
- `feat/JUP-076-azure-cost-ingestion-client`;
- `test/JUP-077-azure-cost-e2e`.

Cada rama contiene las anteriores. No se ha publicado ninguna de estas ramas.
En la auditoría del 2026-08-08, `origin` apunta a
`https://github.com/ParisArcos/tfm-economicon.git`, pero solo se observó
`origin/main`; el `develop` existente es local y no demuestra un acuerdo del
equipo.

## Integración recomendada

Una vez confirmado el remoto, crear `develop` desde la base acordada y abrir un
único draft PR desde la cabeza de JUP-077. Así se conserva la historia por
tarjeta sin repetir commits en seis PR. Título propuesto:

```text
feat(azure-cost): integrate public fixture through persistence (JUP-072..077)
```

Antes de publicarlo:

1. `git fetch --prune origin` y confirmar la base de `origin/develop`;
2. rebasar la pila completa si la base acordada no es `4aee5d7`;
3. repetir tests, build y recorrido E2E desde la cabeza de JUP-077;
4. publicar únicamente la rama integradora;
5. abrir el draft PR hacia `develop`, nunca hacia `main`;
6. enlazar las seis tarjetas y sus evidencias;
7. solicitar las revisiones humanas asignadas en Trello.

No se considera integrado hasta que el equipo confirme el remoto y `develop`,
las personas revisoras aprueben y el PR quede fusionado.
