# JUP-134: etiqueta del selector de tema y limitaciones de anomalías en español

Motivación y alcance en [proposal.md](proposal.md); requisitos en los deltas de
`frontend-brand-identity` y `cost-anomaly-episodes`.

## Context

**Selector de tema.** `ThemeToggle.tsx` lee `theme` de `useTheme`. Con `isDark` elige el icono (sol o
luna) y fija `aria-pressed`, pero el `<span>` tiene el texto fijo «Tema oscuro». El botón funciona como
botón de alternancia: su nombre accesible es «Tema oscuro» y `aria-pressed` dice si está activo. Las
pruebas de `useTheme.test.tsx` (once casos) y `brand-spec.guard.test.tsx` buscan el botón por ese
nombre, y tres de ellas comprueban `aria-pressed`.

**Limitaciones.** `anomaly_episodes.py` define `LIMITATIONS`, cinco frases en inglés que
`episode_payload` devuelve en cada episodio. Se calculan al leer, no se guardan en la base de datos. El
panel las pinta tal cual (`AnomaliesPanel.tsx`). Por su parte, `anomaly_explanations.py` mantiene
`LIMITATIONS_ES`, la traducción en el mismo orden, que el asistente usa en el texto y en
`anomaly_evidence.limitations`. Una prueba exige que las dos listas tengan la misma longitud y que cada
traducción difiera del original.

La evidencia de una explicación guarda el episodio tal como estaba (`episode`, que incluye sus
`limitations`), y el identificador `anomaly-explanation:<sha256>` se calcula sobre todo ese cuerpo. El
identificador no se vuelve a comprobar al leer: solo se calcula al explicar.

## Goals / Non-Goals

**Goals:**
- El texto del selector nombra el tema activo y su nombre accesible es exactamente ese texto.
- Una sola lista de limitaciones, en español, compartida por la API de episodios, el panel y el asistente.
- Una prueba automática que falle si una limitación vuelve a quedar en inglés.

**Non-Goals:**
- Cambiar `useTheme`, el script de arranque de `index.html`, las paletas o la clave de almacenamiento.
- Traducir las limitaciones de `app/schemas/anomalies.py`: van en la evaluación de `/billing`, que
  ninguna pantalla muestra.
- Cambiar `schema_version` o `adapter_version` de la explicación, o reescribir explicaciones guardadas.
- Ampliar `apps/frontend/tests/spanish-ui.test.ts`. Recorre el código del frontend y el texto en inglés
  no está ahí, sino en el backend; la regresión se cubre con una prueba del backend.

## Decisions

### D1. El selector deja de ser un botón de alternancia con `aria-pressed`

El botón muestra el tema activo («Tema claro» o «Tema oscuro»), sin `aria-pressed` y sin `aria-label`.
Su nombre accesible es su contenido de texto, y el icono sigue con `aria-hidden`. Para que quede claro
qué hace al pulsarlo, lleva `title` con la acción («Cambiar a tema oscuro» o «Cambiar a tema claro»).
Ese `title` es una descripción accesible, no el nombre, porque el botón ya tiene contenido de texto.

Alternativas descartadas:
- *Mantener `aria-pressed` con el nombre cambiante*: un lector de pantalla diría «Tema claro, botón de
  alternancia, no pulsado» y luego «Tema oscuro, pulsado». Si el nombre cambia con el estado, el estado
  pulsado no tiene un significado estable.
- *Texto fijo «Tema oscuro» con `aria-pressed`*: es accesible, pero es justo lo que la tarjeta pide
  corregir.
- *Texto con la acción («Cambiar a tema oscuro»)*: no cumple lo pedido, que el texto diga el tema en uso.

Así se sigue cumpliendo el requisito de indicar el estado sin depender solo del color: lo dicen el texto
y el icono.

### D2. Las limitaciones se traducen en origen y hay una sola lista (opción A)

`LIMITATIONS` de `anomaly_episodes.py` pasa a contener las cinco frases que hoy tiene `LIMITATIONS_ES`,
con la misma redacción y en el mismo orden. `anomaly_explanations.py` importa `LIMITATIONS` y elimina
`LIMITATIONS_ES`. El texto del asistente no cambia, porque ya usaba esas frases.

Alternativas descartadas:
- *B. Traducir en el frontend con una tabla*: duplica la lista en otro lenguaje, y una frase nueva o
  cambiada en el backend volvería a verse en inglés sin que nada fallara.
- *C. Servir `LIMITATIONS_ES` desde la API y dejar `LIMITATIONS` en inglés*: mantiene dos listas, y la
  lista en inglés no la mostraría nadie.

La spec `frontend-spanish-ui` («Valores de la API sin traducir») no cambia: el frontend sigue pintando
el valor de la API tal cual, y el cambio de idioma ocurre en el origen.

### D3. Las pruebas existentes se reescriben, no se borran

- `useTheme.test.tsx`: los casos que buscan «Tema oscuro» con el sistema en claro pasan a buscar
  «Tema claro». Las comprobaciones de `aria-pressed` se sustituyen por el texto visible y por la ausencia
  del atributo. Se añaden casos para el texto tras alternar, tras recargar con una elección guardada y
  para el `title`.
- `brand-spec.guard.test.tsx`: el conmutador se busca por el nombre que corresponde al tema de la prueba.
- `test_anomaly_explanations.py`: la prueba «una traducción por cada limitación» pasa a comprobar que la
  explicación usa la misma lista que el episodio. La literal `LIMITATIONS_ES_LITERAL` se conserva como
  redacción esperada, que es también la de `LIMITATIONS`.
- Prueba de regresión nueva en el backend: el episodio devuelve las cinco frases en español y ninguna de
  las cinco frases en inglés anteriores.

### D4. Sin ADR

Es una corrección de textos y de la semántica accesible de un control que ya decidió ADR-0012 (enmienda
JUP-112). No hay una decisión de arquitectura duradera.

## Risks / Trade-offs

- [Una anomalía sin cambios obtiene otro identificador de evidencia si se explica antes y después del
  despliegue, porque la fotografía del episodio incluye sus limitaciones] → Se acepta y se documenta. Las
  explicaciones guardadas no se reescriben y el identificador no se comprueba al leer. Tras el
  despliegue, el escenario «Mismo estado, mismo identificador» se sigue cumpliendo.
- [Las explicaciones guardadas antes del cambio conservan dentro de `episode.limitations` las frases en
  inglés] → El frontend muestra `evidence.limitations`, que ya estaba en español, y no
  `evidence.episode.limitations`. Es historia guardada y no se migra.
- [Un consumidor externo que dependiera del texto en inglés] → No hay ninguno: solo el frontend usa el
  endpoint de episodios y lo pinta sin interpretarlo.
- [Quitar `aria-pressed` cambia el rol que anuncian los lectores de pantalla (de botón de alternancia a
  botón)] → Es lo que se busca. El estado lo dicen el texto y el icono, y la acción el `title`.

## Migration Plan

No hay migración de datos. Se despliega con el ciclo normal de backend y frontend. Para deshacerlo basta
con revertir el commit: no hay estado guardado que dependa del cambio.
