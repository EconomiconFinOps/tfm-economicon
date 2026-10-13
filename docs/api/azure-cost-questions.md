# JUP-036 — Consultas de gasto Azure desde el chat

Trello: https://trello.com/c/LxaVVLcH

En `/assistant`, activa **Consultar gasto Azure**, selecciona suscripción, cuenta
 de facturación o servicio y, opcionalmente, un valor exacto y una suscripción.
Introduce ambas fechas o deja ambas vacías para el mes UTC actual. La fecha final
es exclusiva. Ejemplo del dataset: `2024-06-01` a `2024-07-01`; consultar el mes
actual sobre datos históricos puede devolver ausencia de datos.

El texto de la pregunta acompaña la selección; el ámbito y las fechas se toman
del formulario. No se interpreta lenguaje natural libre. Cuenta significa
`billing_account_id`, no resource group, equipo ni tenant. No se inventan IDs,
conversiones de divisas ni mappings de aplicación (JUP-037 queda separado).

## Contrato HTTP

`POST /assistant/conversations/{conversation_id}/messages`, con bearer válido y
`X-Tenant-Id` autorizado:

```json
{
  "content": "¿Cuánto hemos gastado en Compute?",
  "cost_query": {
    "group_by": "service",
    "value": "Compute",
    "subscription_id": "sub-a",
    "start_date": "2024-06-01",
    "end_date": "2024-07-01"
  }
}
```

`group_by` es obligatorio; los otros campos de `cost_query` son opcionales.
Fechas incompletas/invertidas, campos extra, dimensión desconocida y valores
vacíos/controlados se rechazan con 422 antes de consultar gasto o persistir.
Conversaciones ajenas devuelven 404 y tenants sin membresía 403. Una selección
válida sin filas visibles devuelve 201 con evidencia `no_data`, sin distinguir
valores ajenos de inexistentes. `cost_query` y `ownership_query` son mutuamente excluyentes: enviarlos juntos devuelve 422 sin efectos. Sin ambas selecciones sigue la ruta documental.

Solo se incluyen filas de ingestas completadas, con tenant y suscripción
consistentes en ambos lados del join. Se liga cada filtro como parámetro SQL.
Los importes se agregan antes de redondear a dos decimales con ROUND_HALF_UP;
cero y créditos se conservan. Las monedas permanecen separadas.
Si fuentes completadas solapan la misma suscripción/día, se responde 409
`ambiguous_cost_source` sin importes ni nuevos mensajes; un filtro de servicio
no oculta el conflicto. Un filtro explícito de suscripción delimita el conflicto.

## Evidencia y límites

`assistant_message.metadata.cost_evidence` guarda versión de schema `1.0`, adaptador `azure-cost-1.0`, ID SHA-256,
`queried_at`, selección resuelta, snapshot billing y procedencia (`ingestion_ids`,
primer/último día observado y `observed_day_count`). Persiste al recargar el chat.
El hash incluye tenant, selección, snapshot y procedencia; no incluye la hora
de consulta. Identifica ese resultado: no es firma criptográfica de las filas.
La respuesta visible muestra periodo, ámbito, importes, registros, ingestas y
advertencias. Sin valor exacto muestra hasta 20 grupos, con el resto conservado
en el snapshot y en el desplegable de evidencia de costes. La procedencia del adaptador Azure corresponde a la selección consultada; la de ownership conserva su alcance de todo el periodo del cliente. No hay ejecución LLM, embeddings ni retrieval en esta ruta.

`no_data` significa ausencia de filas, nunca gasto cero. `partial` refleja registros
sin dimensión o sin fecha; presencia de filas tampoco demuestra cobertura
completa del periodo. Los registros sin fecha se cuentan en el ámbito autorizado
de suscripción (no pueden asignarse al periodo); la advertencia es conservadora.
El servicio consulta el dataset simulado, sin acceder a Azure real y sin determinar
amortización, ahorro o utilización. Persistencia de los dos mensajes usa el flujo
existente: no se añade transacción atómica de la pareja ni idempotencia del envío.

## Verificación reproducible

- Backend: `cd apps/backend; python -m pytest tests -q`.
- SQL real aislado: configurar `JUP086_COCKROACH_TEST_URL` en loopback y puerto
  dedicado, `defaultdb`, usuario root sin password, `sslmode=disable`. La fixture
  exige CockroachDB con organization `processor-integration-tests`, sin tablas
  de usuario, y crea/elimina una base propia. Nunca usar una instancia compartida.
- Frontend: `corepack pnpm --filter @finops/frontend test -- tests/conversations.test.tsx`.
- `corepack pnpm --filter @finops/frontend typecheck`, `lint` y `corepack pnpm build`.
- `corepack pnpm openspec:validate` y `corepack pnpm jup:check:all`.

Las pruebas propias no sustituyen la revisión Lucia, validación Paris ni
participación real de Victor/Alejandro. No cerrar la tarjeta antes de ellas.

## Integración con la base actual y JUP-035

JUP-036 reutiliza `MessageComposer` y `CostEvidence` de la base actual. Conserva
las consultas de propiedad JUP-037, las citas documentales y la interfaz en español.
Cada conversación y cliente tiene su propio formulario, de modo que un envío
pendiente no borra el borrador de otra conversación.

La generación y la interpretación libre pertenecen al chat JUP-035, cuya PR121
sigue abierta en la consulta del 13/10/2026. Esta entrega proporciona la consulta
explícita y su evidencia; no declara terminado el recorrido generativo. Su consumo
por JUP-035 requiere contrastar el contrato y validar la combinación de ambas PR.
`fetch_billing_summary` conserva sus argumentos existentes y añade filtros opcionales;
las llamadas sin filtros mantienen el comportamiento previo.
