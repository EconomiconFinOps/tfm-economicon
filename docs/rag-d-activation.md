# Configuración D: preparación, activación y retorno

D selecciona chunking estructural `structural_recursive` 1.0.1, objetivo 600,
máximo 800 y presupuesto de solapamiento 60 tokens (`0.1`; el efectivo depende de
la estructura). El índice usa contexto determinista `contextual_embedding_v1`,
128 tokens de contexto, entrada máxima 1024 tokens/16384 bytes; el contenido y
las posiciones documentales no cambian. Tokenizer: `tiktoken/0.14.0:cl100k_base`
con recurso SHA256 `223921b76ee99bde995b7ff738513eef100fb51d18c93597a113bcffe865b2a7`.

El modelo resuelto es `openai/text-embedding-3-small`, 1536 dimensiones, coseno y
`decimal6_v1`; consulta `plain_query_v1`. Cada carril dense/FTS aporta hasta 20
candidatos; FTS usa `pg_catalog.simple`, `tsvector` persistido y GIN. La generación
se construye con `--retrieval-mode hybrid --rrf-k 60`, política `literal_context_v1`,
rangos desde uno y desempate por ID. Umbral dense inclusivo 0.6, unión máxima 40,
pool final 20, cuatro semillas de chat y vecinos ±1 de la misma revisión/pool.
La recuperación lexical conserva su distancia real, que puede superar 0.6.

## Preparar sin interrumpir legacy

Los ejemplos [de entorno](../infra/rag/d.env.example) y
[de espacio](../infra/rag/space-d.example.json) son entradas del operador, no una
activación automática. Conservar el entorno completo y privado actual, el
catálogo, los vectores legacy y la cabeza/versión anterior de cada tenant.
Mantener las tres opciones RAG en `false` mientras se construyen y verifican los
índices. Aplicar la migración aditiva 004 mediante la preparación existente del
processor; `app.reprocess_document` no migra el esquema.

Comprobar primero la dimensión almacenada de `chunk_embeddings`. Este recorrido
requiere un catálogo legacy de 1536 dimensiones y el proveedor acreditado para
seguir consultándolo mientras se prepara D. Un almacén mock de 8 dimensiones
**no** se convierte cambiando el entorno: su startup rechaza la discrepancia.
Conservarlo operativo y preparar otra base de 1536 con su catálogo autorizado y
reindexación presupuestada; no alterar la columna ni atribuir identidad a sus
vectores. No llamar al proveedor ni reconstruir sin presupuesto/autorización.

Copiar los ejemplos fuera de Git, dentro del entorno privado del operador.
La huella de mapping del JSON es la histórica de D; inspeccionar el mapeo efectivo
no secreto y acreditar modelo, dimensión, huella y `model_info.id` del gateway
actual como describe [la guía de índices](embedding-indexes.md). Si cambia la
huella, editar la copia del descriptor y registrar su nuevo ID de espacio. No
rellenar el entorno con un ID histórico por semejanza del alias. El ID histórico
`83fa478ee20fee366f33ce23d434cb8bb0c2f3bb6f75eae3bccc4bba296d4580` sólo corresponde
al descriptor original. Verificar también el chunking persistido: construir una
generación no vuelve a fragmentar documentos. Un catálogo anterior con otra
receta requiere reprocesado explícito desde checkpoint, conservando sus originales.

Con el processor de preparación ya configurado para el proveedor de 1536,
descriptor privado acreditado y tres opciones OFF, ejecutar para **cada tenant**:

```sh
python -m app.reprocess_document --action inspect --tenant-id TENANT --created-by OPERADOR
python -m app.reprocess_document --action build --tenant-id TENANT --created-by OPERADOR --space-file /private/space-d.json --retrieval-mode hybrid --rrf-k 60
python -m app.reprocess_document --action inspect --tenant-id TENANT --created-by OPERADOR --generation-id GENERACION
```

El operador y los propietarios documentales deben seguir siendo miembros del
tenant, con trabajos completados. Conservar las salidas y comprobar `ready`,
`complete`, catálogo vigente, descriptor, manifest y `retrieval_config`: modo
hybrid, k60, límite20 y política literal. Revisar avisos de contexto recortado.
Una reanudación usa `--resume-generation GENERACION` y conserva el fallo original.
No sustituir vectores, borrar tablas o activar una generación incompleta.

## Activar D

Capturar la cabeza y versión inmediatamente antes de cada CAS. Sólo cuando
`inspect` devuelve cabeza legacy y versión0 se usa este ejemplo:

```sh
python -m app.reprocess_document --action activate --tenant-id TENANT --created-by OPERADOR --generation-id GENERACION --expected-head legacy --expected-version 0
```

En los demás casos, pasar el ID y la versión observados; un conflicto exige
inspeccionar/repreparar, nunca forzar. Verificar la cabeza resultante y conservar
la anterior. Las opciones RAG son globales para el backend: **todos los tenants
servidos deben tener una cabeza compatible antes de habilitarlas**. No existe
fallback automático a legacy para un tenant sin índice verificado. Mantener la
consulta legacy hasta completar estas comprobaciones, con permiso y catálogo
vigentes; no anunciar D por haber activado sólo un tenant.

En el checkout exclusivo del runtime autorizado, integrar los valores de
`d.env.example` en su `.env` privado completo junto a `docker-compose.yml`,
rellenando mapping/deployment acreditados y conservando claves distintas de
backend/processor, URLs, HMAC y demás secretos. Shell/entorno del proceso tiene
precedencia: comprobar que no sobrescribe estos valores. Ejecutar `local:doctor`
con ese entorno completo y renderizar Compose antes de recrear los consumidores:

```sh
corepack pnpm local:doctor
docker compose --env-file .env config --quiet
docker compose --env-file .env up -d backend processor
```

El doctor lee `.env` del directorio del proyecto (o `--project-directory`), no
`ECONOMICON_ENV_FILE`; esta última opción pertenece al arranque Python cuando se
ejecuta fuera de Compose. El doctor comprueba configuración, credenciales, puertos
y dependencias locales;
**no** acredita la identidad remota ni consulta la completitud de PostgreSQL.
Compose propaga dimensión/proveedor y mapping/deployment a ambos servicios,
chunking al processor y opciones/umbral/top-k al backend. Hacer una comprobación
local de consulta, fuentes, citas e historial y conservar el plan efectivo; un
fallo de un carril no puede presentarse como hybrid degradado correcto.

El CD actual prepara su propio entorno de demo y conserva el modo legacy por
defecto; no consume este perfil ni acredita índices de un runtime externo. No
modificar una release inmutable ni activar D desde el workflow de CD. La promoción
de D se realiza en el entorno autorizado después de las comprobaciones anteriores;
el éxito de CI/CD por sí solo no acredita esa promoción.

## Retorno seguro

Ante problemas de lectura, restaurar primero las tres opciones RAG a `false` en
el entorno privado y recrear backend: vuelve al recorrido legacy compatible que
se conservó, sin borrar la generación D. Mantener la configuración de dimensión
y proveedor que corresponda a ese catálogo, no volver a mock/8 sobre tablas1536.
Para cambiar la cabeza, `--action rollback --expected-head ID --expected-version N`
exige catálogo compatible y devuelve la anterior verificada; **no** desactiva las
opciones ni restaura automáticamente una cabeza legacy nula. Si el catálogo
cambió, conservar el rechazo; `--rebuild` necesita autorización/presupuesto y
construye sobre el catálogo actual, sin recuperar permisos revocados. Proteger
generaciones de evaluación con `--keep-generation`; no ejecutar prune como parte
de la activación. Nunca reutilizar un vector entre tenants o espacios.

## Evidencia y límites

Se preservan las correcciones posteriores F1 (constructor obsoleto), F2 (caché
concurrente) y F3 (comparadores/unidades/separadores). Esta política lexical más
conservadora distingue el candidato actual de D histórica, además de la base
develop reconciliada. No se trasladan calculadora Decimal, proyección privada,
prompts ni otras funciones del ensayo E a este cambio RAG.

D histórica registró 68/68 respuestas y 64/68 aceptaciones asistidas, con mejor
contexto adicional y menor cobertura original que A/B. Es evidencia histórica de
otro candidato; no demuestra mejora universal ni la calidad del actual. E sigue
cancelada. Las pruebas locales y el replay de vectores conservados deben declarar
su procedencia y no cuentan como nuevas llamadas ni nueva campaña.
