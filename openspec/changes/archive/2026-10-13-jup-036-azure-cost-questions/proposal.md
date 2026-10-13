JUP: JUP-036
Trello: https://trello.com/c/LxaVVLcH

## Why
El chat devuelve documentos, pero no consulta el gasto ingerido solicitado por la tarjeta.

## What Changes
- Selección explícita de suscripción, cuenta de facturación o servicio, valor exacto opcional y periodo UTC [inicio, fin).
- Respuesta determinista sobre ingestas completadas del tenant autenticado, con monedas separadas, procedencia y limitaciones.
- Entrada desde el chat; conservar la consulta documental sin selección de coste.
- No interpretar lenguaje natural libre ni llamar Azure real o un LLM para calcular importes.

## Capabilities
### New Capabilities
- `azure-cost-questions`: consulta de gasto trazable desde conversaciones.
### Modified Capabilities

## Impact
Backend assistant, agregación billing y formulario de conversaciones. Sin nuevas migraciones.
Pairing asignado Alejandro; liderazgo Victor. Contraste humano pendiente: esta propuesta no acredita pairing real.
