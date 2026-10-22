# JUP-131 — adaptadores Bedrock nativos

Verificación local del 22/10/2026, PR146. El candidato incorpora develop4567e8e7
sobre el punto de control ee934326; el hash de aplicación de la receta identifica
los bytes definitivos. No se han invocado modelos ni APIs de la cuenta AWS.

Backend y processor usan el SDK con credenciales del rol, firma v4, región España
explícita, endpoint overrides/proxies desactivados y límites de tiempo/reintento.
Titan V2 solicita dimensión1024 nativa y normalización, exige vectores finitos/no
nulos con tamaño exacto y guarda identidad de región/modelo/dimensión/receta.
La cache verificada admite dimensiones nativas sin alterar los vectores legacy.
Se conservan el aislamiento de tenant y las comprobaciones de fingerprints.

Chat/resumen usan el perfil explícito `eu.amazon.nova-micro-v1:0`; la variante
Lite también está permitida como elección explícita, nunca fallback. IAM acota
InvokeModel/InvokeModelWithResponseStream al perfil/cuenta y sus cinco destinos
UE revisados. El preflight GetInferenceProfile rechaza cambios de destinos o
identidad antes de crear infraestructura; todavía no se ha ejecutado en AWS.
Fuentes primarias: [perfil Micro desde España](https://docs.aws.amazon.com/bedrock/latest/userguide/model-card-amazon-nova-micro.html)
y [elección de herramienta](https://docs.aws.amazon.com/nova/latest/userguide/tool-choice.html).

Converse y ConverseStream fuerzan una herramienta de salida. Una envoltura
conserva íntegro el schema original y sus referencias locales, ajustando la raíz
a las [restricciones Nova](https://docs.aws.amazon.com/nova/latest/userguide/tools-troubleshooting.html).
El lector retira la envoltura incrementalmente sin truncar/modificar el JSON y
rechaza campos añadidos, duplicados o salida incompleta. Cada resultado conserva
los guardrails de la aplicación. La revisión privada mantiene dos fases y límites
1000/2200; el borrador no se publica. Cancelación, límites y errores seguros se
mantienen. No se reporta un precio, proveedor resuelto ni cache hit inventados;
los contadores de ambas fases se reportan solo si todos se conocen/coinciden.

Comprobado: 57 PASS sobre protocolo, schema, wiring, resumen y revisión privada
antes de integrar develop. Tras integrar recursos v4 y corregir la prueba propia
que intentaba generar con un contrato histórico, **66 PASS** con esos casos,
compatibilidad del modelo por defecto JUP-132 y tamaños de resumen. Las tres
imágenes Linux se construyen; la comprobación no root/raízRO/volumen ordinario
pasa en las tres. Backend carga chat/resumen v4 y processor dispone del tokenizer
de embeddings sin red. No se ha modificado el modelo por defecto de desarrollo.

La regresión completa Linux y la CI del SHA final se registrarán en la entrega
final. Los controles con SDK simulado prueban el código/protocolo, no permisos,
cuotas, salida de un modelo real o aceptación de la cuenta. El ensayo autorizado
debe completar el preflight y el checker funcional antes de declarar READY.
Ver [fixtures y checks](JUP-131-aws-fixtures-checks.md) y
[runtime privado](JUP-131-aws-runtime.md).

Regresión Linux integrada: backend2714PASS/369SKIP; processor2666PASS/150SKIP
más cinco fallos por esperado001..004, corregido a001..005 y siete casos focales
PASS. No cambió el runtime por esa corrección. CI definitiva pendiente en este
corte; no se reutiliza el run previo para acreditar los bytes actuales.

## Adaptación regional vigente — 22/10/2026

El usuario autoriza Irlanda (eu-west-1), conservando París para control y Virginia
para edge, sin despliegue. Sustituye el contrato regional español de los hitos
anteriores; sus resultados conservan su fecha/alcance histórico.

Runtime, endpoints, tareas privadas, CA TLS y validadores usan Irlanda. Bundle
público RDS irlandés con SHA256
a11cf9a1d0aadd7db86f92cbaa496466daeb501bf1c5e429d8ce8914a01c15d6,
idéntico en ambas apps; tres raíces irlandesas y rechazo de alteraciones probados.
El fingerprint de embeddings incluye región y no reutiliza la identidad española.
Nova UE exige exactamente cuatro destinos; IAM y contrato offline coinciden con
GetInferenceProfile consultado en Irlanda. Solo metadatos, no inferencia real.

Pruebas regionales nuevas: backend135PASS/1SKIP y processor61PASS/6SKIP tanto
Windows como Linux sin red. Omitidas incluyen SQL/servicios que requieren opt-in;
no se presentan como ejecuciones reales en esta adaptación. CI PostgreSQL del
nuevo SHA repetirá esos contratos. Referencia Terraform12PASS y control1PASS mock.
Dos imágenes de producción reconstruidas y comprobadas sin red, raízRO,
uid10001 y volumen ordinario /tmp0700: backend fab7b1a4ebd8 y processor54ddb1f177f5.
CA/Bedrock/tokenizer de processor comprobados en esas imágenes, no solo en sources.

Fargate6vCPU Irlanda/CodeBuild Medium1 París solicitados, no suponer aprobación.
Preflight exige cuotas efectivas6/1 antes de plan/lease/alta demo; IAM solo lee
los dos ARNs de cuota y no puede pedir aumentos. Cuenta/DNS/roles/secretos,
ventana/presupuesto60EUR y reviews humanas conservan sus gates externos.
CI del SHA definitivo y revisión incremental se registrarán en PR146/continuidad.
Logs ignorados .work/aws-region-irlanda/. Ver plan aws-ireland-transition.md.
