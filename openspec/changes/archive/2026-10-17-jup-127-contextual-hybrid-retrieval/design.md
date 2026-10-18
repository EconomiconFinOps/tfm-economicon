# Diseño — JUP-127

JUP: JUP-127
Trello: https://trello.com/c/AG5fAbl3

## Context

Formalización del trabajo experimental existente, dependiente de JUP-124/JUP-125.
Selección D aprobada por Paris el17/10; base `3dc2268a` incorpora develop1de41b90.
El delta exclusivo de E se separó íntegro con copia/hash antes de retirarlo.
Roles asignados por PM: Paris liderazgo, Lucía pairing, Alejandro revisión,
Víctor validación. La asignación no acredita aportación o revisión realizada.

## Goals / Non-Goals

Identificar espacios y recetas, reutilizar embeddings compatibles, mantener
snapshots/fuentes y activar D sin mezclar datos ni atribuir identidad a legacy.
No añadir funciones del chat, interpretar fórmulas, alterar bancos o rúbricas,
cambiar proveedor/modelo/dimensión, desplegar ni iniciar nuevas campañas.

## Decisions

Véase [ADR-0024](../../../../docs/adr/ADR-0024-verified-contextual-retrieval.md)
(Proposed, ratificación humana pendiente) y [guía](../../../../docs/embedding-indexes.md).

1. Espacio canónico: proveedor, small1536/coseno, huella mapping, tokenizer exacto,
   preparación y límites; no tenant/generación. Vincular model_info.id y cabecera
   nativa del gateway al mapping acreditado; alias/dimensión no bastan.
2. `contextual_embedding_v1` antepone sólo título/jerarquía acreditada/tipo;128tokens,
   entrada1024tokens/16384bytes, sin LLM ni metadatos operativos. Mantener content,
   posiciones y avisos por revisión. Lotes≤16,16384tokens,262144bytes JSON.
3. Migración004 aditiva: espacios, caché, revisiones/chunks, generaciones/membresías
   y cabeza por tenant. Caché tenant/espacio/SHA256UTF8; ganador canónico y contador
   desconocido de consulta NULL. No atribuir modelo a vectores históricos.
4. Construir snapshot completo sin activar; finalizar sólo la ejecución vigente
   (F1). Publicar/activar por CAS con permisos y catálogo revalidados. Lectura fija
   REPEATABLE READ conserva generación tras embedding y durante fuentes/citas.
5. F2 evita que mantenimiento de last_used_at pierda un hit válido; inserción
   concurrente reintenta sólo SQL40001, nunca la inferencia. Plazo/cancelación
   comunes siguen vigentes. No promete una única llamada entre carreras.
6. D: structural_recursive1.0.1 600/800/0.1 (60presupuesto), contexto determinista,
   FTS simple/GIN + dense exacto.20por carril, pool20, RRF60 desde rango1, desempateID;
   .6inclusivo dense,4semillas y vecinos±1 autorizados. F3 compara literales,
   operadores, magnitudes/unidades y cierra expresiones no soportadas; no fórmulas.
7. Perfil explícito sin cambiar OFF general: preparar todos los tenants, inspeccionar
   ready/completitud/catálogo, CAS y sólo después habilitar flags globales. No hay
   fallback automático para tenant sin cabeza. Legacy de dimensión8 necesita otra
   base/reindexación autorizada, nunca alterar columna o reutilizar sus vectores.
8. OFF recupera legacy compatible conservado. Rollback exige catálogo compatible;
   rebuild sobre catálogo actual puede costar y requiere autorización. Retención
   protege activa/anterior/evaluación; sin prune automático en activación.

## Risks / Trade-offs

La política lexical conserva exactitud y puede reducir recall; no se declara
ganador global. El gateway es dependencia de confianza y su mapping requiere
acreditación operativa. Índice contextual/cache añade almacenamiento. Sin fallback
por tenant, habilitar flags globales prematuramente puede causar indisponibilidad.
Un carril fallido no se oculta como hybrid correcto. Las correcciones F1/F2/F3 y
develop actual diferencian este candidato de D histórica.

## Migration Plan

Seguir [preparación/activación/retorno D](../../../../docs/rag-d-activation.md), sin
servicios nuevos. Migración004 conserva tablas antiguas. Aplicación/mantenimiento
de esquema pertenecen a preparación del processor; CLI no migra. Compose transmite
configuración y doctor no prueba readiness SQL. CD de demo conserva legacy y no
promueve D de un runtime externo. El fallo heredado de preparación de contraseña
Grafana se conserva y corrige con procedencia del ajuste ya autorizado, generación
sólo ausente y preservación/idempotencia; sus pruebas conservan los controles RAG.

## Validation

[Evidencia JUP-127](../../../../docs/evidence/JUP-127-validation.md). Separar suites
focales nuevas, replay con vectores históricos, campañas originales y dictámenes
independientes; mantener originales adversos y costes, sin repetir campaña.
Archivo, CI remota, reviews humanas y publicación permanecen en su fase del proceso.
