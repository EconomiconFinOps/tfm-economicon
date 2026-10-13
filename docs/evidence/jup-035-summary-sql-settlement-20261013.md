# JUP-035: finalizacion de la prueba SQL del resumen

Base: `b89509d0d5327634f7bea587dd746a93ae063a0d`, rama local
`codex/JUP-035-checkpoint-handoff`. Correccion local del 13/10/2026.
No cambia el producto, los plazos del resumen ni su protocolo.

## Causa y correccion

El POST puede devolver 504 al vencer su plazo y la cancelacion puede devolver
202 mientras `run_job` termina la limpieza. Una conexion fisica cerrada no
implica que haya retornado la tarea que cierra el propietario SQL, espera su
hilo de vigilancia y publica `settled=true`. La prueba esperaba la tarea HTTP
y, en el caso que fallo, `asyncio.sleep(0)`; ninguna espera garantiza ese retorno.

Se reprodujo la misma asercion fallida al retrasar 150 ms el retorno del cierre
SQL real, despues de cerrar sus recursos. La consulta termino por SQLSTATE
57014, la conexion estaba cerrada y el HTTP habia vuelto, pero `settled` era
todavia falso. El fallo historico de 5/6 y el ensayo instrumentado favorable se
conservan; este nuevo ensayo controla el orden que el anterior no garantizaba.

La suite espera ahora `job.task` mediante `wait_for(shield(...), 1.5)` antes de
comprobar finalizacion. El limite es de observacion en la prueba, no aumenta el
deadline del producto. Un bloqueo o excepcion de la tarea hace fallar la prueba;
el timeout de observacion no cancela al propietario. Se conservan las aserciones
de cancelacion nativa, cierre fisico, ausencia de llamadas al proveedor y
supervivencia de la conexion principal.

Se incorpora la correccion de portabilidad preparada durante la revision:
base configurable por `JUP035_COCKROACH_TEST_URL`, tabla minima si no existe,
conversacion sintetica propia y borrado limitado a su identidad. No consulta
conversaciones historicas. Debe usarse una base desechable y vacia; esta fixture
no prueba migraciones ni pretende poblar el esquema completo de produccion.

Un nuevo caso retiene la finalizacion del cierre mediante un evento: verifica
HTTP 504 y estado publico `settled=false`, libera la tarea y comprueba
`settled=true`, estado fallido y ausencia de salida. Usa proveedor controlado,
sin llamadas a modelos reales.

## Resultados

| Comprobacion | Resultado |
| --- | --- |
| Prueba anterior con fixture portable y cierre retrasado | 1 fallo esperado en `settled` |
| Misma reproduccion con espera corregida | 1 superada |
| Suite completa, CockroachDB v24.1.11 real | 8 superadas, 0 fallos, 0 omitidas; 18,98 s |
| Mutacion: retirar la espera del propietario | 1 fallo esperado, detectado por el nuevo caso |
| Caso nuevo tras exigir tambien estado fallido y ausencia de salida | 1 superada; 4,53 s |

Son seis casos SQL nativos, el caso existente de preparacion expirada y el
nuevo caso de finalizacion. Los resultados solapados no son casos adicionales.
El ultimo cambio fue una asercion adicional en el nuevo caso; se repitio ese
caso. No se repitieron las suites generales, los 12 controles funcionales ni
las 28 preguntas. No se ha realizado gasto en LLM ni validacion humana final.

## Reproduccion

Con las dependencias de processor instaladas, una base CockroachDB desechable
v24.1.11 y el tokenizer aprobado montado en lectura, configurar:

```text
JUP035_COCKROACH_TEST_URL=cockroachdb+psycopg://root@127.0.0.1:26257/<base_desechable>?sslmode=disable
JUP035_REQUIRE_NATIVE_SQL=true
JUP035_APPROVED_TOKENIZER=/approved/tokenizer.json
```

Desde `apps/processor`:

```sh
python -B -m pytest -p no:cacheprovider --basetemp=/tmp/jup035-sql tests/test_chat_summary_sql_deadline_jup035.py -q --tb=short
```

Tokenizer SHA256:
`19e773648cb4e65de8660ea6365e10acca112d42a854923df93db4a6f333a82d`.
Imagen de dependencias usada:
`sha256:649e9139e2590f8618eb32a33b80489e518901d4199e4d2bfc07c48a4ae1e4ee`.
Imagen SQL:
`sha256:89bda255c52b25f463c7a9373ffedef122a4d9f1b432aa34b897970fe864a66c`.
El codigo se monto desde el checkout en lectura; no se uso el codigo incluido
en la imagen como candidato. SQL en memoria, sin puertos publicados ni red
externa; los otros stacks permanecieron intactos.

Los recibos de esta sesion se conservan fuera de Git en
`jup035-sql-settlement-20261013`: `red-delayed`, `green-delayed`,
`green-native-suite`, `mutation-missing-wait` y `green-final-regression`, cada
uno con stdout, stderr y recibo con comando, tiempo y hash. Son evidencias
historicas locales; la reproduccion ordinaria solo necesita este repositorio,
sus dependencias, el tokenizer y una base desechable.
