# Diseño registrado retrospectivamente — JUP-125

JUP: JUP-125
Trello: https://trello.com/c/H0RUnArf
Registro: 16/10/2026. Describe decisiones ya implementadas y aprobadas durante
la etapa experimental; no simula un diseño previo al código.

## Contexto y base

JUP-124 proporciona normalizado v1 y checkpoint durable después de retirar los
originales. `document.text` es el texto canónico; los bloques son anotaciones
que pueden superponerse o dejar huecos. La estructura incompleta no autoriza
inventar posiciones ni volver a extraer documentos.

R2 fue preservado por PM en `5dc6374743f66370c9f50ade1a73abc287d329e5`.
La incorporación autorizada `238963938e1947fe6d9e3a04900761683d11f6aa` añade
JUP-124 `e126b21703a90dd7d03747a6b51bc4b5d246cf29`: sólo sandbox y su test
cambian producto; seis rutas modificadas y ocho documentos añadidos frente a R2.
Los bytes de chunking, regresiones y fixtures permanecen iguales. Después PM
incorporó el único test health evaluado `eb4453f96b7bab819bf4ba692e6bdcf7e521f2ef`
mediante `2bf31fe356aeccc45991c9f91d65dfbba29b003d`: los JWT se crean al ejecutar
cada caso, sin cambiar TTL/leeway/auth o runtime. Las otras 1.660 fuentes y los
13 documentos de formalización se conservaron; ésa es la base final de cierre. Develop
`53b43bb1` está incluido, según comprobación PM del 16/10; no es un fetch nuevo.

La decisión duradera existente se registra en
[ADR-0023](../../../../docs/adr/ADR-0023-deterministic-document-chunking.md), Proposed.
Se conservan los límites y estados de ADR-0008, ADR-0011, ADR-0013, ADR-0017 y
[ADR-0022](../../../../docs/adr/ADR-0022-document-ingestion-artifact-lifecycle.md).

## Recorrido y separación de responsabilidades

1. `IngestTask` y el grafo reciben el normalizado, con fallback manual explícito.
   El resultado compacto del job no duplica normalizado ni chunks completos.
2. `structure` alinea anotaciones con slices exactos del texto canónico. Markdown
   usa las líneas CR/LF/CRLF del parser, no el dominio Unicode de `splitlines`.
   Un checkpoint antiguo desalineado produce warning y referencia desconocida.
3. El chunker preserva secciones/subsecciones que caben en máximo; si un padre
   excede el límite, desciende por headings antes de dividir por unidades.
   Tablas priorizan filas; listas conservan relación padre/hijo disponible; código
   prioriza líneas. Último recurso: caracteres Unicode válidos con conteo real.
4. El contenido efectivo incluye overlap/cabeceras/contexto repetidos y nunca
   excede el máximo. Se registra su procedencia y overlap efectivo; no se repite
   contexto entre secciones independientes ni se clasifica con un modelo.
5. `validate` comprueba integridad y reconstrucción antes de embeddings/SQL.
   El proveedor recibe sólo `content`, sin nueva contextualización. Modelo,
   dimensión, coseno, ranking y prompts siguen iguales.
6. `PgVectorStore` publica padre, chunks y vectores en una transacción. Un CAS
   operativo distinto de la identidad determinista rechaza resultados obsoletos.
   Fallo del proveedor/SQL conserva la versión consultable anterior.
7. Recuperación/citas usan metadata persistida y snapshots coherentes; el fallback
   textual se conserva para legacy, sin reindexación obligatoria.

## Tokenizador y metadata

Objetivo 600, máximo 800 y overlap 0,1 del objetivo son configurables bajo el
contrato existente; el máximo incluye repeticiones. tiktoken 0.14.0/cl100k_base
queda fijado por versión, tamaño y SHA. El preparador descarga/verifica fuera del
checkout en preparación/build; runtime no descarga ni usa otro tokenizer como
equivalente. El tokenizador GLM de chat permanece independiente.

Cada chunk conserva identidad/orden/contenido/tokens/hash, estrategia/versión,
configuración/tokenizador, spans primarios/repetidos, fragmentos y procedencia.
El padre conserva metadata documental y manifiesto, sin duplicación indiscriminada.
Offsets normalizados: caracteres Unicode, base 0, fin exclusivo. Líneas/páginas
originales: base 1; bbox sólo con sistema declarado por el extractor. Las
ubicaciones no disponibles quedan desconocidas.

## Reconstrucción y correcciones preservadas

`reconstruct_normalized_text(chunks)` usa sólo chunks y metadata: orden, rangos
primarios, exclusión de repetición y texto exacto de blancos omitidos. El primer
chunk conserva longitud/hash/count y omisiones; no recibe el padre para rellenar
huecos. Verifica cobertura, hashes, identidad, repetición y grupos; conjuntos
incompletos/incoherentes fallan explícitamente. Se reconstruye texto normalizado,
no bytes/layout de PDF/Word ni estructura que el extractor no proporcionó.

R1 conservó parentesco TXT indentado; A corrigió rangos Unicode Markdown y su
consumidor extractor; B preservó subsecciones que caben dentro de un padre grande.
R2 corrigió el recuento después de omitir piezas sólo blancas: índice/total
describen registros efectivamente persistidos. La función de reconstrucción y
sus negativos no se relajaron. Informes originales FAIL y regresiones permanecen.

## Persistencia, reprocess y compatibilidad

Migración vectorial 003 añade JSONB con `{}` por defecto; conserva legacy y sus
vectores. El operador puede reprocesar un documento completed sólo con propietario,
tenant y checkpoint íntegro autorizados. No hay endpoint nuevo, ejecución masiva
automática ni reextracción. Un documento sin checkpoint sigue consultable con su
contrato previo; no se promete reconstrucción exacta de legacy sin descriptor.

## Evidencia, riesgos y cierre

[Matriz de quince criterios](../../../../docs/evidence/JUP-125-validation.md) y
[runbook](../../../../docs/runbooks/document-chunking.md) identifican pruebas
reproducibles, campañas y límites. La comparación real es exploratoria: seis
documentos/doce preguntas, Recall 12/12 en ambos y 25→9 chunks; no prueba mejora
general. OCR ambiguo y estructura ausente conservan advertencias honestas.

La formalización/base nueva exige decisión de vigencia por ambos evaluadores y
controles PM nuevos; no extiende automáticamente los PASS anteriores. Archivo,
aprobación humana, CI y publicación están separados. No comienza fase 3 aquí.
