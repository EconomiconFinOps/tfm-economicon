# JUP-038 — Explicación de anomalías

Contribución técnica del 2026-10-10 para [JUP-038](https://trello.com/c/QzkjVY7P).
JUP-030 aún no está integrado en la base `c2995a1`: sin sus módulos la ruta
devuelve **503**. No sustituye el detector con fixtures en ejecución normal.

## Entrada conversacional

`POST /assistant/conversations/{conversation_id}/anomaly-explanations`
requiere `Authorization: Bearer …`, un único `X-Tenant-Id` autorizado y
conversación propia. El cuerpo se construye con una alerta y la definición
devueltas por el evaluador JUP-030:

```javascript
const body = {
  anomaly_id: evaluation.alerts[0].id,
  evidence_id: evaluation.alerts[0].evidence_id,
  definition: evaluation.definition
};
```

No se aceptan costes, tenant ni una explicación aportada por el cliente. La
definición usa start_date/end_date, group_by, currency, absolute_threshold,
deviation_threshold_percent y min_absolute_increase. Los importes son cadenas
con dos decimales. JUP-030 valida los límites de fechas y reglas.

Respuesta 201: `AssistantReply` habitual, sin chunks documentales, con mensaje
en español y `assistant_message.metadata`:

```text
capability: anomaly_explanation
anomaly_explanation:
  contract_version: 1
  content: texto determinista
  evidence: fotografía JUP-030 seleccionada
  limitations: límites en español
  suggested_checks: comprobaciones pendientes
  cause_status: not_established
```

`evidence` conserva versión y fuente del detector, definición, periodos,
calidad de ambas ventanas, estado, completitud no verificada y limitaciones
originales. `evidence.anomaly` conserva ID, evidence_id, grupo, suscripción,
moneda, importes, recuentos, estados y motivos de la alerta seleccionada.
Se excluyen otras alertas y assessments para no guardar datos innecesarios.

## Coordinación JUP-035/036

La capacidad es explícita y determinista: un router de intención puede
seleccionarla con IDs de una evaluación autorizada. No interpretar el texto
libre como SQL ni pedir a un modelo que complete cifras. Reutilizar
`explain_anomaly(raw_evaluation, request)` después del mismo control de
tenant/usuario y de la adquisición de evidencia del servidor. Si falta una
selección, solicitarla; no escoger automáticamente una alerta del usuario.

No se modifican `send_message`, `AssistantService` ni `SourceCitation`:
JUP-035/036 pueden integrar esta capacidad sin hacer pasar evidencia numérica
por citas del corpus. El frontend actual puede recuperar los mensajes por la
ruta de historial; no se añade selector visual en esta contribución.

## Errores y límites

| Estado | Resultado |
| --- | --- |
| 401 / 400 / 403 | Sesión, selector de tenant o membresía inválidos |
| 404 | Conversación ajena/inexistente o alerta no presente en evaluación actual |
| 409 | Evidencia cambió o fuentes de coste ambiguas; refrescar evaluación |
| 422 | Cuerpo o definición inválidos |
| 502 | Evidencia incompatible o numéricamente inconsistente |
| 503 | Dependencia JUP-030 ausente o fallo al consultar/evaluar |

Las reglas no demuestran la causa ni un ahorro. Available/evaluated no
certifican cobertura; se explicitan falta de frescura/cobertura verificadas,
lecturas separadas, redondeo a céntimos y ausencia de conversión monetaria.
Base ausente/no positiva no es crecimiento cero ni infinito.

Se reevalúan costes actuales; no existe recuperación histórica del detector.
El evidence_id evita explicar una fotografía distinta silenciosamente. El
historial conserva la fotografía utilizada, pero no acredita datos inmutables
del origen. Las dos inserciones de mensajes siguen el comportamiento del chat
existente; un fallo intermedio de escritura no se declara atómico.
