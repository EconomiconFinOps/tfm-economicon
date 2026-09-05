JUP: JUP-092

## Context

Última tarjeta de F1 y la única de carril `standard`: produce una **decisión de arquitectura**, no un
inventario. Las dos anteriores dejaron el terreno medido:

- **JUP-090** ([línea base del destino](../../../docs/planning/JUP-090-frontend-migration-baseline.md)):
  `apps/frontend` es JavaScript con JSX, 14 archivos en `src/`, sin `typescript` ni tipos declarados.
- **JUP-091** ([inventario del origen](../../../docs/planning/JUP-091-economicon-source-inventory.md)):
  el origen es TSX **sin `tsconfig` ni dependencia `typescript`** — nunca se ha verificado. De sus 61
  dependencias, 48 están clasificadas `DESCARTAR`, y los 48 componentes de `ui/` (shadcn) son código
  muerto que ninguna pantalla importa.

Estado verificado del repo hoy:

- **No existe ningún `tsconfig.json`** en todo el árbol.
- `apps/frontend` acumula **49 violaciones de `react/prop-types`** (recuento reproducido en esta HU),
  el motivo por el que su lint no es check obligatorio de CI (`RF-082-002`,
  [github-branch-protection.md](../../../docs/governance/github-branch-protection.md)).
- `apps/frontend` no tiene tests: su script `test` es `echo "No frontend tests configured yet"`.
- Existe `packages/shared-config` (`@finops/shared-config`), hoy con un único `index.js` de
  metadatos del workspace.
- Backend y processor son Python: TypeScript sería el primer código tipado del lado JavaScript.

El ADR es obligatorio por [docs/adr/README.md](../../../docs/adr/README.md) (patrones compartidos que
afectan a varios módulos y tareas futuras) y por la decisión nº 1 del spike.

## Goals / Non-Goals

**Goals:**

- Producir `docs/adr/ADR-0003-frontend-typescript.md` con las cuatro decisiones que bloquean F2
  resueltas de forma inequívoca, sin dejar ninguna como "se verá en F2".
- Documentar honestamente las consecuencias negativas, no solo los beneficios.
- Registrar las alternativas descartadas con su motivo, para que la decisión sea auditable.
- Dejar el ADR en `Accepted` y enlazado desde el spike, desbloqueando F2 y F3.

**Non-Goals:**

- Instalar `typescript`, `@types/react` o `@types/react-dom` (F2).
- Crear `tsconfig.json` ni `tsconfig.node.json` (F2).
- Migrar `eslint.config.js` al parser de TypeScript (F2).
- Renombrar archivos `.jsx` → `.tsx` ni tocar código de `apps/frontend` (F3).
- Decidir la versión de Vite (5 vs 6): decisión propia de F2, ya registrada en el inventario de
  JUP-091 como la única dependencia `SUSTITUIR`.
- Decidir si se adopta shadcn/ui (`RF-091-002`): es decisión de F2, aunque el ADR debe reconocer que
  **afecta al coste de la adopción de TS** (menos superficie que tipar si se descarta).

## Decisions

Estas son decisiones **sobre cómo se produce el ADR**. Las decisiones técnicas que el ADR contendrá
se proponen abajo, en "Posiciones propuestas", y requieren aprobación del equipo antes de fijarse.

- **ADR-0003, numeración correlativa.** Es el siguiente número libre (existen `ADR-0001` y
  `ADR-0002`), según la convención de `docs/adr/README.md`. Nombre de archivo
  `ADR-0003-frontend-typescript.md`, el slug que ya reserva el spike.

- **El ADR se redacta primero en `Proposed` y pasa a `Accepted` en un paso separado.** Lo exige el
  flujo de `docs/adr/README.md` ("keep its status `Proposed` during review"). Se traduce en dos
  tareas y dos commits distintos, para que el historial muestre la revisión.

- **Cada una de las cuatro decisiones se resuelve con una posición explícita.** El criterio de
  aceptación es que F2 pueda ejecutarse sin volver a preguntar. Una decisión redactada como
  "dependerá de" no se acepta.

- **Las consecuencias se escriben en ambas direcciones.** La plantilla pregunta "what becomes easier,
  harder, riskier". Un ADR que solo enumere ventajas no es auditable ni creíble; el coste real
  (errores latentes del origen nunca verificados, curva de aprendizaje) se documenta.

- **El ADR no reabre lo ya decidido.** La adopción de TypeScript *en sí* ya está decidida en el
  spike; este ADR la formaliza y define **cómo**. Si durante la redacción apareciera un motivo de
  peso para no adoptarla, se para y se escala en vez de decidirlo aquí.

## Posiciones propuestas para el ADR (requieren aprobación del equipo)

No las fijo unilateralmente: son la propuesta de partida que el ADR recogerá y el equipo aprobará o
corregirá en el gate.

1. **Nivel de rigor → `strict: true` desde el inicio.** El frontend se reemplaza por completo, así
   que no hay deuda heredada que migrar gradualmente: el momento más barato para exigir rigor es
   antes de escribir el código nuevo. Retrofitear `strict` sobre un frontend ya portado sería mucho
   más caro. *Riesgo asumido:* el TSX del origen nunca se ha verificado y aflorarán errores latentes
   al compilarlo por primera vez; el coste real depende de `RF-091-002` (descartar shadcn/ui reduce
   drásticamente la superficie a tipar).

2. **Convivencia → `allowJs: true` durante la migración, `false` al cerrar F5.** El spike prohíbe
   explícitamente el "big bang" y manda avanzar por slices verificables; con `allowJs: false` desde
   el día uno, el primer slice rompería el build de todo lo aún no migrado. La tarjeta de cierre de
   F5 lo endurece a `false` una vez no quede JavaScript.

3. **CI → type-check como check obligatorio, y `RF-082-002` se cierra por obsolescencia.** El
   type-check debe correr en CI; si no, `strict` es decorativo. Sobre las 49 violaciones de
   `react/prop-types`: la vía correcta **no es arreglarlas**, sino que la regla deja de aplicar —
   `prop-types` es validación de tipos en runtime y TypeScript la sustituye en tiempo de compilación.
   Mantener ambas sería redundante. La propuesta es desactivar `react/prop-types` para archivos
   `.ts`/`.tsx` en F2 y cerrar `RF-082-002` como resuelto estructuralmente, documentándolo.

4. **`tsconfig` → a nivel de `apps/frontend`.** `packages/shared-config` existe pero hoy solo contiene
   un `index.js` con metadatos del workspace, y `apps/frontend` sería el **único** paquete TypeScript
   del repo (backend y processor son Python). Extraer una config base compartida para un solo
   consumidor es abstracción prematura. *Puerta de salida:* si más adelante aparece un segundo
   paquete TS, se extrae entonces un `tsconfig.base.json` a `shared-config`; el ADR lo deja
   registrado como evolución prevista, no como deuda.

## Risks / Trade-offs

- **El equipo puede no estar de acuerdo con las posiciones propuestas.** → Por eso van marcadas como
  propuesta y no como decisión; el gate pre-código es el punto donde se confirman o corrigen, antes
  de redactar el ADR como `Accepted`.
- **`strict: true` puede resultar más caro de lo estimado** si F2/F3 descubren que el TSX del origen
  arrastra muchos errores. → Mitigación: el ADR debe declarar el criterio de escape (si el coste
  desborda la tarjeta de F3, se documenta y se revisa el ADR, no se desactiva `strict` en silencio).
- **Riesgo de que el ADR invada F2.** Es tentador especificar `compilerOptions` completas. → El ADR
  fija las cuatro decisiones y su porqué; la configuración concreta es de F2.
- **Cerrar `RF-082-002` por obsolescencia toca gobernanza de CI**, que es territorio de JUP-079. → No
  se modifica ningún ruleset en esta HU: el ADR documenta la intención y F2 la ejecuta.

## Migration Plan

1. Redactar el ADR en estado `Proposed` sobre el commit base de la rama.
2. Aprobación del equipo sobre las cuatro decisiones (gate pre-código de esta HU).
3. Pasar el ADR a `Accepted` y enlazarlo desde el spike.
4. F2 y F3 citan el ADR en su `design.md`.
5. **Rollback:** revertir los ficheros de documentación. Sin impacto en runtime, build ni
   dependencias. Si la decisión se revisa más adelante, el mecanismo es un ADR nuevo que supersede a
   `ADR-0003`, nunca editar el aceptado.

## Open Questions

- ¿Se cierra `RF-082-002` en esta HU o se deja abierto hasta que F2 ejecute el cambio de lint? La
  propuesta es dejarlo abierto y anotar en él la resolución prevista, porque el finding no queda
  materialmente resuelto hasta que la regla se desactive.
- El ADR menciona que el coste de `strict` depende de `RF-091-002` (adopción o descarte de
  shadcn/ui), que se decide en F2. El ADR registra la dependencia sin resolverla.
