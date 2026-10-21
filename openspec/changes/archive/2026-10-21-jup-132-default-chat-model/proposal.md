JUP: JUP-132
Trello: https://trello.com/c/ERLZlPsT

# Un único modelo activo del chat

## Why
El ejemplo activo sigue ofreciendo GLM/Pro y los consumidores fijan FP4,
en contradicción con la continuidad elegida de DeepSeek V4.1 Flash.

## What Changes
- Mantener economicon-chat como único alias generativo, resuelto a
  openrouter/deepseek/deepseek-v4.1-flash por DeepInfra FP8 normal.
- Coordinar consumidores, diagnóstico, pruebas, documentación y ADR.
- Recursos activos v4 con tokenizer Flash oficial fijado/verificado; conservar
  lectores y recursos históricos sin alterar sus hashes o datos.
- Conservar embeddings, límites, privacidad, permisos y ausencia de fallback.

## Impact
Sin cambio de FinOpsResponse, despliegue, inferencias, credenciales, migraciones
o memoria canónica. Propuesta de consistencia de e/g separada para revisión humana.
