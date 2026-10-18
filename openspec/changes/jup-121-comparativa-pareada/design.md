## Decisions

1. Mantener los cinco formatos e hitos históricos y añadir un manifiesto separado.
   Una ejecución del agregador contiene dos modelos; no inventar dos runs.
2. Grupo `paired_local_provisional`, métricas propias y `judgment=null` sólo en
   `provisional_pass/provisional_fail/pending`. Los consumidores de `automatic`
   o `human` no pueden tratar estos recuentos como sus series. Medidas técnicas
   conservan `automatic`; metadatos no registrados permanecen nulos.
3. Coste USD de fases, latencia en segundos con sus exclusiones; no recalcular ni
   confundir unidades/denominadores ni convertir provisional en aceptación.
4. El modo histórico `load` conserva su contrato de regeneración total. Para un
   destino existente usar SQL acotado que borra/inserta únicamente el mismo run
   con fuente y hash completo iguales. Una colisión de prefijo provoca error PK
   y rollback. No cambia tablas/vistas/roles ni otras ejecuciones.
5. Dashboard sin nuevas dependencias, usando el datasource PostgreSQL existente.
   Mostrar provisionalidad y límites en el panel. Datos/live sólo se acreditan
   con recibo del destino efectivo; no seleccionar stacks históricos por nombre.

## Verification

Pruebas offline de adaptación, errores, nulos, SQL generado y consulta del panel;
compatibilidad de formatos previos. Prueba opt-in PostgreSQL real en contenedor
propio 1 CPU/1 GB, sin red/puertos, con sentinel inmutable, idempotencia y rollback.
Ejecución remota y visibilidad del Grafana activo pendientes de evidencia.
