JUP: JUP-114 · ADR: [ADR-0020](../../../../docs/adr/ADR-0020-cost-anomaly-episodes.md) (se actualiza: se quita el límite de 7 días)

## Context

Ver `proposal.md`. Estado de partida tras el change 1 (`openspec/changes/archive/2026-10-12-jup-114-persisted-anomalies/`):

- Backend: `POST /billing/anomalies/detect`, `GET /billing/anomalies/episodes[?scope=]`, `GET` y `PATCH /billing/anomalies/episodes/{id}`; `detection_window` limita cada ejecución a los 7 días pendientes más recientes; la lista no devuelve la marca de agua, ni el origen de los datos, ni totales.
- Frontend: `AnomaliesPanel.tsx` lee `data/demo/anomaliesPanel.ts`; `services/api.ts` (`fetchJson` con token, `X-Tenant-Id`, validación y generación de sesión), `services/contracts.ts` (validadores), TanStack Query con claves por tenant y generación, `useMutation` en otras pantallas, `components/ui/dialog.tsx` (Radix) y `costCents` en `lib/executiveCostDashboard.ts` para céntimos exactos con `BigInt`.
- Demo: `scripts/synthetic_anomalies.py` carga 22 registros semanales en `tenant-core`; el guion de 3 minutos (`docs/demo/JUP-107/guion.md`, D1–D11) usa `tenant-growth` con los datos de JUP-106; la receta de navegador recorre esos pasos.

## Goals / Non-Goals

**Goals:** panel conectado según las decisiones de UX de la exploración (ver la spec `anomalies-panel`), ejecución sin límite de días, datos de demo diarios con P1, P2, P3 y las dos observaciones, y la demo de 3 minutos con el paso de Anomalías.

**Non-Goals:** ejecución periódica y avisos (change 3), explicación con el agente (JUP-038), permisos por rol, histórico de estados, paginación de la lista (el volumen de la demo y del MVP es pequeño; se registra si hace falta).

## Decisions

**D1. Ejecución sin límite de días.** `detection_window` recibe el primer día observado del tenant: en la primera ejecución evalúa desde ese día (los 7 primeros se saltan como `reference_incomplete`) y en las siguientes todos los días tras la marca de agua. Desaparecen `MAX_DAYS_PER_RUN` y `unevaluated_range` de la respuesta (el campo se quita del esquema; ningún cliente lo usa todavía). La lectura de costes sigue empezando 7 días antes del primer día a evaluar. Se añade una prueba de equivalencia: una pulsación sobre toda la historia da los mismos episodios que una pulsación por día. Se actualizan ADR-0020 (decisión 8 y limitaciones), `docs/api/anomaly-episodes.md` y `RF-114-006` (resuelto). Alternativa descartada: mantener el límite (decisión de Lucia del 2026-10-12, porque la alerta de Compute de la demo no saldría en el panel).

**D2. La lista devuelve tres datos del tenant.** `last_evaluated_date` (de `anomaly_detection_state`, null si nunca se detectó), `includes_synthetic_data` (`EXISTS` de una ingesta completada del tenant con `request->'synthetic' = true`, la misma marca que ponen las herramientas de JUP-106 y JUP-107) y `open_impact_by_currency` (suma exacta de `impact_numerator / 7` de los episodios `new` o `investigating` por moneda, redondeada una vez). Se calculan en la misma lectura que la lista, con predicado de tenant, para cualquier `scope`. Alternativa descartada: sumar en el navegador; los importes llegan redondeados y `Number` pierde céntimos con importes grandes.

**D3. Panel: una lectura y filtros en el cliente.** El panel pide `scope=all` una vez por tenant y generación de sesión y filtra en el navegador (criticidad, estado, observación); los recuentos del resumen se cuentan sobre esa lista y el impacto viene de `open_impact_by_currency`. Clave de consulta: `["anomaly-episodes", 1, tenantId, generation]`. Al cambiar de tenant la clave cambia y se muestra el esqueleto, nunca datos del anterior. Las mutaciones (`detect` y `PATCH`) invalidan esa clave. El botón «Detectar ahora» se desactiva mientras su mutación está en curso.

**D4. Importes exactos en pantalla y en la exportación.** Los importes se tratan como cadenas con dos decimales y se formatean con agrupación y símbolo de moneda sin pasar por `Number` (misma convención que `costCents`); la exportación CSV/PDF usa el valor decimal en texto y la moneda en su propia columna.

**D5. Detalle con el diálogo existente.** `components/ui/dialog.tsx` (Radix: foco atrapado, Esc, foco devuelto al botón «Detalle»), a pantalla completa por debajo del ancho `sm`. Acciones: «Marcar en investigación» (solo `new`) y «Cerrar…» (solo `new` o `investigating`), que muestra Resuelta o Falso positivo, el campo de motivo con la misma validación que el backend (al menos un carácter visible, sin caracteres de control) y el aviso «no se puede deshacer» con un botón de confirmación. Los errores 404, 409 y 422 se muestran dentro del diálogo; 409 ofrece recargar el episodio.

**D6. Textos y etiquetas.** Criticidad «Alta (P1)», «Media (P2)», «Baja (P3)» con la leyenda de umbrales; estados «Nueva», «Investigando», «Resuelta», «Falso positivo»; observación «Se sigue observando» o «Ya no se observa desde …»; colores de la guía de marca (JUP-112) y texto siempre presente. Mensajes de «Detectar ahora» y de los estados vacíos según la spec.

**D7. Datos de demo diarios.** `ROWS` de `scripts/synthetic_anomalies.py` pasa a una tabla por servicio y día (134 registros: seis servicios × 21 días más Networking desde el 14), con los totales de los dos periodos de JUP-030 intactos (comprobado en la exploración ejecutando la regla real). `remove` borra, tras las mismas comprobaciones de que el tenant solo tiene filas de la herramienta, `anomaly_episodes` y `anomaly_detection_state` de ese tenant (ADR-0011 permite a un servicio escribir filas de tablas de otro; no hay DDL). `status` informa también del número de episodios. Las pruebas recalculan de forma independiente (sin importar el servicio del backend) las sumas por periodo y la regla diaria con `Decimal`, y las comparan con `esperados-anomalias.json`, que gana la sección de episodios.

**D8. Demo de 3 minutos.** Nuevo paso de Anomalías tras D9 (aislamiento), que ya cambia a `tenant-core`; D7 (etiquetas) pasa a opcional; el paso de límites se acorta de 15 a 5 s y deja de decir que Anomalías usa datos fijos; los identificadores se renumeran donde haga falta y `preguntas.md`, `README.md`, `preparacion.md`, `anomalias.md` y la receta de navegador se actualizan, con sus pruebas (`scripts/tests/test_synthetic_cost_demo.py` y las de la herramienta). La preparación carga los dos conjuntos y no detecta antes de la ruta.

**D9. Purpose de `anomalies-panel`.** Se rellena el `TBD` heredado de JUP-057 editando `openspec/specs/anomalies-panel/spec.md` tras archivar.

## Risks / Trade-offs

- [Primera ejecución con mucha historia] → el MVP tiene semanas o pocos meses por tenant; la lectura es una consulta agrupada por día y servicio; se mide el tiempo con el conjunto de JUP-106 en la validación y se registra si fuera alto.
- [Quitar `unevaluated_range` rompe el contrato del change 1] → sin consumidores todavía; se documenta en la API.
- [El guion cambia de cliente a mitad] → el paso de aislamiento ya lo hacía; la receta de navegador comprueba el aviso sintético y el primer episodio.
- [Los totales semanales del conjunto se rompen al rehacerlo] → prueba independiente que falla nombrando servicio y periodo; la guía de JUP-030 se repite contra el endpoint real.
- [Resaltado de episodios nuevos tras detectar] → solo visual; los nuevos se identifican por los `id` que no estaban en la lista anterior.

## Migration Plan

Sin migraciones de base de datos. Despliegue normal del backend y del frontend; los datos de demo se recargan con `remove` y `apply`.
