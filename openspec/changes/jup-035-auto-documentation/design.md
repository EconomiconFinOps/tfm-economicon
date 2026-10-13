JUP: JUP-035

## Decision vigente (13/10/2026)

Paris aprueba adaptar exclusivamente en feat/JUP-035-chat-delivery el protocolo
server-documentation-v4: una recuperacion determinada por los primeros 2048
caracteres de la pregunta canonica y una generacion final estructurada por
intento. No hay decision ni llamada nativa a herramientas del modelo. Tambien
se recupera ante saludos; recuperar no obliga a citar resultados irrelevantes.

La referencia es 193b785a786ab68b3b2839e5154e814571fa1319 de Alejandro.
El HEAD observado de PR #121, f1848e5744391d7bd472ec9c944ba08f8ad764aa,
se consulta solo como referencia; no se integra su rama completa.
Se preservan nuestras correcciones de resumen, migraciones, interfaz,
scheduler, deadlines SQL, buffers y aislamiento.

## Contrato

Ampliacion aprobada 13/10: catalogo unallocated-cost-v1 anclado al pasaje
literal versionado del corpus (formula y tres bandas completas), con SHA256
incluido en el contrato privado. Se activa solo para registros efectivos
autorizados cuyo contenido contiene ese pasaje exacto; el titulo no autoriza.
El segmento privado classification recibe rule_id y expression de raiz
percentage. El modelo no entrega color, operador ni umbral. El renderer aplica
<=5 verde, >5 y <=10 amarillo, >10 rojo antes de redondear y exige citar el
registro con el pasaje completo. Cero es indefinido sin color. El criterio
MVP aprobado admite explicaciones naturales y reiteraciones correctas:
no se rechaza una respuesta por mencionar colores o variar la redaccion.
La coherencia documental y la ausencia de datos inventados se comprueban
en la aceptacion funcional, no mediante un filtro lexical de estilo.
El servidor publica las citas propias de la regla aplicada desde sus registros
autorizados y pasajes literales. No depende de que el modelo repita esa seleccion.
Una cita proporcionada con ese ID pero metadatos o pasaje incorrectos se rechaza;
no se reemplaza para ocultar el error. Las citas ajenas conservan los validadores.
Las referencias de metrics/recommendations se restringen por enum a los IDs
autorizados; su pertenencia a evidence seleccionada sigue validandose al final.
El prompt exige esa seleccion previa, sin rutas ni IDs abreviados.
El catalogo no valida que el modelo escoja el denominador pertinente.

Para tagging, la prosa que enumera requisitos necesita el pasaje de la politica.
Sin ese pasaje se omite la enumeracion y se conserva la distincion sustentada
entre allocation y cumplimiento de tagging. No hay segunda recuperacion.

006: el intento gen-1791905760-pa83ud2SxBOPaT0IGsT2 consumio exactamente 3200
tokens de salida; diagnostico length/JSON incompleto. Se aprueba 6400 para chat,
incluido reasoning, coordinado en ambos servicios, Compose y manifiestos.
No cambian resumen, ingesta, modelo, deadline, ventana ni reintentos.

Claim firmado congelado, HMAC, intento vigente, correlacion, cancelacion y
deadline absoluto se conservan. Backend autoriza el contexto recuperado.
Ambos servicios cuentan mensajes y esquema efectivo antes de generar.
El proveedor recibe reasoning high/exclude true, sin registrar razonamiento,
con 6400 tokens totales y los plazos y reintentos existentes.

El catalogo cerrado distingue valor, unidad y origen. Solo incorpora cantidades
documentales de fragmentos efectivos autenticados. Expresiones: suma, diferencia,
cociente, porcentaje, variacion relativa y comparacion terminal. Raiz operacion;
un denominador calculado reutiliza el subarbol completo, no un literal inventado.
Limites: profundidad 4, operaciones 12, cantidades 128, precision Decimal 40,
magnitud de entrada 10^12 y resultado 10^18, representacion de seis decimales.
Cero se representa indefinido; divisas incompatibles no se agregan. Se rechazan
estructuras y unidades incompatibles sin otra inferencia reparadora.

Segmentos privados comparten renderer para streaming y final. Publicamente se
conserva FinOpsResponse 1.0 y una sola pareja persistida. Los ejercicios siguen
siendo hipoteticos, nunca evidencia financiera. Chat e ingesta separan prompts.
IDs de corpus y support_quote literal quedan restringidos al contexto autorizado;
backend vuelve a verificar duplicados, procedencia y citas conservadas. La
literalidad prueba origen, no pertinencia: esta exige revision semantica real.

## Diseños sustituidos y atribucion

Se conservan las evidencias historicas de auto-documentation-v2 y de la
calculadora experimental; no acreditan este diseño. Quedan sustituidas la
decision del modelo, las llamadas nativas y los planes con IDs n:/c:.
Referencias de Alejandro: 0d91d337 (fuentes), 1b7eb148 (pasajes),
41e23706 (segmentos), 85994b86 (recuperacion/expresiones),
192b6872 (raiz calculada), 193b785a (denominador compuesto).

## Aceptacion y entrega

Pruebas Red/Green, mutaciones y regresiones locales preceden imagenes finales.
Solo siete ensayos reales nuevos: 005, 006, 007, 012, 019, 021 y 022; maximo
adicional conjunto 0,12 USD. Revisar contenido, unidades, operandos, semaforo,
pertinencia de citas y persistencia; reabrir 005/006 en navegador.
Detener ante SQL inestable, falta de presupuesto o salida vacia/truncada.
No repetir las 28 ni heredar resultados previos. Sin commit, push, publicacion,
comentarios, merge ni escrituras en rama/PR de Alejandro.

## Convivencia con consulta de propiedad

Se conserva JUP-037 en /ownership con formulario y endpoint estructurados.
La ruta antigua /assistant abre el panel nuevo y el evaluador usa generaciones.
La captura no-adapter no promueve el formulario a evidencia financiera.
## Diagnostico focal autorizado tras el ensayo del 13/10

Una expresion con unidades incompatibles sigue siendo invalida. Su diagnostico
podra conservar exclusivamente operador, profundidad y clases dimensionales
de un vocabulario cerrado, nunca operandos, valores, IDs, pasajes o prosa.
No se modifica el contrato publico ni se reparan expresiones por inferencia.

Los errores SQL de admision anteriores a reservar una operacion deben producir
el error existente `storage_unavailable` (503), sin inferencia, mensajes ni
reintentos implicitos. La peticion original puede volver a presentarse cuando
se recupere el almacenamiento, conservando su identidad y unicidad.
Este manejo no corrige el reloj del host ni autoriza ampliar tolerancias.

Excepcion posterior autorizada el 13/10: margen Cockroach de un segundo solo
en la base desechable del ensayo, sin cambiar el Compose del producto, el host
ni otros stacks. Los saltos de reloj permanecen visibles en las evidencias.
El diagnostico de 005 exige aclarar unidades y conclusion en el prompt; no
convierte una comparacion formalmente valida en prueba de pertinencia semantica.
