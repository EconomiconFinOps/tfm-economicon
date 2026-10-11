# JUP-035 — Prompts, pantalla preparada y prefijo de resumen

**APROBACIÓN HUMANA DEL DELTA JSONB — Paris vía Project Manager 10/10/2026 09:15:41 (Atlantic/Canary): «si hazlo».** Aprobado `jsonb-history-design.md` entregado03:20:56: esquema por conversación, final conjunto pregunta/respuesta, alternativas sin duplicar pregunta, migración003/backfill conservador y tabla histórica sin rutas activas. Autoriza adaptación Red→Green→mutación y pruebas afectadas; ventana SIN escritores y migración únicamente LOCAL AISLADA. Sustituye el estado pendiente de ejecución de esta misma propuesta; no acredita implementación ni aceptación. Conservar IDs/citas/metadata/precisión, operaciones separadas y fuente JSONB única; retirada activa exigida a Revisor, Validador y cierre PM. Presupuesto compartido0,20EUR desde02:54:46 permanece, readiness/cota/reserva antes de gasto. No producción/remoto/Git/publicación/archivo/destrucción. Versión aprobada exacta y hashes conservados externamente por TL.


**CAMBIO VIGENTE DE HISTORIAL — Paris vía PM 10/10/2026 03:01:32, con control independiente añadido03:03:01 (Atlantic/Canary).** Historial canónico: un JSONB por conversación; pregunta y respuesta completa se añaden juntas al finalizar, sin cambios al enviar ni por deltas. [Contrato concreto y migración propuesta](jsonb-history-design.md). Sustituye el mecanismo de filas `messages`, su desempate temporal y la ausencia de backfill del diseño anterior; originales/decisiones históricas conservados. Preferencia JSONB aprobada; esquema003/backfill y reescritura material pendientes de validación/despacho, SIN implementación de este delta. Los demás contratos funcionales permanecen. Nueva autorización PM02:54:46 permite pruebas reales necesarias por ruta aprobada hasta0,20EUR acumulados compartidos, con coste acotado/contador antes de llamar; sustituye únicamente la prohibición de gasto anterior. No amplía Git/publicación/remoto/archivo.


**APROBACIÓN HUMANA PRE-CODE — Paris, vía Project Manager09/10/2026 23:23:27 (Atlantic/Canary): «pues aprobado».** Aprobado el diseño consolidado entregado23:17:59 y sus contratos/spec/tareas, incluidas esperas acumuladas, persistencia, seguridad, compresión LLM, concurrencia y UI. Autoriza desarrollo local y dependencias/migración definidas SOLO en entorno aislado de pruebas. Las menciones anteriores de propuestas/pre-code pendiente quedan como antecedentes fechados sustituidos por esta aprobación; no convierten hechos externos no confirmados en integrados ni resultados NOT_RUN en PASS. Sigue propuesta configurable/no medida la capacidad8, ahora autorizada para implementación/prueba en ese alcance. No autoriza nuevas inferencias con coste, publicación, gestión Git, archivo o merge; conservar guards y Red→Green→mutación separados. Versión exacta aprobada y SHA256 conservados fuera del repositorio por TL.


**DECISION_REQUIRED; solo diseño.** Paris vía PM 09/10/2026 21:33:08/TL 21:34:12 corrige preparación de pantalla y resumen/cache. Aprobación PM 21:46:22/TL 21:47:33 de operación durable/pareja final,120×4/480 y resumen LLM EN DISEÑO; detalles y pre-code pendientes. Base `ceb6520fd9b92c561c455cd8cbcd40aecf2c9f46`, rama `feat/JUP-035-conversational-web-interface`, CONTRIBUTING 2026-09-30/JUP-100. Paris líder, Víctor pairing, Alejandro revisión, Lucía validación. [Historial](history-persistence-design.md), [resumen LLM](context-compression-extension.md), [integración](integration-readiness-plan.md), [matriz](design-decision-matrix.md).

## Aprobaciones funcionales conservadas

Paris ya aprobó cargar los prompts exclusivamente en servidor, reutilizar las reglas de JUP-024, separar instrucciones y datos variables, versionar por respuesta y capturar datos cargados/filtros/periodo/moneda/totales/desglose/fecha/completitud de la pantalla activa, ligados a usuario y tenant. Estas decisiones funcionales no se vuelven a consultar. El contrato técnico siguiente debe formar parte del diseño consolidado que verá Paris antes del desarrollo.

Fuente PM 19:42:02/TL 19:42:47. Límites **1 MiB UTF-8 por captura completa y 8192 tokens variables aprobados PM 21:15:55**. HTTP interno privado autenticado en un DockerServer y HTTPS externo aprobados PM 21:17:13. La corrección PM 21:33:08 determina cuándo preparar pantalla: al recibir/cambiar datos; Send solo copia/congela versión existente. No nueva decisión sobre esos requisitos.

## Recursos, roles y versión

Processor `apps/processor/app/agents/prompts.py` contiene las diez reglas JUP-024; AgentRuntime las usa, pero LiteLLMProvider.invoke actual acaba aplanando system+human en un único user. **El chat nuevo conserva roles reales**, no copia ese comportamiento. Backend AssistantService actual es plantilla retrieval, no generador.

Proponer recursos chat `apps/processor/app/agents/prompt_resources/jup035/chat/v2/`: system.md, input.md y manifest.json. v2 distingue la revisión con diálogo/prepared screen/attempts; no sustituir bytes de una versión anterior desplegada. Manifest incluye hashes UTF-8 de recursos/SYSTEM_PROMPT heredado, schema canónico FinOpsResponse 1.0, input-contract, assembler y tokenizer. `prompt_version=jup-035.chat.v2:<manifest-digest>`; Git build SHA opcional, nunca Git por petición. No importar paquete app del processor en backend: contrato de respuesta derivado del schema autoritativo y verificación de hash, no segunda copia editable divergente.

Loader de lista cerrada valida una vez hashes/schema y prepara objeto inmutable. Falta/diferencia de recurso impide habilitar chat; no prompt vacío, URL/filename del cliente, edición HTTP o descarga en runtime. Descriptor interno autenticado aporta versiones/hash, nunca texto system. Backend congela versión antes de reservar; processor exige exactamente esa versión y retorna la misma. FinOpsResponse/model/provider configurados se distinguen de observados; un alias no certifica modelo upstream.

### Orden exacto del prefijo

```text
system: reglas JUP-024 + system.md + contrato estable/guardrails
user:   UNTRUSTED_DIALOGUE_SUMMARY {resumen y referencias estables}, si válido
user:   UNTRUSTED_CURRENT_CONTEXT {recent_turns, current_question,
          screen_projection, omissions, verification, authorized_evidence}
response_format: FinOpsResponse canónico
```

El system no contiene fecha, request/attempt IDs, tenant/user, pantalla ni pregunta. El resumen es datos user **no confiables**, separado de pantalla, nunca system/instrucciones/autoridad financiera. Mismos bytes de resumen+schema/version dejan prefijo candidato estable; cambia al instalar otra revisión/policy/prompt. El bloque final contiene variables. IDs operacionales, timestamps de transporte y capabilities viajan fuera de messages del modelo salvo referencia funcional imprescindible, nunca delante del resumen.

Reserializar de forma canónica y escapar controles/`<`/`>` en strings; no interpolar browser/corpus en templates de instrucciones. Delimitadores no eliminan prompt injection. Reenviar contexto necesario en cada intento: proveedor no recibe «subir contexto una vez» ni memoria remota garantizada. Misma operación/retries automáticos usan contexto congelado; retry humano toma otra versión ya preparada y fuentes server nuevas.

## Pantalla preparada al recibir o cambiar datos

Registro por pestaña/ruta protegido por `(session_generation,tenant,user,route,selection_version)`. El adaptador de cada página recibe **el mismo resultado que renderiza** y prepara inmediatamente un descriptor JSON cerrado, bytes/hash/tamaño/version y copia inmutable cuando llegan datos, cambian filtros/periodo/moneda/completitud o estado de carga. Limpiar descriptor anterior al cambiar identidad/ruta/selección; publicar loading para nueva selección, no reutilizar viejo payload como actual. Refetch de la página actualiza preparación cuando llega su resultado; chat no lo inicia.

**Send no construye el descriptor, no lee DOM, no recorre cachés, no consulta API ni ejecuta diagnóstico.** Solo selecciona versión vigente y copia/congela el objeto/bytes preparados en la nueva intención y request_id. Si no hay descriptor válido para la ruta/identidad, deshabilitar envío hasta publicar descriptor loading/no-adapter explícito de esa ruta; no enviar la captura de otra ruta. Sincronicidad del registro permite comprobar selección y evitar un render obsoleto. Un cambio posterior no muta una solicitud enviada. Reenvío incierto usa bytes originales; retry humano copia versión preparada entonces.

Contrato cerrado propuesto: schema_version, screen_version, route/tab_id/source, identity tenant/user, captured_at, selection/filtros/periodo/moneda, datasets con source/load_state/loaded_at/selección efectiva/data_environment/completeness/totales/grupos/series/counts/missing_dimensions. Objetos por pantalla con strings funcionales acotados; no sesiones/perfil/email/bearer/URLs internas/headers/trazas/bruto ingestión/prompts/historial. Identidad cliente es declaración comprobada contra sesión server, no credencial.

| Vista inspeccionada | Qué se prepara usando datos cargados |
| --- | --- |
| Ejecutivo `/` | useExecutiveCostKpis: agregado y meses, fechas/group_by/tag/moneda; conservar meses con error/partial y selección efectiva por dataset. |
| `/overview-legacy` | Billing v2 y estados de servicio mostrados de useDashboardData; nunca diagnóstico bruto/lista de otros tenants. |
| `/operational`, `/cuts`, `/anomalies`, `/recommendations` | Fixtures funcionales marcados demo, filtros/periodo; no hechos Azure confirmados ni alcance AWS/GCP inferido. |
| `/ingest`, `/assistant`, `/system-health` | Estado funcional saneado mediante allowlist; no texto bruto, historial completo, secretos ni nueva llamada «Salud del sistema». |
| loading/error/no-adapter | Descriptor de ruta actual con estado y datos disponibles explícitos; vacío/null cuando no llegaron; no selección vieja como actual. |

Datos stale de misma selección pueden marcarse refresh_pending con su selección/loaded_at reales, nunca mezclarse con otro filtro/identidad. Decimales de costes como strings exactos; currencies separadas, selected_currency no convierte/elimina datos cargados. Inicio inclusivo/fin exclusivo UTC y fechas mensuales explícitas. Timestamp/source/completeness browser son declaraciones, no certificados.

Captura completa válida≤1 MiB UTF-8 se conserva; exceso 413 antes de reserva con explicación, sin truncar ni enviar sin ella. Preparación del frontend ya mide el límite; server vuelve a medir bytes antes de parsear y validar. Cuerpo público≤2 MiB, pregunta≤16 KiB y profundidad JSON 32 propuestos. Los límites de frames SSE no limitan captura persistida: recursos GET separados.

## Autorización, contraste y evidencia

Autenticar tenant miembro+owner de conversación antes de buffers/consultas; mismatch de identidad captura bloquea sin consultar tenant declarado. Canonicalizar fechas/tag/cantidades con reglas billing backend, no aproximación JS. Input hash de intención contiene captura completa y pregunta/modo/referencia; conservar orden significativo de datasets/series. Resolver duplicados antes de descriptor/fuentes cambiantes.

Billing-summary-v2 se contrasta mediante `database.fetch_billing_summary` del **tenant autenticado**, selección normalizada; no HTTP a URL browser. Ejecutivo verifica cada selección de agregado/mes, deduplicando consultas iguales; no prometer snapshot transaccional global entre consultas. Comparar currencies/totales/grupos/counts/completitud y periodos; filtros resource/demo no implementados no se transforman en SQL/permisos. Guardar snapshot browser, evidencia server y diferencia por separado.

| Contraste | Consecuencia |
| --- | --- |
| Igual | matched_at_verification con fecha server; acredita consulta, no timestamp browser. |
| Distinto | different_at_verification; cifras autoritativas server y explicación de discrepancia, sin atribuir automáticamente manipulación. |
| Parcial/vacío | Mantener meses/dimensiones ausentes, cero/créditos; no extrapolar ni sumar monedas. |
| No disponible/ambiguo | Estado saneado, insuficiencia de evidencia; captura explica declaración de pantalla pero no sustenta métricas. No retry LLM por dato ausente. |
| Demo/sin contrato | unverified_screen_data explícito; no cerrar dependencias 036/037 con fixtures. |

FinOpsResponse 1.0 mantiene cost_query/corpus/user_input. Pantalla sin verificar es user_input `screen:<snapshot_id>:<dataset-key>`, visible «Contexto de pantalla, no verificado»; evidencia de costes server distinta es cost_query. SourceCitation/AnswerEvidence existentes aceptan corpus: mantener `validate_context/resolve_citations`, no fabricar document_id/page para pantalla. Proponer screen_citations separadas saneadas y enlaces internos scoped, nunca URL arbitraria modelo/browser. Cost_evidence sujeto a contrato 036.

JSON válido/evidence_id dentro del JSON no autentica procedencia. Validar refs contra registro server autorizado y cantidades/currency/periodo/cálculo determinista. User_input/resumen solos no sustentan ahorros/métricas; insufficient_data y colecciones no accionables vacías. Reglas 024 de aprobación humana/acciones permanecen. Prosa y datos pueden contener inyección: negativos de secreto/rol/cita ajena/cifra inventada necesarios; no prometer veracidad general con schema. Deltas provisionales; completed solo después de validación+pareja commit.

## Contador y presupuesto compartido concretos

Datos variables **≤8192 tokens TOTAL**: resumen+recientes+pregunta+proyección pantalla+verificación/evidencia+envolturas. No 8192 por bloque. Prioridad propuesta: pregunta/selección/estado/totales/evidencia mínima server; luego pares recientes/resumen y grupos/series pertinentes con omisiones explícitas. Reservar objetivo resumen 768 y cuatro pares solo si hay espacio. Si esenciales no caben, error/insuficiencia antes de inferencia; no ocultar pérdida ni recortar captura completa almacenada.

Examen cerrado en diseño: LiteLLM puede usar fallback tiktoken para modelo no reconocido, por lo que `token_counter(model=alias)` no acredita contador GLM-5.2. Proponer `tokenizers==0.22.1` y artefacto **ZAI GLM-5.2 revision a66456a59f21345d1e5e586345c448a9106d29d7** offline en backend+processor. Tokenizer.json 20,217,442 bytes SHA256 `19e773648cb4e65de8660ea6365e10acca112d42a854923df93db4a6f333a82d`. Public tokenizer_config TokenizersBackend/model_max_length 1048576. No pesos/modelo, torch, Transformers, código remoto o descarga runtime.

Contar con Tokenizer.from_file bytes/texto serializado real de bloques variables y separadores, sin truncation; manifest registra versión/hash/recuento. Backend y processor vuelven a medir antes de enviar. Contar además system/schema/roles y reservar **1024 tokens de margen de envoltura más 800 output**, subordinado a context_length 1048576 declarado por endpoint DeepInfra fp4. La disponibilidad publicada/correspondencia tokenizer son evidencias técnicas, no prueba de facturación exacta ni del wrapping interno OpenRouter. Fallo/mismatch de assets/contador cierra admisión; no sustituir por bytes o tiktoken y afirmar mismo límite.

**APROBADO PM 21:54:52/TL 21:55:24:** Paris «aprobado» a tokenizers HuggingFace 0.22.1 y tokenizer público ZAI de revisión fija/hash descritos, ≈20 MB sin pesos, en diseño 035/futura implementación aprobada. No reconsultar la misma elección; no instalar/descargar/ejecutar ahora. PyPI 0.22.1 requiere Python≥3.9 y huggingface-hub≥0.16.4,<2.0; wheel `cp39-abi3 manylinux2014_x86_64` compatible declarado con Python 3.12, SHA256 `e2ef6063d7a84994129732b47e7915e8710f27f99f3a3260b8a38fc7ccd083f4`. Fijar conjunto transitivo y hashes en build autorizado. Inspección de metadatos no equivale a instalación/ejecución ni conteo idéntico a facturación. Compatibilidad declarada cerrada; pruebas futuras de carga/conteo contractual y lock son implementación, no investigación aplazada. Esta aprobación no alcanza key/budget separado del resumen ni pre-code completo.

## Persistencia y caché observada

chat_operations guarda captura completa preparada, versiones/hash y bloques autorizados congelados; cada intento copia manifest/resumen realmente usados, token counts y omisiones. Final assistant guarda manifest completado y metadata canónica; control privado separado. GETcontext/evidence/result propios repiten autorización scope. Dialogue_summary guarda artefacto y revisión/CAS; resumen nuevo no altera intentos anteriores.

Cadena seleccionada alias economicon-chat→openrouter/z-ai/glm-5.2→deepinfra/fp4 exclusiva; require_parameters=true, fallbackfalse, reasoningfalse, pin LiteLLM 1.103.2. Metadata endpoint supports_implicit_caching=false no prueba imposibilidad ni garantiza soporte de cache_control. **No añadir headers/cache_control/session IDs ni cambiar proveedor para obtener hit.**

Ensayo inicial autorizado PM 19:47:29: dos intentos, HTTP 200 cached 0 y HTTP 429 sin usage; INCONCLUSIVE, causa 429 indeterminada. Autorización followup PM 20:09:10 y cierre PM 20:20:45: una llamada adicional autorizada, hit reportado **3840/4053 cached_tokens**, completion 2, gasto gateway observado **0.0005266125 USD**. Tres intentos acumulados de cache; no repetir. Evidencia externa jup 035-prompt-cache-spike-20261009 y jup 035-prompt-cache-followup-20261009, no vertical UI/backend/processor producto. Alias reportado no certifica modelo real; ausencia usage/cache=unknown, cero explícito=no hit en esa respuesta, positivo=hit reportado de esa respuesta. No extrapolar descuento/capacidad ni omitir contexto. Cache miss no invalida chat ni dispara retry/calentamiento.

## Escenarios y decisiones restantes

NOT_RUN: cambio datos→descriptor listo antes de Send; Send cero fetch/construcción/diagnóstico; captura de cambio filtro/ruta/loading no stale; reenvío usa bytes idénticos y retry humano nueva versión; resumen user estable antes de variables; tokenizer assets+8192 compartido con Unicode/límite; captura 1 MiB conserva completos GET sin overflow SSE; inyección/monedas/fecha/citas/prosa no sustentada; same-tenant otro usuario/tenant ajeno en captura/result/context/resumen; manifest por cuatro intentos.

Aprobaciones funcionales anteriores, PM 21:46:22 y elección tokenizer PM 21:54:52 siguen; pendientes reparto/cobertura y detalle credenciales/capacidad, acuerdos 036/037 y pre-code completo. Lock/instalación/prueba focal del tokenizer son futuros bajo esas fases, sin nueva elección genérica. No repetir spikes ni usar checks documentales como aceptación.

Fuentes públicas primarias consultadas 09/10/2026: [LiteLLM conteo/fallback](https://docs.litellm.ai/docs/completion/token_usage), [ZAI tokenizer/modelo](https://huggingface.co/zai-org/GLM-5.2), [HF revision](https://huggingface.co/api/models/zai-org/GLM-5.2/revision/a66456a59f21345d1e5e586345c448a9106d29d7?blobs=true), [PyPI tokenizers 0.22.1](https://pypi.org/pypi/tokenizers/0.22.1/json), [OpenRouter endpoint](https://openrouter.ai/api/v1/models/z-ai/glm-5.2/endpoints). Lectura pública sin inferencias/instalación.
