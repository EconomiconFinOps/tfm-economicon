JUP: JUP-134
Trello: https://trello.com/c/zg2LSCjb/126-jup-134

# Etiqueta del selector de tema y limitaciones de anomalías en español

## Why

Se encontraron dos fallos visibles en la interfaz. El botón de tema de la cabecera dice siempre
«Tema oscuro», también cuando el tema claro está activo, y no informa del tema en uso. Además, el
desplegable «Limitaciones» del detalle de una anomalía muestra cinco frases en inglés en una interfaz
que, desde JUP-117, está en español. Las frases salen de la API de episodios, que JUP-117 dejó fuera
porque eran valores de la API, mientras que el asistente ya muestra su propia traducción.

## What Changes

- El botón de tema muestra el tema activo: «Tema claro» con el icono del sol y «Tema oscuro» con la
  luna. El texto cambia al alternar y al recargar con la elección guardada. El nombre accesible sigue
  siendo el texto visible.
- Las limitaciones de los episodios de anomalía se redactan en español en el origen
  (`LIMITATIONS` de `anomaly_episodes.py`), con las mismas cinco frases y en el mismo orden. La API, el
  detalle del panel y la explicación del asistente comparten una sola lista y desaparece la copia
  `LIMITATIONS_ES`.
- **BREAKING (menor)**: el campo `limitations` de las respuestas de episodios pasa del inglés al
  español. El único consumidor es el frontend, que lo pinta tal cual. Las explicaciones ya guardadas no
  cambian, pero una anomalía explicada otra vez tras el cambio obtiene otro identificador de evidencia,
  porque la fotografía del episodio incluye sus limitaciones.
- Se actualizan las pruebas que dependen del texto fijo del botón y de la pareja inglés/español, y se
  añade una prueba de regresión que falla si vuelve a aparecer una limitación en inglés.

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

- `frontend-brand-identity`: el control de tema muestra como texto el tema activo («Tema claro» o
  «Tema oscuro») y su nombre accesible coincide con ese texto.
- `cost-anomaly-episodes`: la lista de limitaciones que devuelve cada episodio está redactada en
  español.

## Impact

- Frontend: `apps/frontend/src/components/ThemeToggle.tsx`, `src/hooks/useTheme.test.tsx`,
  `src/test/brand-spec.guard.test.tsx` y `apps/frontend/README.md`.
- Backend: `app/services/anomaly_episodes.py` (`LIMITATIONS`), `app/services/anomaly_explanations.py`
  (deja de definir `LIMITATIONS_ES`), `tests/test_anomaly_explanations.py` y las pruebas de episodios que
  usan la constante.
- No cambian: la lógica de `useTheme`, las paletas, el esquema de la base de datos (las limitaciones se
  calculan al leer), el contrato de tipos del frontend ni `adapter_version` de la explicación.
- Fuera de alcance, con motivo: las limitaciones por defecto de `app/schemas/anomalies.py`, que van en
  la respuesta de evaluación de `/billing` y ninguna pantalla muestra; el resto de valores de la API en
  inglés; la internacionalización completa.
- ADR: no aplica. Es una corrección de textos y de un control ya decidido en ADR-0012 (enmienda
  JUP-112).
- Documentación de continuidad: `docs/continuidad/frontend-espanol.md`,
  `docs/continuidad/identidad-marca-frontend.md` y `docs/continuidad/README.md`.
