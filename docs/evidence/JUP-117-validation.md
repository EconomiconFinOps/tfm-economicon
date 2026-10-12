# Evidencia de validación JUP-117

Tarjeta: [JUP-117](https://trello.com/c/B4832TYk). Change: `openspec/changes/jup-117-frontend-espanol/` (tras archivar, `openspec/changes/archive/`).

Esta evidencia recoge lo que se ejecutó al implementar el change. **No es una validación independiente**: esa corresponde a quien tenga el rol de validación en la tarjeta.

## Entorno

- Rama `feat/JUP-117-frontend-espanol` sobre `develop` `3c6517b`.
- Servidor de desarrollo de Vite de la rama, en `http://localhost:5173`, contra el stack Docker Compose local ya levantado (backend, CockroachDB y RabbitMQ) con la cuenta de demostración y el cliente Core Finance. Windows, Docker Desktop.
- Recorrido con `playwright-core` y Chromium (revisión `1243`), ejecutado fuera del repositorio.

## Pruebas automáticas

| Comprobación | Resultado |
| --- | --- |
| Vitest del frontend (`apps/frontend`) | 794 de 794 en la ejecución final |
| `eslint src tests` | sin avisos |
| `corepack pnpm build` | correcto |
| `corepack pnpm openspec:validate` | 66 de 66 |
| `corepack pnpm jup:check -- --change jup-117-frontend-espanol` | correcto |
| `corepack pnpm jup:cleanup:check` | correcto |

La prueba nueva `apps/frontend/tests/spanish-ui.test.ts` falló antes de traducir (60 textos en inglés encontrados en el código) y pasa después. Incluye los casos de la spec: texto en inglés en un botón, en varias líneas, junto a expresiones y con otras mayúsculas; términos del glosario; y comentarios, importaciones, rutas, claves de objeto y atributos no visibles.

**Prueba intermitente:** en ejecuciones de la suite completa fallaron sin cambios de producto de forma aleatoria de uno a tres tests de acceso y sesión (`login-session-expired-notice*`, `auth-session`) por esperas agotadas bajo carga; sueltos pasan. Es la intermitencia ya registrada en JUP-061 y JUP-064; no se ha medido contra `develop`.

## Recorrido visual con el stack real

Se recorrieron `/login` y las nueve pantallas del menú (Coste Global, Coste Detallado, Corte Global, Anomalías, Recomendaciones, Ingesta, Asistente, Resumen, Salud del sistema) en tres configuraciones: escritorio 1440 px en tema claro, escritorio 1440 px en tema oscuro y móvil 390 px en tema claro. 30 capturas fuera del repositorio.

- Ninguna pantalla muestra textos propios de la interfaz en inglés. El rastreo automático de palabras inglesas solo marcó falsos positivos: «Total» y «error» (también son español), «Data Lake» (nombre de proyecto de los datos de demostración), «billing» (ejemplo de URI `s3://billing/report.csv`) y el identificador de cliente `tenant-core` que devuelve la API dentro de un mensaje.
- Sin desborde horizontal en ninguna pantalla ni configuración y sin errores de página.
- Revisadas a ojo las capturas de acceso (claro), ingesta (oscuro) y asistente (móvil): los textos más largos que los anteriores caben sin cortarse.
- No se recorrió el flujo de error de red ni el de sesión caducada en el navegador; esos textos se comprueban solo con las pruebas automáticas.

## Lo que no se tradujo y por qué

- Valores que devuelve la API (nombres de servicio de Azure, etiquetas de coste, planes, títulos de conversación, mensajes del asistente).
- Mensajes de error que genera la capa de API (`Request failed for…`, `Invalid response for…`) y los errores del navegador (`Failed to fetch`): decisión de Lucia de dejar fuera la capa de API. Pueden verse en pantalla si el backend falla.
- Términos técnicos del glosario `apps/frontend/GLOSARIO.md` (backend, gateway, endpoint, embeddings, Compute/Storage/Network de los datos de demostración).
- Formato de importes con `toLocaleString()` sin código de idioma en las pantallas de demostración: depende del navegador.

## Criterios de aceptación de la tarjeta

| Criterio | Estado |
| --- | --- |
| Ninguna pantalla con texto visible en inglés salvo términos justificados | Cumplido en las nueve pantallas y el acceso (recorrido y prueba) |
| Excepciones listadas con su motivo | Cumplido (`GLOSARIO.md`) |
| El mismo concepto se nombra igual en todas las pantallas | Cumplido para los conceptos del glosario; el tratamiento de tú/usted no está unificado en la pantalla de salud del sistema |
| Errores, estados vacíos, títulos de página y etiquetas de accesibilidad en español | Cumplido salvo los errores de la capa de API indicados arriba |
| Pruebas, documentación y decisiones actualizadas | Cumplido; falta la validación independiente por el rol de validación |
