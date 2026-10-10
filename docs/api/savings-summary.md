# Resumen ejecutivo de ahorro — JUP-039

Tarjeta: https://trello.com/c/ojFr6fCU. Contrato consumidor `savings-input.v1` y
salida `savings-summary.v1`. Verificado el 2026-10-10 contra base
`c2995a118d419dfe725247bac9c6f219a3f0ea77`.

## Uso

En una conversación propia del asistente, escribir:

```text
/ahorro 2026-09-01 2026-10-01
```

Equivalente HTTP, con bearer válido y `X-Tenant-Id` de una membresía:

```http
POST /assistant/conversations/{conversation_id}/messages
Content-Type: application/json

{
  "content": "Resume las oportunidades de ahorro para stakeholders",
  "savings_query": {
    "start_date": "2026-09-01",
    "end_date": "2026-10-01",
    "top_n": 5
  }
}
```

Fechas UTC, inicio incluido y fin excluido. `top_n` limita 1–20 oportunidades
por moneda. La API admite `subscription_id` sólo cuando el proveedor puede
probar ese alcance; el adaptador actual de JUP-033 no admite ese filtro porque
su contrato está agregado por proyecto. No mezclar comando y savings_query.
No se interpretan otras frases o fechas libres como filtros financieros.

201 devuelve AssistantReply existente; texto compartible y
`assistant_message.metadata.savings_evidence`. 401/403/404 conservan las reglas
de sesión, membresía y propiedad; 422 rechaza selección inválida. 503 indica
proveedor ausente o fallo y 502 evidencia inválida. Ambos errores se producen
antes de escribir mensajes. Una consulta documental ordinaria no cambia.

**La instalación por defecto devuelve 503:** JUP-033/034 todavía no forman
parte de la base integrada. Esta entrega no acredita funcionamiento financiero
en producción ni ahorro real. Las pruebas usan dobles explícitos.

## Proveedor interno y contratos dependientes

El proceso servidor instala `app.state.savings_provider`, que implementa
`load_snapshot(tenant_id, selection)`. Ningún endpoint permite instalarlo o
subir sus filas desde el cliente. El adaptador
`RecommendationSavingsProvider` recibe loaders del servidor para JUP-033 y,
opcionalmente, JUP-034. Los loaders deben aplicar autorización y selección,
devolver datos completos y propagar errores; nunca ocultarlos como conjunto vacío.

Contratos examinados el 10/10 en las ramas de implementación, no integradas:

| Productor | Campos consumidos | Límite conservado |
| --- | --- | --- |
| JUP-033, RecommendationReport v1 | period, recommendations, evidence, assumptions, limitations, data_status, truncated | Candidatos agregados por proyecto. estimated_savings es null; observed_cost no es ahorro. El wrapper servidor es responsable del tenant. |
| JUP-034, ImpactReport 1.0 | tenant_id, baseline_month, basis, recommendations/scenario, potential_monthly_savings, potential_annual_savings, totals, assumptions, limitations | basis=caller_supplied_scenario; valores hipotéticos. Referencias no equivalen a evidencia financiera verificada. |

El adaptador enlaza sólo IDs conocidos y período/moneda compatibles. Sin impacto,
mantiene null; no inventa baseline, target ni scopes atómicos a partir de proyectos.
Preserva ambos reportes completos en `upstream_reports`. No suma importes
individuales redondeados del informe034: sus totales originales se conservan
en evidencia, pero no se presentan como total ejecutivo independiente.

El consumidor normalizado requiere tenant, período, fecha con zona, cobertura,
IDs únicos, fuentes, supuestos, riesgo/confianza y valores mensuales/anuales
emparejados. El importe usa string decimal no negativo con dos decimales y
hasta 26 dígitos enteros. No hay conversión monetaria. `independent_cost_basis`
es certificación del proveedor de que los beneficios de bases distintas son
aditivos; su ausencia o repetición suprime el total. Con datos incompletos el
subtotal se etiqueta parcial, incluyendo conteos sin cuantificar.

## Evidencia y límites

Se conserva el snapshot completo aunque sólo se muestren los primeros N:
fuentes, supuestos, limitaciones, estados excluidos, selección y SHA-256 de JSON
canónico. El hash identifica el contenido, no lo autentica. Citas financieras
no se hacen pasar por `source_citations` del corpus. Estados implemented,
dismissed y expired no se contabilizan como potencial ni prueban ahorro realizado.

No hay LLM, embeddings, ejecución de recomendaciones ni modificación de costes.
El texto incluye aviso de estimación, supuestos, fuentes y riesgo. Requiere
validación del responsable antes de tomar una acción de optimización.

Pendiente: publicar/estabilizar contratos033/034, conectar loaders autoritativos,
probar las dependencias juntas con datos de origen y completar pairing/reviews.
Pruebas y limitaciones: [evidencia JUP-039](../evidence/JUP-039-validation.md).
