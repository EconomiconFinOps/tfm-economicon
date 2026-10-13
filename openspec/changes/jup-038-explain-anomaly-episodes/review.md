# Revisión de jup-038-explain-anomaly-episodes

JUP: JUP-038
Trello: https://trello.com/c/QzkjVY7P

Registro de ejecución del `apply`, grupo a grupo. El resultado final, el checklist y el gate
posterior a la revisión se completan al terminar el grupo 10. Nada de lo que no figure aquí con su
comando y su resultado se da por validado.

## Grupo 1 — Preparación y contrato (tareas 1.1 a 1.3)

**Excepción doc-only.** El grupo solo escribe documentación (evidencia, contrato y una nota en el
ADR), sin código de producto ni comportamiento testeable: no hay ciclo tester/coder, ni mutación, ni
QA de código. Se registra aquí como pide el flujo.

| Tarea | Resultado | Archivo |
| --- | --- | --- |
| 1.1 | Evidencia abierta con fecha, rama, SHA base (`bfaf3983`), enlace a Trello y los cinco criterios, todos pendientes salvo el 3 («en curso») | `docs/evidence/JUP-038-validation.md` |
| 1.2 | Contrato de la petición, respuestas, evidencia, fórmulas y correspondencia con el resultado común de herramientas, con ejemplo calculado a mano | `docs/api/anomaly-explanations.md` |
| 1.3 | Nota fechada en ADR-0020 con la decisión de no registrar herramienta y el aplazamiento del punto 11; el estado y el texto de la decisión no cambian | `docs/adr/ADR-0020-cost-anomaly-episodes.md` |

**Comprobaciones ejecutadas el 2026-10-12** (sobre `feat/JUP-038-explain-anomaly-episodes`, con
`develop` aún en `bfaf3983`):

- `corepack pnpm openspec:validate`: 68 de 68.
- `corepack pnpm jup:check -- --change jup-038-explain-anomaly-episodes` y
  `corepack pnpm jup:cleanup:check` (1301 archivos): correctos.
- `git diff --check`: sin avisos.
- Enlaces relativos y anclas de los tres documentos, con un comprobador propio: 0 rotos.
- Texto sin doble codificación UTF-8 en los tres documentos.

**Ejemplo de 1.2.** Calculado con un script independiente del backend, con aritmética exacta y sin
usar sus constantes: 150.00 EUR de subida absoluta, 37.50 % de subida relativa, 400.00 EUR de
impacto acumulado en 2 días hasta el 2026-09-09 y criticidad P3. Coincide con la salida del ejemplo
ejecutable de `docs/api/anomaly-episodes.md`. Los tres bordes de redondeo del contrato (subida
100.004, subida relativa 20.0002 % e impacto 499.996) están calculados en el mismo script. No se ha
ejecutado todavía ningún código de este change.

**Lo que este grupo no demuestra.** Que el explicador produzca esas cifras (grupo 2), que la ruta
las guarde (grupo 4) o que la interfaz las muestre (grupos 5 a 7). El contrato describe lo acordado,
no comportamiento implementado, y así lo dice su cabecera.
