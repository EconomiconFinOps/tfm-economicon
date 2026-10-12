JUP: JUP-035
Trello: https://trello.com/c/BJfABykd

## Why
PR120 solo admite required y rechaza decisiones nativas en auto. La orden del
12/10/2026 autoriza un parche separado sobre f63c150, sin publicar ni desplegar.

## What Changes
- Contrato auto-documentation-v2: decision privada auto sin esquema final;
  cero/una busqueda backend y finalizacion estricta none, maximo dos generaciones.
- Actualizar prompt, hashes, ambos servicios y regresiones sin relajar validadores.
- Mantener limites, proveedor, aislamiento y autoridad financiera existentes.
- Corregir la entrega del evento terminal ante carreras SQL/RAM y hacer
  reproducibles los fixtures backend de autenticación, pgvector y summary SQL.

## Impact
Processor, backend y especificacion conversational-web-interface. Despliegue
coordinado requerido por hashes incompatibles; no compatibilidad silenciosa con
required-documentation-v1. El archivo de la entrega previa se conserva intacto.
La compatibilidad del proveedor y batería real de 28 preguntas siguen pendientes;
no se heredan presupuestos ni resultados de otros SHA. El usuario autoriza el
12/10 la revisión y validación asistidas del parche, atribuidas al agente.
