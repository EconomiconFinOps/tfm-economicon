JUP: JUP-021
Trello: https://trello.com/c/0oUtjfnH

## Why

El baseline contiene pgvector y retrieval, pero carece de una prueba reproducible
de arranque, persistencia y restauracion, y no detecta al iniciar una dimension
configurada incompatible con el esquema existente.

## What Changes

- Despliegue aislado reproducible con imagen fijada por digest, volumen y puerto local.
- Migracion incremental del indice por tenant, conservando busqueda coseno exacta.
- Rechazo de dimension incompatible al iniciar y antes de reemplazar documentos.
- Smoke con escritor y lector reales, dos tenants, recreacion y recuperacion.
- Runbook con limites de capacidad, configuracion del modelo y diagnostico.

## Capabilities

### New Capabilities
- `vector-database-runtime`: operacion verificable de PostgreSQL/pgvector.

### Modified Capabilities
- None.

## Impact

Processor, migracion vectorial 002, scripts y documentacion. No cambia el contrato
HTTP, ni introduce otro proveedor de embeddings. El runtime actual implementa mock;
la validacion demuestra almacenamiento/retrieval real, no calidad semantica de un
modelo externo. Revision humana y merge siguen el flujo protegido hacia develop.
