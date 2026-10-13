JUP: JUP-116

## Context

Ver `proposal.md` para el motivo. Estado actual del frontend (`develop` en `3c6517b`):

- `src/routes.tsx` monta bajo `SessionGate` y `Layout` diez rutas. Tres son de demostración sin ninguna petición (`/operational`, `/cuts`, `/recommendations`), y `/overview-legacy` es la ruta puente de JUP-095.
- `src/layouts/Layout.tsx` tiene dos listas de menú (`navItems`, con las cinco pantallas heredadas del origen, y `backendNavItems`, con cuatro) separadas por una línea vertical que distinguía «demostración» de «datos reales». Esa distinción ya no es fiable: Coste Global, de la primera lista, es real, y Anomalías conserva datos de demostración pero los rotula.
- No hay ninguna ruta comodín: una dirección desconocida muestra la pantalla de error por defecto de React Router.
- `/overview-legacy` la usan como vehículo de una petición autenticada 34 líneas de 9 archivos de pruebas y de soporte de pruebas, y `frontend-navigation-shell` exige que el resumen de facturación conserve dirección propia.
- Las pruebas de las tres pantallas (`OperationalCostDashboard`, `ExecutiveCutDashboard`, `RecommendationsPanel`, `savings-coral`) montan el componente directamente, sin pasar por el enrutador.

## Goals / Non-Goals

**Goals:**

- Que ninguna pantalla de demostración sin rótulo sea alcanzable desde la interfaz ni por dirección, sin borrar su código, sus datos ni sus pruebas. Anomalías, que sí declara visiblemente su origen, sigue publicada.
- Que reactivar una de ellas sea añadir una ruta y una entrada de menú, sin reescribir pantalla ni datos.
- Que una dirección antigua (marcador, enlace compartido) no deje al operador en una pantalla de error.

**Non-Goals:**

- Retirar `/overview-legacy`, su hook o sus pruebas (`RF-105-001` sigue abierto).
- Un interruptor de configuración para activar o desactivar las pantallas.
- Cambiar nada de las pantallas con datos reales ni del backend.

## Decisions

**1. Quitar rutas y entradas de menú; no borrar archivos.** `routes.tsx` deja de importar las tres pantallas, y `Layout.tsx` deja de listarlas. Los archivos de `src/pages/`, `src/data/demo/` y sus pruebas no se tocan. Fue la opción elegida por Lucia el 2026-10-12 frente a un interruptor de build (`VITE_SHOW_DEMO_SCREENS`): el interruptor reactivaría sin editar código, pero añade un mecanismo de configuración, dos modos que probar y que las pruebas dependan de su valor, para tres pantallas que el MVP no va a mostrar. Reactivar una pantalla son dos líneas (ruta y entrada), que el README describirá.

**2. `/overview-legacy` se oculta del menú pero conserva su ruta.** Ocultarla del todo obligaría a reescribir 34 líneas de 9 archivos de pruebas y de soporte de pruebas que la usan como vehículo, con el riesgo de perder cobertura de sesión caducada y de aislamiento por cliente, y chocaría con la spec vigente (el resumen de facturación conserva dirección). Dejarla en el menú mantendría dos pantallas casi iguales (Coste Global y Overview) que el equipo ve como confusas. Se opta por quitar solo la entrada: no se ve en la demo y no se rompe nada. Es una excepción explícita en la spec (el segundo requisito modificado) y deja `RF-105-001` abierto con su inventario actualizado. Alternativa descartada: retirar la ruta y reescribir las pruebas, que queda para la tarjeta que cierre ese finding.

**3. Ruta comodín hacia la pantalla inicial.** Se añade `{ path: "*", element: <Navigate to="/" replace /> }` como hija de `Layout`, de modo que `SessionGate` actúa antes (sin sesión, la dirección lleva al acceso, como hoy) y con sesión el operador cae en Coste Global con el armazón y el ámbito intactos. Se usa `replace` para que Atrás no devuelva a la dirección oculta. Alternativa descartada: una pantalla «no encontrada» propia: más código y diseño para un caso que la demo no necesita. Efecto lateral aceptado: cualquier dirección desconocida, no solo las ocultas, redirige a `/` en lugar de mostrar el error del enrutador.

**4. Menú de una sola lista.** `navItems` y `backendNavItems` se fusionan en una sola, sin el separador, en el orden Coste Global, Anomalías, Ingestions, Assistant, Salud del sistema. El separador existía para distinguir demostración de datos reales; con Anomalías (rotulada) como única pantalla de demostración, ya no separa dos grupos. Los rótulos no se cambian (el idioma mixto queda fuera de alcance).

**5. Las pruebas que usaban Coste Detallado como ejemplo pasan a una pantalla publicada.** Las tres pruebas de `routes.integration.test.tsx` (abrir directamente, conservar el ámbito, redirigir sin sesión) usan `/operational` porque solo exige `/tenants`; se pasan a `/ingest`, que tampoco consulta nada más al montarse. `Layout.test.tsx` deja de esperar las tres etiquetas ocultas y pasa a afirmar su ausencia. Se añaden pruebas de: cada dirección oculta redirige a la inicial con el ámbito conservado, el menú no contiene las ocultas ni Overview, y `/overview-legacy` se presenta sin enlace. Las pruebas con sesión llevan su control positivo (fallan con la ruta restaurada o sin el comodín); las de «sin sesión» son escenario de la spec y control de que el comodín no se salta `SessionGate`, pero pasarían también sin él.

**5b. Las pruebas de las pantallas ocultas se conservan.** Siguen ejecutándose porque montan el componente. Dejan de acreditar que la pantalla sea alcanzable; el README lo dirá.

**6. Documentación.** La tabla «Rutas» del README añade una sección de pantallas no publicadas y rehace el recuento: 5 pantallas con menú y datos del backend, 1 ruta puente sin menú, 3 no publicadas. Los demás documentos solo se corrigen donde afirman que las pantallas se pueden abrir o que hay tres pantallas de demostración publicadas. Los findings: `RF-104-004` se cierra (ya no hay pantalla de demostración publicada sin rótulo), y `RF-095-002`, `RF-091-003` y `RF-105-001` se actualizan sin cerrarse.

**ADR:** no se necesita. La decisión es reversible con dos líneas, no fija arquitectura ni contrato, y no cambia dependencias. La revisión lo anotará.

## Risks / Trade-offs

- **Código sin ruta que se pudre** (nadie lo monta, tsc y lint lo comprueban pero no el navegador) → sus pruebas siguen montándolo y el README documenta cómo reactivarlo. Si se reactiva meses después puede necesitar ajustes.
- **La ruta comodín esconde direcciones mal escritas** → aceptado; en una aplicación con sesión y menú, ir a la inicial es menos dañino que una pantalla de error.
- **`/overview-legacy` sigue alcanzable por dirección** → intencionado y declarado en la spec; no se enlaza ni se documenta en la guía de la demo.
- **Referencias a las pantallas en documentos históricos** (evidencias de JUP-095 a JUP-099, ADR-0003) → no se reescriben: son registro de lo ocurrido; solo se corrigen los documentos vigentes.
- **El guion de la demo de JUP-107 y su `esperados.json`** mencionan las pantallas como «no abrir»; el fichero lo valida una prueba, así que se edita junto con ella y se vuelve a ejecutar.
