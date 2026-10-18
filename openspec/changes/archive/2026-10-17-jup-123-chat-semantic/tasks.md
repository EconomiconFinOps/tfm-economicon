## Estado y alcance — 17/10/2026

Las casillas distinguen ejecución técnica y medición histórica de aceptación.
La N5 de f3ec760d (140 respuestas, 825 PASS) no se atribuye al nuevo delta de PR140.
El gateway histórico fija DeepInfra FP8 y enabled=false; processor envía high/exclude
con order FP4. No se afirma razonamiento interno desactivado. Véanse
[procedencia N5](../../../../docs/evidence/JUP-123-n5-request-provenance.json) y
[correcciones y límites](../../../../docs/evidence/JUP-123-victor-corrections.md).

## 1. Base y contratos
- [x] 1.1 Recuperar B y activar JUP-123 en Trello.
- [x] 1.2 Admitir recibos repetidos y detectar ausencias/duplicados.
- [x] 1.3 Reconciliar A/develop y verificar las superficies afectadas.
  - Integración comprobada con develop 1de41b90; no incorpora las PR RAG posteriores.
- [x] 1.4 Acordar criterios obligatorios y calidad con revisores.
  - Usuario aceptó C1/C3 y sustituyó C2 por dos subagentes separados para la
    adjudicación local. No dispensa reviews oficiales, aceptación ni archivo.

## 2. Medición histórica ejecutada
- [x] 2.1 Implementar colector del API, procedencia y reserva de coste.
- [x] 2.2 Verificar entorno aislado y contabilidad para la baseline a817382b.
- [x] 2.3 Congelar y recoger baseline N3 completa (84/84, con fallos preservados).
- [x] 2.4 Resolver incertidumbres con adjudicación asistida independiente según la excepción C2.
- [x] 2.5 Recoger N3 de e23e495b: 84 recibos, 78 completed y 6 failed.
- [x] 2.6 Recoger y revisar N3 de c7e2d561: 83 completed y 1 failed; sin aceptación.
- [x] 2.7 Completar N3 de 7be57c05 y conciliación con máximos desconocidos retenidos.
  - Los fallos y juicios originales permanecen en sus recibos; no se convierten en PASS.
- [x] 2.8 Implementar comparación descriptiva entre bancos con procedencia explícita.

## 3. Correcciones y entrega
- [x] 3.1 Corregir los defectos medidos con lógica determinista.
  - Cierre histórico local f3ec760d; el delta posterior de coste de análisis se
    verifica por regresión y contrafactuales, sin heredar su aceptación semántica.
- [x] 3.2 Comparar por requisito/repetición y descartar regresiones en la campaña histórica.
  - 139 pares semánticos, 818 PASS→PASS y 1 FAIL→PASS; par técnico separado.
    Es comparación descriptiva del banco conocido, no de inferencias nuevas.
- [x] 3.3 Confirmar la N5 histórica según alcance acordado y presupuesto.
  - 140 nuevas completed, 825 PASS y C2 asistido. Cota 23.117520366/30 USD;
    reservas íntegras. No se autorizan más campañas ni cambios contables.
- [x] 3.4 Preparar candidato técnico con pruebas, evidencias y limitaciones.
  - PR140 publicada; correcciones de Víctor verificadas offline y preparadas para publicar. Cada paquete y CI
    conserva su SHA; las reviews oficiales siguen siendo requisitos independientes.

## Excepción de archivo técnico — 17/10/2026

El usuario de este chat `01a143ae-b740-7043-aedb-1a8a65b4b585` autorizó expresamente:
«Tienes autorizacion para registrar la excepcion y seguir procediendo», en respuesta
a la consulta sobre la contradicción de archivo y aceptación. Autoriza el archivo
**técnico** de los dos changes de PR140 con los pendientes expresos. No completa
las tareas de aceptación, no sustituye reviews oficiales ni autoriza merge,
activación, nueva campaña pagada, renovación de claves o cambios de reservas.

## Pendientes de aceptación

- Revisión de Víctor y revalidación de Lucía sobre el delta final.
- Disposición explícita del alcance no repetido con proveedor real/navegador y de
  los deltas de integración posteriores. No lo acredita el replay offline.
- El archivo técnico se realiza por la excepción anterior; no acredita estos
  pendientes ni aceptación del código o las mediciones.
- Merge, Trello y activación siguen separados y no están autorizados por estas casillas.

## Evidencia histórica conservada

[Informe local](../../../../docs/validation/JUP-123-local-review.md) y
[continuidad](../../../../docs/continuidad/chat-evaluacion-local.md) mantienen los
SHA, recibos, fallos de infraestructura y cortes anteriores. Se elimina de esta
lista la repetición de estados antiguos contradictorios; no se altera su evidencia.
