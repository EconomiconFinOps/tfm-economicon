# Proveedor y modelos — JUP-078

Verificado: 2026-10-10. Chat: `01a12747-8575-7eb3-a21b-ab23813dc2eb`.
Encargo: «JUP-078 — Proveedor y modelos», implementacion completa con
interacciones del equipo sustituidas por subagentes autorizados.

## Alcance y decisiones

[Trello](https://trello.com/c/M4zqDGlW) confirmo que ADR-0002 ya estaba
aceptado por las cuatro personas e integrado en PR #71. Solo quedaba emitir
y validar las claves virtuales. No se repite ni se reinterpreta el benchmark
historico; la latencia y fiabilidad siguen teniendo las limitaciones del ADR.

Gateway nuevo `economicon-jup078-gateway`, DockerServer, administracion
loopback 44000, LiteLLM 1.103.2 y PG17 fijados por digest, base propia.
Los contenedores previos 4000/4100 se conservaron. El 4100 historico seguia
activo en 1.82.6: no confundir su existencia con la baseline aprobada.

Claves de 30 dias: processor USD9 para chat principal+embeddings, backend
USD1 para embeddings. Total USD10, RPM10/TPM20000/concurrencia1 por clave.
No hay rotacion automatica ni asignacion adicional para DeepSeek. Caducidad
2026-11-09 20:31 Europe/Paris; renovar requiere conciliacion de gasto/ventana.
Contadores asincronos: no garantizan reserva atomica ni evitan todo exceso
por llamada. Los limites mas restrictivos del uso real siguen vigentes.

## Evidencia y reproduccion

- [Cierre operativo](../evidence/JUP-078-operational-closure.md): comandos,
  resultados, rutas privadas (sin valores) y atribucion de subagentes.
- [ADR-0002](../adr/ADR-0002-litellm-openrouter.md),
  [runbook](../../infra/litellm/README.md) y
  [herramienta](../../tools/litellm-product-keys.py).
- Emision, scope, denegacion de administracion y persistencia tras recrear
  el gateway verificadas sin invocar modelos; recibos no contienen claves.

## Siguientes pasos

Pruebas simuladas: 26/26 pasan, revision asistida APPROVE. Pendiente de
publicacion: PR/CI y estado final de Trello. No hay autorizacion para publicar en Discord. Las revisiones asistidas
se atribuyen a subagentes, nunca como intervenciones de los miembros humanos.
