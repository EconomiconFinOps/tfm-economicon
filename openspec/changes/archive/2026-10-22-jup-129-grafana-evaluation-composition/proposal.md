JUP: JUP-129
Trello: https://trello.com/c/07J4M5ZN

# Lectura narrativa de la evaluación en Grafana

## Why
La evaluación y las señales técnicas están repartidas en tablas y dos dashboards. La persona lectora necesita distinguir resultados, diagnóstico y límites sin sumar campañas o convertir ausencias en ceros.

## What Changes
- Provisionar una composición nativa con resultado de una campaña, anillo y perturbaciones; core/conversación, recuperación/calibración, rendimiento/modelos y secundarios plegados.
- Usar lenguaje funcional, conservando identificadores sólo en contratos y evidencias internos.
- Comparar una pareja explícita únicamente con contexto compatible; indicar ausencia o incompatibilidad sin inferir mejora.
- Mantener los dos dashboards y UID previos como superficies de auditoría/operación y sus contratos de conciliación; la nueva composición es la entrada narrativa de la guía.
- Adaptar la composición aprobada a la proyección real: el manifiesto de la base no carga la campaña experimental ni el suplemento de modelos.

## Impact
Nuevo JSON y pruebas de composición; guía, evidencia y continuidad. Sin cambios de loader, adaptadores, informes, manifiestos de datos, datasource, permisos, backend o frontend. Sin incorporar producto de PR144, métricas nuevas ni campañas.
