# JUP-131 — solicitudes de revisión PR146

22/10/2026. Origen: review humana `lmatsan`, CHANGES_REQUESTED, publicada
22/10 sobre41cace, leída junto con conversación e inline antes de corregir.
Usuario autoriza corregir las ocho solicitudes y verificar CI, sin desplegar.
Base del incremento: bee31eca11a3c0ffe4fda4a77e8c89b8165b30d3.

| Solicitud | Corrección y regresión |
| --- | --- |
| Plan applications sin aprobación | `check_applications_plan` admite únicamente altas/actualizaciones en las seis direcciones ECS de aplicaciones y tres políticas de modelos conocidas. Rechaza borrados/sustituciones y cambios en RDS/MQ/Cognito o direcciones ajenas. Se comprueba antes de subir y antes de aplicar. Los cambios refresh-only sin acción no provisionan infraestructura. |
| Fuente sin revisión | Requiere CI `push`/`develop`, repositorio correcto, workflow y SHA exactos, completed/success, y comparación GitHub `SHA...develop` con ancestro idéntico al SHA. CI de PR, rama de trabajo, fork o workflow_dispatch no habilita el ensayo. La revisión humana de la rama protegida sigue siendo necesaria. |
| Lease sin CAS | Cada transición comprueba atómicamente ciclo, SHA, configuración y fase esperada. `RELEASING` evita dos releases. Teardown invalida el escritor anterior y la eliminación del lease exige TEARDOWN y la misma configuración. Regresión simula teardown entre lectura y escritura. |
| Entorno heredado | Docker build/save, pnpm y unittest reciben una lista explícita de variables públicas, HOME separado y proveedores AWS desactivados/vacíos. Docker login/push usa su propio directorio de auth y el password por stdin. Los procesos de confianza Terraform/AWS conservan su acceso. Esto no es un sandbox de código arbitrario; sigue siendo obligatorio revisar la fuente. |
| Tarea lanzada con respuesta inválida | Antes de validar cantidad/failures/formato se registran las tareas devueltas del propio clúster/cuenta y se añaden a cleanup. Un ID inesperado o fallo parcial intenta stop/wait antes de retirar la definición. Un error de cleanup queda CLEANUP_FAILED. Recursos de otra cuenta/clúster nunca son objetivos de stop. |
| Secretos bajo claves públicas | Validación recursiva compartida rechaza userinfo en URL, claves AWS reconocibles, claves privadas, Bearer/Basic, JWT y parámetros sensibles. Se conserva el contrato separado de ARN de Secrets Manager. No promete detectar secretos arbitrarios sin formato reconocible. |
| Receta incompleta o mock | Exige ambientes completos de las tres apps, Bedrock/TitanV2/1024/Irlanda en backend y processor, ARN Titan exacto, perfil Nova UE admitido y LLM_PROVIDER/BEDROCK_CHAT_MODEL_ID coherentes. Falla antes de provisionar. |
| JWKS por cada kid desconocido | `BoundedJWKClient` limita a un intento HTTP cada30s por verificador, también si falla. Sin caché por kid: memoria constante frente a IDs arbitrarios. RLock serializa consultas concurrentes, TTL300s conservado y rotación descubrible tras30s. Pruebas usan transporte HTTP simulado y parser/caché reales de PyJWT, no AWS. |

Menores atendidos: campos numéricos ASCII, tipos incorrectos producen ValueError
y preparación bloqueada, `plan_kind` en binding y SHA256 exportado a la aprobación
manual. Los recibos antiguos requieren volver a planificar. La prueba Terraform
de aprobación falló antes del cambio y pasó después (mock, sin AWS).

Las pruebas nuevas reprodujeron ausencia de guardas y aceptación de entradas
inválidas; los dos casos de tareas fallaron por cero llamadas stop, luego ambos
pasaron. Comprobados12/12 casos de `test_review_fixes.py`,9/9 de tareas privadas,
34/34 Cognito y142/142 del conjunto focal backend (Cognito/runtime/documentos/
bootstrap/contrato). El resto de suites y CI del SHA publicado se registran en
PR146 y continuidad. Una ruta de test inexistente se corrigió antes de ejecutar
el conjunto; no cuenta como prueba ni defecto del producto.

Repetido en Linux/Python3.12:69 casos controlador,68PASS/1SKIP y142PASS focales
backend, con red desactivada, raízRO, uid10001 y /tmp0700 en contenedor --rm.
Imagen de producción backend reconstruida `a9fa0549a2d8`; helper de pruebas
`14d643eef047`. Terraform referencia12/control1PASS con mocks; OpenSpec89PASS,
gobernanza15PASS, local doctor/smoke80PASS y ocho rutas edge conformes.

Revisión técnica independiente del incremento: APPROVE, sin P1/P2/P3 nuevos;
12 regresiones y34 Cognito repetidos por el revisor. No sustituye Revision ni
Validacion JUP-131 humanas, ni levanta CHANGES_REQUESTED automáticamente.

Razonamiento de los tests local-doctor heredados de esta PR: PostgreSQL es ahora
un motor soportado, por eso el negativo usa MySQL; el caso de puertos ocupados
inyecta `isPortFree` para no depender de otros servicios locales. No se han
modificado nuevamente ni eliminado controles de puertos reales.

Fuentes de contrato consultadas22/10:
[GitHub compare](https://docs.github.com/en/rest/commits/commits#compare-two-commits),
[PyJWT API](https://pyjwt.readthedocs.io/en/stable/api.html#jwt.PyJWKClient).
La imagen fija PyJWT2.15.1; la API declarada es>=2.8. No se ejecutó matriz2.8+.
No se contactó con AWS, no hay inferencias, altas/bajas de recursos ni prueba de
aprobación CodePipeline real en este incremento.
