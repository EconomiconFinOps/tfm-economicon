# JUP-035 - Correcciones de CI

Fecha: 2026-10-11. Correcciones locales sobre `7daabf0`, autorizadas por Paris
segun el encargo trasladado por PM. No incluyen commit, push ni nueva CI remota.

## Causas y cambios

- Backend y processor: `requirements-dev.txt` incluye `requirements.txt`, que
  no declaraba `tokenizers` aunque los locks e imagenes ya lo incluian.
  Se declara la misma version `0.22.1` en ambos manifiestos de produccion.
  No se cambia la version ni se incorpora una biblioteca nueva al runtime.
- La prueba de recursos calculaba el repositorio como `/workspace` y exigia
  copiar exclusivamente summary/v2. Ahora deriva la raiz desde `__file__` y
  verifica el empaquetado completo de summary y su carga en ambos Dockerfiles.
  Sus escenarios v2 siguen usando explicitamente el bundle historico v2.
- `react-hooks/exhaustive-deps` de `eslint-plugin-react-hooks` 4.6.2 usaba
  `context.getSource`, retirado en ESLint 9. Se fija el plugin de desarrollo
  en 5.2.0, compatible con ESLint 9, y se regenera el lock sin otros cambios
  de paquetes. No se desactiva ni modifica ninguna regla.
- Los fixtures de `local-doctor` omitian `CHAT_HMAC_FILE`, ya obligatorio en
  Compose. Se incorpora una ruta sintetica al fixture y a la lista esperada.
  No se modifica Compose, el diagnostico ni la autenticacion.

Referencia de la API de ESLint:
[migracion a v9](https://eslint.org/docs/latest/use/migrate-to-9.0.0).

## Comprobaciones afectadas

| Comprobacion | Resultado |
| --- | --- |
| Instalacion pnpm con lock congelado y sin scripts | PASS; solo un paquete nuevo descargado, plugin de lint |
| Lint frontend, mismas reglas `src tests` | 0 errores, 1 aviso sobre la dependencia `current` en ChatPresentation |
| local-doctor y local-smoke | 74 PASS, sin omisiones |
| Recursos summary backend en `/checkout`, no `/workspace` | 54 PASS, avisos heredados de SQLite |
| Coleccion backend con Python 3.12 | 1667 casos recogidos, sin errores; NO ejecutados |
| Coleccion processor con Python 3.12 | 1026 casos recogidos, sin errores; NO ejecutados |
| Manifiestos CI y lock de tokenizers frente a imagenes existentes | PASS en ambos servicios, version 0.22.1 |
| CI workflow y topologia Docker | 47 PASS |
| `git diff --check` | PASS |

Las comprobaciones Python usan imagenes locales ya existentes, sin red y con
fuentes readonly. No equivalen a instalar desde cero todas las dependencias de
CI. El lint usa Node 24 en Windows; tooling tambien se ejecuto con Node 20 en
Linux. CI usa Node 22: la siguiente ejecucion remota debe confirmar su resultado.

Los intentos iniciales conservan sus fallos: corepack sin DNS en sandbox, copia
Docker sin permisos, copia incompleta de las reglas del processor e imagen sin
pytest. Se corrigio el ejecutor de comprobacion, no se ocultaron fallos del
producto. No se ejecutaron las suites completas, ensayos funcionales, llamadas
de OpenRouter ni cambios de servicios existentes para esta correccion.

Logs y referencia SHA256 de los seis archivos iniciales bajo la ruta local
`e5-context-compression-evidence/restart-20261011/ci-corrections/`, junto al
worktree entregado al PM. `original.csv` es referencia local de este delta,
no un reemplazo de las referencias originales ni un guard del PM.
