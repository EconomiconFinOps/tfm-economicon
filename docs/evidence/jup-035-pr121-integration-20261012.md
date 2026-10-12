# JUP-035: incorporacion local de PR #121

## Alcance y autorizaciones

Paris autoriza incorporar la rama de Alejandro, conservar su RAG automatico,
realizar dos ensayos reales focalizados y corregir el saludo sin fuentes sin
alterar su diseno ni los validadores. No autoriza publicacion, merge en develop,
archivo adicional OpenSpec ni cambios en Trello.

- Entrega anterior: f63c15031b65c99f1da149e867675ff771d3c1dd.
- Checkpoint que conserva nuestras correcciones pendientes: a8f4ddd.
- Rama incorporada: fix/JUP-035-auto-documentation.
- Revision del compañero: 75f4f41dc970f32447fde5ce0e10adf24bcea61d.
- [PR original](https://github.com/EconomiconFinOps/tfm-economicon/pull/121).
- [Su evidencia original, preservada](jup-035-auto-documentation-20261012.md).

Los cuatro conflictos se resuelven conservando el protocolo automatico y los
dos arreglos de cierre de SSE del compañero, su fixture SQL portable y nuestras
protecciones de contexto, resiliencia, historial, despliegue y UI. La continuidad
mantiene un tema actual e indice breve, con evidencias historicas enlazadas.
Sus commits se conservan mediante merge, sin reescribir autorias ni su rama.

## Comprobaciones afectadas

En contenedores desechables Python 3.12, checkout montado solo lectura,
sin inferencia para pytest:

| Grupo | Resultado |
| --- | --- |
| Backend auto, metadata, operaciones, resiliencia y admision | 64 passed |
| Backend ensamblado de contexto | 30 passed |
| Summary SQL: tres probes CockroachDB reales y un control CPU | 4 passed |
| Processor auto, gateway, recursos y contrato privado, con correccion final | 112 passed |
| OpenSpec estricto | 67 passed |

Son 210 casos distintos focalizados, no suites completas ni una CI nueva.
Los tres probes SQL primero se omitieron sin URL y despues dieron error usando
por equivocacion el dialecto PostgreSQL; con cockroachdb+psycopg pasan los tres.
Dos invocaciones previas de backend apuntaron a un modulo inexistente y no
ejecutaron pruebas. Se conservaron como intentos fallidos, no resultados verdes.

El test nuevo cubre ausencia de fuentes, evidencia billing y resultado corpus.
Red: 1 failed / 2 passed. Tras corregir la firma del productor controlado de
cancelacion, Green: 112 passed; se conservan sus aserciones de cancelacion.
Mutacion en copia desechable retirando la restriccion: 1 failed / 2 passed.
El producto entregado no se modifico para ejecutar esa mutacion.

Comandos focales desde cada servicio:

```text
python -m pytest -q -p no:cacheprovider tests/test_chat_auto_jup035.py tests/test_chat_metadata_jup035.py tests/test_chat_operations_jup035.py tests/test_chat_resilience_jup035.py tests/test_chat_admission_hardening_jup035.py
python -m pytest -q -p no:cacheprovider tests/test_chat_context_assembly_jup035.py
JUP035_REQUIRE_NATIVE_SQL=true JUP035_COCKROACH_TEST_URL=<base desechable economicon_jup035_mock_* con CockroachDB 24.1.11 y dialecto cockroachdb+psycopg> python -m pytest -q -p no:cacheprovider tests/test_chat_summary_sql_deadline_jup035.py
python -m pytest -q -p no:cacheprovider tests/test_chat_auto_jup035.py tests/test_chat_gateway_jup035.py tests/test_chat_resources_jup035.py tests/test_chat_private_jup035.py
node node_modules/@fission-ai/openspec/bin/openspec.js validate --all --strict --no-interactive
```

## Ensayos reales

Backend y processor temporales usan las fuentes reconciliadas y recursos
verificados, una base CockroachDB nueva y el corpus sintetico pgvector existente
en lectura. No se reinician los servicios anteriores. Resumen desactivado solo
en estos probes; no se comprueba compresion, navegador ni nueva bateria completa.
Las llamadas pasan por endpoints autenticados del chat, canal privado HMAC,
LiteLLM y OpenRouter. Cada caso utiliza una conversacion nueva.

| Caso | Resultado |
| --- | --- |
| Que significa owner y que informacion personal debe excluirse | completed, un intento, 32.859 s; RAG automatico, dos citas de business-rules.economicon-mvp y dos mensajes persistidos/reabiertos |
| Saludo inicial | failed, un intento, 10.313 s; backend diagnostica response_validation/evidence_membership; se conserva el recibo |
| Solo saludo, tras corregir el productor | completed, un intento, 8.250 s; no_data, cero retrieval/citas, dos mensajes persistidos/reabiertos |

Los chunks citados sustentan responsable operativo, preferencia por equipo,
exclusion de PII/informacion sensible y ejemplo web-team. La respuesta distingue
que la fuente son reglas de tagging, no una definicion atribuida al glosario.

La correccion especializa solo la respuesta final sin fuentes a evidence vacia
y estados no accionables, desde evidencia autenticada y resultados ya validados.
No fuerza retrieval, no cambia modelo, no elimina citas despues de generarlas y
no relaja FinOpsResponse 1.0. Con fuentes, el esquema anterior se conserva.
El caso documental no se repite: su rama del esquema permanece intacta y las
regresiones verifican ambas variantes.

## Consumo y limites

Paris autoriza 0.03 USD adicionales para estos probes y dos horas de caducidad.
El gateway limita processor a spend anterior + 0.025 y embeddings a anterior
+ 0.005; no se modifica el tope upstream, permisos, modelos o concurrencia.

- Processor: 0.417465675 -> 0.423759405 USD, delta 0.006293730.
- Embeddings backend: 0.00024008 -> 0.00024034 USD, delta 0.000000260.
- Total observado: 0.006293990 USD, incluido el saludo fallido.

Recibos locales conservados en pr121-integration junto al worktree de entrega:
documentary.json, greeting.json, greeting-corrected.json, budget-before.json y
budget-after.json. No contienen claves. El fallo original no se sobrescribe.
Los recibos privados no son requisito de arranque: el corpus versionado y los
comandos anteriores permiten repetir el alcance con credenciales propias.

## Pendientes reales

La incorporacion no cierra las mejoras pendientes del plan completo, incluida
la adaptacion de pruebas antiguas de JUP-022 al chat nuevo, formato, documentacion
y controles finales. No acredita compresion, alta disponibilidad, todas las
preguntas ni revision/validacion humanas. No se publican commits ni reviews.
