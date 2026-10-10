JUP: JUP-060

## Diseño documental

docs/architecture.md es la entrada técnica consolidada. Reutiliza fuentes
canónicas de código, OpenSpec, ADR y evidencia; no duplica la memoria del TFM.
Fija base c2995a118d419dfe725247bac9c6f219a3f0ea77 y fecha de contraste.
Diagramas Mermaid editables distinguen conexiones implementadas, opcionales y
objetivo. El mapa de datos es lógico, no atribuye FK entre bases.

## Decisiones

ADR: not applicable — no se cambia la arquitectura ejecutada ni se ratifica
hosting productivo; se documenta lo implementado y una alternativa cloud de
referencia con Terraform sin ejecución.
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
- Propuesta EC2 del 09/10 conservada como antecedente con aviso de alcance
  superado. Esquema AWS y Terraform del 10/10 incorporados como documentación;
  no precios actuales, credenciales, plan real ni apply. PostgreSQL/Cognito/
  Bedrock requieren adaptaciones hipotéticas y no se presentan como runtime.
- Memoria: solo apartado d/JUP-060, revisión humana y autorización de su líder;
  no leer otros apartados para obtener contexto ni editar e/f/g/h/i.

## Verificación

Contraste de fuentes con dos inspecciones estáticas auxiliares (no reviews
humanas), enlaces/anchors, Mermaid, OpenSpec estricto, trazabilidad e higiene
y checks de gobernanza aplicables. Sin repetir runtime ajeno o usar proveedor
pagado para un cambio documental. Registrar comandos/resultados en
[la evidencia](../../../docs/evidence/JUP-060-validation.md).

La plantilla en infra/aws-reference usa Terraform 1.13.3 y proveedor AWS 6.13.0
fijado, con mock_provider regional y edge. Verificar formato, validate, los seis
runs simulados y las ocho rutas Node desde su ubicación versionada. Solo se
incorporan fuentes/lockfile/guía: no ZIP, caché de proveedores, binarios, state
ni tfvars reales. Los nuevos diagramas y enlaces se validan tras su traslado.

## Cierre

Change activo mientras quede incorporación/aceptación del entregable y reviews
humanas. Esta excepción es visible en tasks y evidencia; no archivar por mera
disponibilidad de una contribución ni marcar Trello Hecho.
