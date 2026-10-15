# JUP-035: correccion local del envelope nativo

## Hechos y causalidad

Operacion real fallida: 9fbcc540-7194-4128-beab-13bae203cec9, intento
c6a4dd0d-7f1c-4815-8518-f65f68488601. Diagnostico retenido: envelope,
ValueError, finish_reason null, invalid_response. No hay campo offending
retenido: no permite afirmar que null o repeticion fueran su causa real.
Fuente externa preservada: corrections-runtime/validador-diagnostics-0818.json
y validador-requiredtool-dbdeadline-20261012-FAIL.md del expediente local.

Reproduccion controlada demuestra dos defectos distintos: campos null presentes
eran rechazados, y repetir id/type identicos los concatenaba. La correccion
no inventa valores ausentes ni deduplica fragmentos de nombre/argumentos.
Las contradicciones y tipos incorrectos siguen rechazados. La validacion final
de query/nombre/id y todos los limites se conserva sin cambios.

## Comprobaciones

Expediente externo corrections/requiredtool-envelope-20261012-*:
- design-spec: OpenSpec estricto; guard solo especificacion.
- red-native: 10 FAIL esperados, 1 PASS; guard solo test existente gateway.
- green-native: 11 PASS.
- green-affected: 16 FAIL/43 PASS por rule_code null anadido a diagnosticos
  previos; fallo preservado. Se corrigio el producto, no las expectativas:
  rule_code aparece exclusivamente en errores nativos.
- green-diagnostics: 32 PASS; guard solo gateway.
- final-affected: 59 PASS en suites gateway y resources existentes.
- mutation-native: cuatro mutaciones en memoria detectadas con exit 1 por
  aserciones: rechazar null, concatenar metadatos, ignorar conflicto y omitir
  validacion final. Guard posterior sin cambios de producto.

No sumar repeticiones como pruebas unicas. No se modifican prompt/manifiesto,
schema publico/privado, proveedor, modelo, deadlines, caps ni politica financiera.
No red/modelo/admin/build/Git/publicacion. Los doubles no acreditan aceptacion
real, recuperacion del corpus, citas sustentantes o persistencia.

## Siguiente control

Revision independiente del parser; parent reconstruye solo backend/processor
con el helper ya existente y ejecuta una operacion focal con requiredtool_focal.py.
Si vuelve a fallar una validacion nativa, rule_code distingue indice, cantidad,
tipo, contradiccion, estructura, fragmento, limite o llamada final invalida sin
conservar argumentos, prompts, respuestas ni texto arbitrario de excepcion.
No se declara completada la integracion ni full28 actual. Presupuesto comunicado:
baseline .338851568, gasto .262898470, limite .29, reserva conjunta .025.
