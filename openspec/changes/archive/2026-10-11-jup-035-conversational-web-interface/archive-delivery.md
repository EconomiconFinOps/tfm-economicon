# JUP-035 — Entrega y autorización de archivo

Fecha: 2026-10-11. Paris autoriza expresamente: «ok archiva openSpec y prepara el PR». La preparación no autoriza push, creación de PR, publicación de mensajes ni merge.

## Estado vigente

La entrega local incluye chat con streaming por backend/processor/gateway, panel assistant-ui, aislamiento tenant/usuario, historial JSONB con pares completos atómicos, títulos y borrado, citas documentales, contexto de pantalla preparado, compresión mediante LLM y Compose mock/IA. HEAD previo al archivo: 8886494532883dc83d04a6139b8fbe9f213a84e8; incorpora develop 3b8e95288000b1f14513cbc5158324017554f514.

Este corte sustituye los estados de ejecución anteriores que indicaban E5, resumen real, consumo del resumen, Compose o reconciliación pendientes. Los documentos, casillas y fallos anteriores se conservan como registro de sus fases; no se convierten retroactivamente en PASS. Las tareas administrativas e independientes sin evidencia específica tampoco se marcan como realizadas.

## Evidencia conservada

- [Compresión y reutilización por un turno posterior](../../../../docs/evidence/jup-035-conversation-memory-validation.md): resumen persistido utilizado por la siguiente pregunta; originales conservados. La comprobación posterior sizes-real identifica el mismo artefacto 98b7df18-e875-4144-9e1b-90ec2f5575ca usado por el consumidor 2911a4bd-8100-4d0c-9bea-396b083fab1d, con 68 mensajes preservados. No es una comprobación pendiente global.
- [Período calculado por servidor](../../../../docs/evidence/jup-035-server-period-correction.md) y [respuestas no accionables](../../../../docs/evidence/jup-035-non-actionable-prompt-correction.md).
- Compose mock/IA: arranque, streaming, persistencia y recuperación de compresión real. Repetición independiente limitada: un resumen válido f54f27a9-2c16-4cee-9178-ab1dc893d3cc, tres pares procesados, 14 mensajes idénticos y conservación tras reiniciar backend. Su duración de 10.135 s no prueba una llamada real superior a 30 s; las fronteras de timeout tienen pruebas automatizadas.
- Incremento reconciliado: backend 72 PASS, frontend 65 PASS más tipos/build, processor 88 PASS y topología 35 PASS; tres mutaciones detectadas. Revisión incremental independiente favorable con cinco comprobaciones propias. Builds reales de ambas imágenes satisfactorios, reutilizando caché de dependencias.
- Recibos originales: e5-context-compression-evidence/restart-20261011/compose-chat/runtime/ai-repeat-validation.md, summary-timeout/delivery.md y merge-develop/parent-integrity.md en la entrega local de Autónomo. Son artefactos externos, no enlaces públicos ni nuevas ejecuciones del PM. La referencia del padre no se presenta como guard independiente creado por el PM.

## Límites y siguientes gates

Las llamadas reales anteriores conservan fecha, snapshot y entorno originales; no se etiquetan como repetición real del árbol fusionado. No se ha desplegado ese árbol en los stacks existentes. El RAG documental sintético observado con fuente NEXO-LIMA acredita ese recorrido; no certifica exactitud financiera ni un corpus productivo con embeddings reales. Permanece la incidencia transitoria E4 de carga de costes, sin causa ni arreglo acreditados; Paris autorizó registrarla y avanzar.

No se declara ejecución de la batería formal JUP-069, revisión humana, validación humana, CI remota, despliegue en DockerServer ni cierre global. El control de integridad prepublicación del PM debe conciliar las referencias originales aplicables; el archivado no elimina ese requisito.

Roles de la tarjeta en el último export oficial disponible: Paris liderazgo, Víctor pairing, Alejandro revisión, Lucía validación. Confirmar vigencia al publicar; los agentes no sustituyen participación humana.