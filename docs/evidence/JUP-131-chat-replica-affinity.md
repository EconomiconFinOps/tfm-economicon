# JUP-131: afinidad entre réplicas privadas

Trello: https://trello.com/c/NtiH8R4Z
Base: `da43f40810d81e7e0e90f10cca1825a3c48e6bd5`.
Verificación local:25/10/2026, Europe/Paris.

El ensayo3 alcanzó siete etapas de aceptación y falló generación. Con dos
processors, resolver DNS independientemente para descriptor y POST puede
entregar el claim a otro boot. Se reprodujo con dos aplicaciones ASGI reales:
descriptorA/POSTB404 y cero llamadas al gateway; A/A funciona y su repetición
da409 sin segunda inferencia. No se afirma haber capturado ese404 en AWS.

La corrección conserva la IP del socket del descriptor firmado y el puerto
configurado, vinculados por boot. Chat, herramientas, cancelación y resúmenes
utilizan esa identidad. Un backend frío sólo busca el boot con GETs firmados
de los candidatos DNS configurados. Nunca reenvía un POST de inferencia a otra
réplica. La caché tiene TTL300s y límite256; resolución/cancelación respetan el
deadline, incluso si el hilo DNS tarda más en regresar.

## Evidencia del implementador

Cuatro regresiones iniciales HTTP fallaron antes del arreglo y pasaron después.
La suite final ejecutada fue:

```text
PYTHONPATH=apps/backend python -m pytest
  apps/backend/tests/test_chat_replica_affinity_jup131.py
  apps/backend/tests/test_chat_transport_jup035.py
  apps/backend/tests/test_chat_summary_transport_jup035.py
  apps/backend/tests/test_chat_cancel_jup035.py
  apps/backend/tests/test_chat_operations_jup035.py
  apps/backend/tests/test_chat_summary_scheduler_jup035.py -q
```

Resultado: **89 PASS** en72.15s con Python3.14 y tokenizers0.22.1; sólo avisos
de deprecación. El venv local se usó porque el intérprete global tenía0.23.1,
incompatible con las fixtures fijadas; no se modificaron las dependencias.
Ocho casos nuevos cubren rotación DNS, controles en backend frío, concurrencia,
reinicio, firma inválida/boot desconocido, deadline y cancelación sin I/O tardío.

El agente independiente revisó el código y verificó6 casos HTTP y5 adicionales.
Detectó en el primer diff una espera DNS sin límite y sondas tras cancelación;
ambos hallazgos están corregidos y su reproducción ahora pasa. Informe local
con hashes: `.work/master-rehearsal/chat-replica-review.json`.
No es una revisión humana ni sustituye la política de integración.

## Límites

La búsqueda secuencial puede consumir los2s de control en un candidato
inaccesible; devuelve resultado incierto sin repetir la inferencia. El SO puede
mantener un hilo DNS bloqueado, pero el llamante termina y no inicia sondas
cuando ese DNS regresa tarde. No hay nueva aceptación AWS, llamada a modelos
ni modificación de recursos en esta validación. ApiError y starlette1.9.0
permanecen intactos. CI del candidato e integración se registran en la PR.
