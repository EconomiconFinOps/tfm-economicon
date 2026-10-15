# Citas documentales sin peticion explicita - 11/10/2026

Cambio minimo autorizado por el usuario: toda afirmacion de answer apoyada en
corpus debe seleccionar en evidence los ids exactos de las fuentes realmente
usadas, aunque no se pidan citas. Recuperar no implica usar. No listar todo el
corpus, inventar referencias ni convertir recuerdos en evidencia documental.

Se modifica solo system.md y system_sha256 del manifest del bundle chat/v2.
FinOpsResponse, input, tokenizer, contratos, limites y endpoints no cambian.
La version sigue el patron existente kind:SHA256(manifest canonico):

`jup-035.chat.v2:2e88ca61d7768c579b03031d406c206e144bcdacbde136b0218774bec2575d9a`

SHA256 system nuevo:
`8c93b404813a317f68d6cc33418cf6c1de9f2896afde8cba5769d89ea82c9ee4`

SHA256 system anterior:
`f92dc4213b18abbd310fdd15237d0c943a100f2766f3bbb0be87566fed0039d5`

El backend conserva validacion de ids y procedencia; response_citations resuelve
solo evidence seleccionado contra el contexto congelado. No se agrega fallback
de todas las fuentes recuperadas. El prompt no ofrece deteccion semantica perfecta
del uso de una fuente ni garantiza por si solo obediencia del modelo.

Prueba focal nueva: ausencia de instrucciones produce Red significativo (1 fallo).
Suite de recursos processor: 16 PASS, incluyendo integridad y rechazos de bundle.
Carga backend del mismo bundle: PASS, system 794 tokens y schema sin cambios.
Todo offline, contenedores desechables, W readonly; sin llamadas al modelo.
Logs externos: restart-20261011/citation-prompt-{red,green,backend-load}.log.

Despliegue local a cargo del padre: backend y processor deben cargar el mismo
bundle apps/processor/app/agents/prompt_resources/jup035/chat/v2 mediante su
CHAT_RESOURCE_DIRECTORY existente (backend empaquetado: /opt/economicon/chat/v2).
Si usan copia empaquetada, actualizar ambos archivos juntos; si usan W montado,
reiniciar ambos procesos. Conservar tokenizer y configuracion restantes.
El descriptor debe anunciar la version completa indicada arriba; mezcla de
versiones debe fallar cerrada. No se ha cambiado runtime.

Validacion viva pendiente del padre, con pregunta sin pedir cita:
"Segun el procedimiento NEXO-LIMA, como se revierte la anomalia?"
Contrastar evidence y citas persistidas con el fixture sintetico ya cargado.
No equivale a aceptacion final, publicacion o merge.
