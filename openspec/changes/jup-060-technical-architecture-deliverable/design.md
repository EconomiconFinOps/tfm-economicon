JUP: JUP-060

## Diseño documental

docs/architecture.md es la entrada técnica consolidada. Reutiliza fuentes
canónicas de código, OpenSpec, ADR y evidencia; no duplica la memoria del TFM.
Fija base c2995a118d419dfe725247bac9c6f219a3f0ea77 y fecha de contraste.
Diagramas Mermaid editables distinguen conexiones implementadas, opcionales y
objetivo. El mapa de datos es lógico, no atribuye FK entre bases.

## Decisiones

ADR: not applicable — no se cambia arquitectura; se documenta lo implementado.
Se conservan estados y razones en [índice ADR](../../../docs/adr/README.md),
especialmente 0006 (secretos), 0008/0009 (autoridad y cola), 0011 (DDL),
0013/0014/0015 (vector/auth/Compose) y 0017 (embedding de consulta).
No ratificar propuestas mediante este change.

## Fronteras

- Chat plantilla + retrieval no equivale a LLM conversacional.
- Job documental no activa la ingesta Azure por CLI.
- OpenSpec de tools no equivale a registro ejecutor implementado.
- Compose y evidencia histórica no equivalen a inventario vivo.
- JUP-052/PR73 no integrado en base; CI no equivale a CD.
- Propuesta AWS preservada byte a byte del 09/10; no precios actuales ni apply.
- Memoria: solo apartado d/JUP-060, revisión humana y autorización de su líder;
  no leer otros apartados para obtener contexto ni editar e/f/g/h/i.

## Verificación

Contraste de fuentes con dos inspecciones estáticas auxiliares (no reviews
humanas), enlaces/anchors, Mermaid, OpenSpec estricto, trazabilidad e higiene
y checks de gobernanza aplicables. Sin repetir runtime ajeno o usar proveedor
pagado para un cambio documental. Registrar comandos/resultados en
[la evidencia](../../../docs/evidence/JUP-060-validation.md).

## Cierre

Change activo mientras quede incorporación/aceptación del entregable y reviews
humanas. Esta excepción es visible en tasks y evidencia; no archivar por mera
disponibilidad de una contribución ni marcar Trello Hecho.
