## 1. Contrato y prompt

- [x] 1.1 JUP-024 definir `FinOpsResponse` version 1.0 y sus objetos anidados
- [x] 1.2 JUP-024 definir estados, evidencia, metricas y recomendaciones
- [x] 1.3 JUP-024 sustituir el prompt generico por instrucciones FinOps seguras
- [x] 1.4 JUP-024 delimitar metadata como datos no confiables

## 2. Guardrails runtime

- [x] 2.1 JUP-024 validar source, status, tenant y metadata antes del provider
- [x] 2.2 JUP-024 redactar claves de secretos sin modificar datos FinOps publicos
- [x] 2.3 JUP-024 pasar JSON Schema estricto y validar otra vez con Pydantic
- [x] 2.4 JUP-024 exigir evidencia y aprobacion humana para salidas accionables
- [x] 2.5 JUP-024 devolver mock estructurado sin recomendaciones inventadas

## 3. Pruebas y documentacion

- [x] 3.1 JUP-024 probar schema, metadata no confiable, secretos y aislamiento de tenant
- [x] 3.2 JUP-024 probar fuentes no Azure, campos extra y referencias de evidencia
- [x] 3.3 JUP-024 probar estados no accionables y cifras sin evidencia
- [x] 3.4 JUP-024 documentar contrato, limites y fuentes oficiales
- [x] 3.5 JUP-024 ejecutar validacion completa y registrar evidencia
- [x] 3.6 JUP-024 publicar rama, abrir PR hacia develop y actualizar Trello
- [ ] 3.7 JUP-024 obtener pairing, revision y validacion de los otros miembros
