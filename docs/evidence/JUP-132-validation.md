# JUP-132: cambio del modelo por defecto

[Tarjeta](https://trello.com/c/ERLZlPsT) ·
[Diseño archivado](../../openspec/changes/archive/2026-10-21-jup-132-default-chat-model/design.md) ·
[ADR-0026](../adr/ADR-0026-default-chat-model.md).

## Candidato y alcance

21/10/2026, base b7c8b708c21a7cc37e3f84329811877db37f9618,
rama feat/JUP-132-default-chat-model. La evaluación identificó el parche local R2
sobre esa base; el archivado administrativo posterior conserva su implementación.
Paris liderazgo, Alejandro pairing, Lucía revisión, Víctor validación;
las asignaciones no acreditan participación o reviews humanas.

economicon-chat apunta sólo a openrouter/deepseek/deepseek-v4.1-flash por
deepinfra/fp8 normal. Se retira el alias Pro. Chat, resumen y diagnóstico
comparten ruta y reasoning desactivado. No se habilita fallback ni se amplían
límites, permisos, concurrencia o credenciales. Embeddings/1536, corpus y
tokenización de embeddings permanecen intactos.

Recursos activos chat/summary v4: tokenizer oficial Flash, revisión
314113f8a7dadb388215396ba5fbee2c610a04d6,6367257bytes, SHA256
c90dfa01249db1be4245780a052ede752e1361c612ac6d08e2bdada7d599476b.
La descarga y verificación ocurren en preparación/build, no en runtime.
V2/V3, sus contratos/huellas y tokenizer anteriores se conservan como lectores
históricos. Los gateways rechazan generar con lectores antiguos; no se reescriben
datos ni se cambian las ventanas actuales.

## Comprobaciones propias

| Comprobación | Resultado y límites |
| --- | --- |
| Configuración, topología y preparación Node | 45PASS; los3smokes omitidos por defecto se ejecutan separadamente abajo |
| Controles nativos PR/CI/gobernanza/trazabilidad/higiene | 150/150PASS,0omitidos |
| Backend: salud, contratos y recursos nuevos/antiguos | 208PASS,0omitidos |
| Processor: proveedores, recursos y gateway | Primera207PASS/1FAIL de fixture; tras corregirla43/43afectadas PASS, incluida la que fallaba;46/46transporte final PASS. No se suman ejecuciones solapadas como casos nuevos |
| Fetcher de tokenizer | 5/5PASS en Linux local sin red; original Windows incompleto conservado, no declarado PASS |
| Dependencia AI de gateway sano | PASS con Docker y red interna propia |
| Gateway LiteLLM real con upstream simulado | PASS: permisos y persistencia de claves exclusivamente sintéticas; no acredita campos efectivos del upstream |
| Compose mock completo | PASS:12servicios configurados,10daemons y2inicializadores correctos, backend saludable, sin gateway |
| Imágenes backend/processor | Builds PASS; carga offline de recursos y hashes de código contrastados |
| OpenSpec/trazabilidad/higiene | 88/88elementos,11changes e higiene favorables |

Las tres pruebas Docker finales pasan juntas:3PASS,0FAIL,0omitidas,141,89s.
Se ejecutan con valores centinela incompatibles en el entorno padre para comprobar
que no se heredan los proveedores ni las rutas de secretos del host. Los recibos
previos, también los fallidos, se conservan. Se corrigió sólo su
preparación antigua: variables/archivos sintéticos requeridos por el Compose
vigente, Minio/migrador y lista exacta de servicios, CIDR propio opcional para un
host con pool automático agotado. No cambia configuración de redes del producto
ni del daemon. Los dos inicializadores deben terminar con0; no se exige mantenerlos
como procesos vivos. Los proyectos verifican retirada al finalizar.

La suite Docker histórica completa del adaptador de ingesta no se repite: los
dos cambios de sus expectativas son el modelo y la ruta, comprobados por las
pruebas de configuración. El smoke no consulta estadísticas del upstream ni
acredita por sí solo los campos modelo/provider/reasoning/esquema efectivos. No se
atribuye a esta entrega una ejecución nueva de aquella suite. Tampoco se repiten
SQL, batería de preguntas ni build del frontend: no se modifica su lógica;
sí se construyen las dos imágenes Python afectadas y arranca la topología actual.

## Corrección tras evaluación independiente

La revisión R1 detectó dos carencias: procedencia del runtime todavía limitada
a v3/tokenizer histórico, y cinco expectativas de build/Compose/generación que
seguían usando v3. La validación R1 fue favorable exclusivamente offline; no
sustituye la revisión desfavorable ni se extiende automáticamente al delta R2.
Se conservan íntegros ambos informes y los controles originales de retorno.

Los planes nuevos ahora fijan Flash y el asset histórico; el verificador comprueba
ambos y los recursos chat/summary v4 en los dos servicios. Los planes antiguos
mantienen su selección explícita. Las pruebas negativas de omisión/alteración
fallaron antes del arreglo; sus regresiones, preparador y runner pasan25/25.
Las cinco expectativas se adaptan sin cambiar límites ni guard de lectura.
Las tres suites directamente afectadas pasan36/36, sin omisiones; no se repiten
los smokes ni builds porque el delta sólo modifica herramientas, pruebas y docs.
La revisión independiente R2 fue favorable: 60 comprobaciones propias pasaron
(24 de procedencia y 36 de dependencias directas); otra comprobación de
procedencia, que crea un helper de código, se reutilizó explícitamente de la
ejecución del liderazgo. La validación independiente R2 fue favorable únicamente
offline: 11 comprobaciones propias adicionales pasaron, sin omisiones; los 38
casos R1 y los tres smokes Docker se reutilizaron con justificación de identidad
y del delta. No se suman ejecuciones solapadas. Ambos informes R1 originales,
incluido el desfavorable, y los informes R2 se conservan en la entrega externa.

PM comprobó los dos retornos contra sus mismas referencias originales: estado
final intacto y cero violaciones. Este control detecta diferencias al retorno;
no demuestra aislamiento técnico ni descarta escrituras transitorias restauradas.

## Identidad de imágenes y recursos

- Backend: sha256:a017b7407f92da5518fc956347f7749b4dce7fb93ff8c09c5d6c21179848342e.
- Processor: sha256:85c37ae9b77ebb787a7cd97c049d56be785347103a53f6fa4fcadae98301e15e.
- Chat v4: db86b2787abb8c53489e90258bee8e81a810430b56c800370e506ea2dd684042.
- Summary v4: ba51412f3ab4cf752cf67aff4a12844acaf66c4a193d7befdf2082a439997052.
- Lectores summary v3/v2: b77cb54456152e08db25c57fef510b5864b0f2679db76e743cfe7a5b8a9c8634
  y f724d3fc8379d7926c667c9f5f3c43ed9074d34080a11fb5a1c76b2cd43b8b94,
  sin cambios.

Se reutilizan las imágenes previas de frontend/Azure/Minio únicamente como
infraestructura no modificada del smoke, no como una validación nueva de sus
funciones. Los comprobantes completos, manifiestos y salidas adversas se entregan
al liderazgo fuera del producto; no se incluyen secretos o informes con rutas
privadas en el artefacto público.

## Fallos conservados y correcciones

Pruebas negativas iniciales detectaron el mapping anterior y la incompatibilidad
de los recursos nuevos. Un primer ensayo de recursos importó módulos de la imagen
antigua; se corrigió el directorio ejecutor y sólo la reproducción sobre /src se
atribuye al candidato. Un runtime de pruebas antiguo no tenía email-validator:
se usó la imagen backend declarada y pytest de desarrollo, sin nueva dependencia
de producción. La fixture de esquema empaquetado seguía suministrando el tokenizer
anterior al bundle activo; se cambió a v4 sin eliminar sus aserciones.

El primer build backend sufrió timeout de descarga; el processor descargó y
verificó el mismo recurso, y el segundo build backend terminó correctamente sin
cambiar plazos. Windows dejó incompleto un ensayo del fetcher; se retiró sólo
ese proceso propio y las cinco pruebas equivalentes pasaron en Linux. No se
declara una causa Windows no demostrada ni se ocultan esos intentos.

## Corrección focal de CI posterior al archivado

La CI 39662397196 sobre 21441d23 terminó con 11 fallos, 2596 pruebas
superadas y 144 omitidas en processor. Se conserva el log original. Las dos
suites afectadas reproducen localmente los mismos 11 fallos y 6 éxitos.
La expectativa del prompt aún exigía v3; el doble de recursos del flujo de
revisión carecía de check_generation. Las dos esperas de cancelación tampoco
se alcanzaban por ese AttributeError, no por un timeout de producto demostrado.

Se actualiza la expectativa a v4 y el doble utiliza el guard real de
ChatResources con identidad v4/Flash. Se conservan todas las aserciones previas
de contenido, consumo, plazos y cancelación. Dos controles adicionales rechazan
versión histórica y tokenizer ajeno antes de abrir transporte. Las dos suites
completas pasan 19/19, sin omisiones, en 2,43 segundos con red deshabilitada.
No cambia código de producción ni recursos empaquetados.

La reevaluación independiente de este delta y la CI posterior a su publicación
se registran por separado; el resultado local no sustituye la CI remota fallida.

## Lo no validado y siguientes pasos

No se ejecutan inferencias contra OpenRouter, campañas, calidad o costes reales.
El catálogo público y la metadata local de LiteLLM acreditan parámetros
declarados, no identidad física, retención real o exactitud de facturación.
No se ha desplegado ni cambiado el gateway compartido/DockerServer; no se han
emitido claves reales ni renovado credenciales. Una política diagnóstica anterior
de GLM no autoriza la nueva ruta: deberá renovarse y verificarse por su operador,
sin ampliar sus caps.

La memoria canónica e/g no está editada: sólo se entrega una propuesta separada
para revisión humana. Ratificación del equipo, pairing y reviews humanas siguen
pendientes. Las campañas/ADR históricos no se atribuyen a este runtime.

## Archivado autorizado

Tras la entrega local favorable, Paris autorizó archivar, hacer commit y push y
comprobar la CI el 21/10/2026, conservando la aprobación del mensaje de PR antes
de publicarlo. Se comprobó el cambio activo y su trazabilidad antes de moverlo;
se archivó como `2026-10-21-jup-132-default-chat-model`, promoviendo dos requisitos
nuevos y dos modificaciones. Se actualizaron únicamente los registros de cierre,
los enlaces y los requisitos promovidos; la implementación evaluada se conserva.
La CI remota y la aceptación humana se registran por separado; el archivado no
equivale a integración ni a despliegue.
