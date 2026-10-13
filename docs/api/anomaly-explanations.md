# Explicación de anomalías de coste

JUP-038 — [Trello](https://trello.com/c/QzkjVY7P). Contrato HTTP versión 1 de la explicación de un
episodio de anomalía guardado. Change: `jup-038-explain-anomaly-episodes`. Fuente de los episodios:
[anomaly-episodes.md](anomaly-episodes.md) y [ADR-0020](../adr/ADR-0020-cost-anomaly-episodes.md).

**Estado: implementado y validado con datos sintéticos (2026-10-13).** Backend en
`apps/backend/app/services/anomaly_explanations.py` y la ruta del asistente; frontend en el redactor y el
panel de anomalías. La sección «Ejemplo real» muestra una explicación guardada por un navegador real contra
un stack aislado; el ejemplo de «Cifras» está calculado a mano. Evidencia y límites de la validación en
[JUP-038-validation.md](../evidence/JUP-038-validation.md).

El asistente explica con palabras y cifras exactas por qué se marcó una anomalía guardada, cuánto
lleva y en qué estado está. **La explicación es determinista: la arma código a partir de los datos
guardados del episodio, sin modelo generativo, sin embeddings y sin recuperación documental.** Lo
que el usuario escribe en la pregunta no se interpreta. Presenta la anomalía como candidata a
investigar: no atribuye causa, no estima ahorro y no convierte monedas.

## Petición

`POST /assistant/conversations/{id}/messages`, con Bearer y `X-Tenant-Id`, igual que las demás
preguntas del asistente. El mensaje lleva la selección estructurada de una anomalía:

```json
{
  "content": "¿Por qué se ha marcado esta anomalía?",
  "anomaly_query": {
    "episode_id": "anomaly-<64 caracteres hexadecimales>"
  }
}
```

- `episode_id` es el `id` de un episodio de [anomaly-episodes.md](anomaly-episodes.md) y debe cumplir
  `^anomaly-[0-9a-f]{64}$`. No hay otros campos: un campo adicional, incluidos un cliente o un
  usuario, se rechaza.
- `anomaly_query` y `ownership_query` ([ownership-questions.md](ownership-questions.md)) son
  excluyentes: enviar los dos a la vez es un 422.
- El cliente y el usuario salen de la sesión, nunca del cuerpo. El texto de `content` se guarda como
  pregunta del usuario, pero no filtra ni autoriza nada.
- La explicación se calcula entera antes de escribir. No se abre, continúa ni cambia ningún
  episodio, no se lee ningún registro de coste y la fecha «Revisado hasta» del cliente no se mueve.

## Respuestas

| Código | Cuándo | Cuerpo | ¿Se guardan mensajes? |
| --- | --- | --- | --- |
| 201 | Anomalía del cliente activo, explicable | `AssistantReply` con `retrieved_context` vacío | Sí, el del usuario y el del asistente |
| 401 / 403 | Sesión o pertenencia al cliente no válidas | Como el resto de rutas | No |
| 404 | La conversación no es de este usuario y cliente | `Conversation not found.` | No; no se lee ninguna anomalía |
| 404 | La anomalía no existe **o es de otro cliente** | `{"detail":{"code":"anomaly_episode_not_found"}}` | No |
| 409 | La anomalía no se puede explicar con las reglas que el sistema conoce | `{"detail":{"code":"anomaly_explanation_unavailable"}}` | No |
| 422 | Identificador con otro formato, campos adicionales o los dos tipos de selección a la vez | Detalle de validación | No |

El 404 de una anomalía de otro cliente y el de una inexistente son idénticos, como en
`GET /billing/anomalies/episodes/{id}`: la respuesta no dice si el identificador existe en otro
cliente. El 409 se da con una versión de reglas distinta de `jup019-daily-v1`, con `rules` guardadas
que no son las de esa versión, con valores del día de apertura que no cumplen la regla del
episodio o con datos guardados incoherentes: estado u observación desconocidos, moneda que las reglas
no evalúan, menos de 1 día de impacto, fecha final del impacto anterior a la de inicio, impacto acumulado
menor que el exceso del día de apertura (que el acumulado siempre incluye), cerrado sin fecha o sin motivo
con texto, o no observado sin la fecha desde la que no se observa. También da 409 un operando que no es un
número finito, que es negativo o que excede lo que guarda `NUMERIC(38,12)` (más de 38 dígitos, más de
26 cifras enteras o más de 12 decimales), en lugar de un error del servidor. En esos casos el sistema prefiere no responder a dar una explicación aproximada.

## Qué dice la explicación

Las secciones van siempre en este orden. La redacción exacta la fijan las pruebas del grupo 2 de las
tareas; aquí se define el contenido.

1. **Identificación:** el servicio entrecomillado (o «sin servicio informado») y la moneda.
2. **Por qué se marcó:** día de apertura, coste observado ese día, referencia diaria con la que se
   comparó, subida absoluta y relativa, y que la regla marca un día solo cuando supera las dos
   condiciones a la vez, con los umbrales y la versión de reglas guardados en el episodio.
3. **Impacto y criticidad:** impacto acumulado en la moneda del episodio, días que cuenta y hasta
   qué día, criticidad y el tramo que la determina.
4. **Seguimiento:** estado con las mismas palabras que el panel, si se sigue observando o desde qué
   día ya no, y si está cerrada, la fecha y el motivo. Si el servicio ya tuvo una anomalía anterior,
   su identificador.
5. **Causa no establecida** y las limitaciones del episodio, redactadas en español.
6. **Aviso de datos sintéticos**, solo cuando el cliente tiene alguna ingesta completada marcada
   como sintética.
7. **Alcance:** la explicación cubre el día de apertura y los acumulados. No hay serie diaria
   guardada, así que no cuenta la evolución día a día.
8. **Fotografía:** fecha y hora de la explicación e identificador de la evidencia.

El nombre del servicio y el motivo de cierre son datos del cliente: se muestran entrecomillados en
una sola línea, con los caracteres de control e invisibles escapados, para que no puedan pasar por
frases de la respuesta. No se escriben en los registros del servidor. Estados y criticidades usan las
palabras del panel: «Nueva», «Investigando», «Resuelta», «Falso positivo» y «Alta (P1)», «Media
(P2)», «Baja (P3)».

## Cifras: aritmética exacta

Con `R` = suma de los 7 días de referencia, `O` = coste observado el día de apertura e `I` = impacto
acumulado multiplicado por 7, valores exactos guardados (la API de episodios los devuelve ya
redondeados):

| Cifra | Cálculo | Se muestra |
| --- | --- | --- |
| Referencia diaria | `R / 7` | dos decimales, HALF_UP |
| Subida absoluta del día de apertura | `(O × 7 − R) / 7` | dos decimales, HALF_UP |
| Subida relativa | `(O × 7 − R) × 100 / R` | dos decimales, HALF_UP, con `%` |
| Impacto acumulado | `I / 7` | dos decimales, HALF_UP |

Se redondea una sola vez, al mostrar. No se restan nunca importes ya redondeados. Cuando la cifra
mostrada coincide con el umbral con el que se compara, el texto añade que el valor exacto queda por
encima o por debajo y que la cifra está redondeada, y la evidencia lo anota en `rounding_notes`.
Los umbrales son estrictos, como en [anomaly-episodes.md](anomaly-episodes.md#regla-y-lo-esperado).

### Ejemplo calculado a mano

Serie del contrato de episodios: 400.00 EUR al día del 1 al 7 de septiembre de 2026, 550.00 el día 8
y 650.00 el día 9. Referencia del episodio: `R` = 2800.00 (400.00 al día). Se abre el 2026-09-08 y se
sigue el 2026-09-09; el 10 es el último día con datos y no se evalúa.

| Concepto | Cálculo | Resultado |
| --- | --- | --- |
| Subida absoluta del día 8 | (550.00 × 7 − 2800.00) / 7 = 1050.00 / 7 | 150.00 EUR (> 100.00) |
| Subida relativa del día 8 | 1050.00 × 100 / 2800.00 | 37.50 % (> 20 %) |
| Impacto del día 8 | 150.00 | 150.00 |
| Impacto del día 9 | (650.00 × 7 − 2800.00) / 7 = 1750.00 / 7 | 250.00 |
| Impacto acumulado | `I` = 1050.00 + 1750.00 = 2800.00; 2800.00 / 7 | 400.00 EUR en 2 días hasta el 2026-09-09 |
| Criticidad | 400.00 < 500.00 | P3 |

Es la misma cifra que da el ejemplo ejecutable de [anomaly-episodes.md](anomaly-episodes.md)
(`2026-09-08 2026-09-09 400.00 400.00 2 P3`), calculada aquí con un script independiente del backend
que usa aritmética exacta.

Bordes de redondeo que el explicador debe tratar (cálculo en el mismo script):

| Caso | Valores exactos | Se muestra | Qué debe decir el texto |
| --- | --- | --- | --- |
| Subida absoluta igual al umbral | `R` = 2800.00, `O` = 500.004: subida 100.004, 25.001 % | 100.00 y 25.00 % | Supera el umbral de 100.00 aunque la cifra mostrada coincida; cifra redondeada |
| Subida relativa igual al umbral | `R` = 7000.00, `O` = 1200.002: subida 200.002, 20.0002 % | 200.00 y 20.00 % | Supera el 20 % aunque la cifra mostrada coincida; cifra redondeada |
| Impacto igual al límite del tramo | `I` = 3499.972: impacto 499.996 | 500.00 | Criticidad P3 (por debajo de 500.00); cifra redondeada |

## Evidencia guardada

El mensaje del usuario se guarda con `metadata = {"anomaly_query": {"episode_id": "..."}}` y el del
asistente con `metadata = {"citations": [], "anomaly_evidence": {...}}`. No hay migración: es JSON
dentro de los metadatos del mensaje. Es una evidencia distinta de las citas documentales
(`source_citations`) y de la evidencia de costes por propiedad (`cost_evidence`).

| Campo | Contenido |
| --- | --- |
| `schema_version`, `adapter_version` | `"1.0"` y `"anomaly-explanation-1.0"` |
| `id` | `anomaly-explanation:` seguido de un sha256 (ver más abajo) |
| `status` | `"ok"` |
| `source` | `kind: "anomaly_episodes"`, `rules_version` y `data_as_of` (= `impact_through_date`) |
| `episode` | El episodio tal como lo devuelve la API en ese momento, con las fechas y horas en ISO 8601 (las horas con desfase `+00:00`, donde la API escribe `Z`: es el mismo instante) |
| `operands` | `reference_seven_day_total`, `opening_observed_cost` y `accumulated_impact_times_seven`, como cadenas decimales exactas, sin redondear ni normalizar: conservan la escala de la columna (la base de datos guarda 12 decimales, así que un valor de 2800.00 se escribe `2800.000000000000`; los ejemplos de este documento usan dos decimales por claridad) |
| `opening` | Referencia diaria, observado, subida absoluta y subida relativa (cadenas con dos decimales), umbrales (cadenas tomadas de las `rules` del episodio) y `conditions_met: true` |
| `impact` | Impacto acumulado, días, último día, criticidad y tramo |
| `rounding_notes` | Cifras a las que se aplicó la nota de redondeo (vacío si ninguna) |
| `includes_synthetic_data` | Booleano |
| `cause_status` | `"not_established"` |
| `assumptions`, `limitations` | Lista vacía y limitaciones en español |
| `explained_at` | Fecha y hora UTC de la explicación |

**Identificador.** `id` es el sha256 del JSON canónico (claves ordenadas, sin espacios, UTF-8 sin
escapar) del objeto `{"tenant": <cliente>, ...evidencia}` sin `id` y sin `explained_at`. El cliente
entra en el hash y no se guarda en claro en la evidencia, como en `cost_evidence`. Consecuencias:

- La misma anomalía explicada dos veces sin que haya cambiado da el mismo `id` y distinta
  `explained_at`.
- Cualquier cambio del episodio (más impacto, otro estado, un cierre) da otro `id`, y la explicación
  anterior guardada no cambia: es una fotografía del momento en que se pidió.
- Dos clientes con episodios de los mismos valores tienen `id` distintos.

Con los `operands` y las reglas publicadas aquí se puede recalcular todo a mano, cifras e
identificador, sin acceso al backend.

## Ejemplo real

Salida de la validación del 2026-10-13: stack aislado de Compose con el conjunto **sintético** de JUP-107
(cliente `tenant-core`; son datos de demostración, no facturas de Azure), «Detectar ahora» y el enlace del
panel hacia el asistente. Petición, con el identificador de la anomalía de Compute:

```json
{
  "content": "¿Por qué se ha marcado esta anomalía?",
  "anomaly_query": {
    "episode_id": "anomaly-33b468f4cd0e1bc998899927f3d8b2eef5f220cedb42c23883c3b10acb91a699"
  }
}
```

Respuesta `201` (`AssistantReply`, con `retrieved_context: []`). Los metadatos del mensaje del asistente, con el
episodio y las limitaciones abreviados (`…`):

```json
{
  "citations": [],
  "anomaly_evidence": {
    "schema_version": "1.0",
    "adapter_version": "anomaly-explanation-1.0",
    "id": "anomaly-explanation:1bf475eb797ed5e61a76cba335925f274e6295887f7ea4e2e67c54f2fef5da52",
    "status": "ok",
    "source": { "kind": "anomaly_episodes", "rules_version": "jup019-daily-v1", "data_as_of": "2026-09-20" },
    "episode": { "id": "anomaly-33b468f4…a699", "service": "Compute", "currency": "EUR", "start_date": "2026-09-09", "…": "…" },
    "operands": {
      "reference_seven_day_total": "1000.000000000000",
      "opening_observed_cost": "377.000000000000",
      "accumulated_impact_times_seven": "19654.000000000000"
    },
    "opening": {
      "reference_daily_cost": "142.86", "observed_cost": "377.00",
      "absolute_increase": "234.14", "relative_increase_percent": "163.90",
      "absolute_threshold": "100.00", "relative_threshold_percent": "20", "conditions_met": true
    },
    "impact": { "accumulated_impact": "2807.71", "day_count": 12, "through_date": "2026-09-20", "severity": "P1", "severity_band": "> 2000.00" },
    "rounding_notes": [],
    "includes_synthetic_data": true,
    "cause_status": "not_established",
    "assumptions": [],
    "limitations": ["Es un candidato para investigar, …", "…"],
    "explained_at": "2026-10-13T05:19:25.518738+00:00"
  }
}
```

El texto del mensaje del asistente (`content`), línea a línea, con las cinco limitaciones abreviadas:

```text
Anomalía candidata en el servicio "Compute" (EUR).
Por qué se marcó: el 2026-09-09 el coste observado fue 377.00 EUR frente a una referencia de 142.86 EUR al día (media de los 7 días anteriores a la apertura). Subió 234.14 EUR (163.90 %).
Regla jup019-daily-v1: un día se marca solo si supera la referencia en más de 100.00 EUR y en más de un 20 %, las dos condiciones a la vez. Este día cumple las dos.
Impacto acumulado: 2807.71 EUR en 12 días, hasta el 2026-09-20. Criticidad: Alta (P1), por encima de 2000.00 EUR.
Estado: Nueva. Se sigue observando.
Causa no establecida: es un candidato para investigar, no una causa demostrada ni un ahorro.
Limitaciones:
- Es un candidato para investigar, no una causa demostrada, un ahorro ni una confianza estadística.
- … (otras cuatro limitaciones)
Aviso: los datos de este cliente incluyen datos sintéticos de demostración.
Alcance: esta explicación cubre el día de apertura y los acumulados; no hay detalle día a día.
Fotografía tomada el 2026-10-13T05:19:25.518738+00:00 (UTC).
Evidencia: anomaly-explanation:1bf475eb797ed5e61a76cba335925f274e6295887f7ea4e2e67c54f2fef5da52.
```

Comprobaciones hechas sobre esta misma evidencia, con un script independiente del backend (`BigInt` y
`crypto`): 142.857… → `142.86`, (377 × 7 − 1000) / 7 → `234.14`, 1639 × 100 / 1000 → `163.90 %`, 19654 / 7 →
`2807.71` y el sha256 del JSON canónico coincide con el `id`.

## Correspondencia con el resultado común de herramientas

El contrato de herramientas del agente ([finops-agent-tools.md](../architecture/finops-agent-tools.md#resultado-comun))
define un resultado común. La evidencia usa los mismos nombres para que envolverla no obligue a
rehacerla:

| Resultado común | Esta evidencia |
| --- | --- |
| `status` | `status` |
| `source` | `source` |
| `data` | `episode`, `opening` e `impact` |
| `evidence_ids` | `[id]` |
| `assumptions`, `limitations` | los mismos campos |
| `correlation_id` | No existe todavía: lo añade quien registre la herramienta |

**Este cambio no registra ninguna herramienta del agente ni modifica el modelo.** El explicador es
una función aparte, sin dependencias de la ruta ni de HTTP; cuando JUP-035 se integre, la futura
herramienta `detect_cost_anomaly_candidates` puede llamarla y devolver las mismas cifras y el mismo
`id` que esta ruta. Hasta entonces la explicación solo se ofrece por selección estructurada.

## Entrada desde la interfaz

El redactor del asistente tiene el modo «Explicar una anomalía», excluyente con «Consultar costes
por propiedad». Al activarlo carga las anomalías del cliente activo (`GET /billing/anomalies/episodes?scope=all`)
y solo ofrece las que tienen un identificador con el formato real, `anomaly-` más 64 caracteres
hexadecimales en minúscula; un `episode_id` con otro formato da un 422 genérico, así que el frontend lo
valida antes de enviar. Los errores se traducen por `detail.code`: `anomaly_episode_not_found` y
`anomaly_explanation_unavailable` tienen texto propio; cualquier otro error conserva el mensaje genérico.

El detalle de una anomalía en el panel `/anomalies` ofrece el enlace «Explicar en el asistente», que abre
`/assistant?episode=<id>`, **solo si el identificador tiene ese formato**; el panel solo navega y no hace
peticiones nuevas. El parámetro solo **preselecciona**: el envío ocurre únicamente al pulsar «Enviar» (la
validación en navegador comprobó que no hay ningún `POST` antes) y el parámetro se quita de la dirección tras
un envío correcto. El identificador de la dirección no autoriza nada: el backend filtra siempre por el
cliente de la sesión.

## Límites

- La explicación cubre el día de apertura y los acumulados; la evolución día a día no está guardada.
- Solo se explican episodios con `jup019-daily-v1`, en cualquier estado (también los cerrados); otra
  versión de reglas da 409 hasta que se enseñe al explicador a contarla.
- La criticidad sigue la lectura de los tramos «EUR/mes» como impacto acumulado del episodio, todavía
  sin confirmar con la responsable de las reglas de negocio (ver ADR-0020).
- Una pregunta en texto libre sobre anomalías sigue respondiéndose con el corpus del asistente, que
  no tiene las aclaraciones de ADR-0020: `RF-114-001` está aplazado y abierto.
- Los importes se muestran por moneda, sin conversión, y nunca se suman monedas distintas.
- Los nombres de servicio son datos del cliente: no se publican en registros ni en evidencia
  compartida.
