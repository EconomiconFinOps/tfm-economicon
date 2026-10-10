# JUP-078 — Cierre operativo de proveedor y modelos

Verificacion: 2026-10-10. Rama `feat/JUP-078-provider-models-completion`,
base `e1c2a8f`. [Tarjeta](https://trello.com/c/M4zqDGlW).
Origen: chat `01a12747-8575-7eb3-a21b-ab23813dc2eb`, autorizacion explicita
para implementar al completo y sustituir interacciones por subagentes.

## Resultado

El snapshot autorizado de Trello `snapshot-20261010T192813Z.json` confirma
ADR-0002 aceptado (PR #71) y un unico pendiente: emitir y validar claves.
Se crea un gateway dedicado, sin modificar los otros gateways del servidor:

- Ruta: `DockerServer:/home/danteadmin/economicon-jup078-gateway`.
- Proyecto Compose: `economicon-jup078-gateway`; puerto `127.0.0.1:44000`.
- Configuracion y digests: `infra/litellm/docker-compose.yml`,
  `config.example.yaml` y `safe_logging.py`, mas reinicio `unless-stopped`.
- PostgreSQL propio en volumen persistente; ni la DB ni su puerto se publican.
- `.env`: upstream reutilizado exclusivamente dentro del servidor; master
  y password de DB nuevos. `product-keys.json`, `processor.env`, `backend.env`:
  archivos privados 0600. Los dos ultimos contienen la clave propia bajo el
  nombre de entorno interno `LITELLM_API_KEY`; el agregador JSON distingue
  `BACKEND_LITELLM_API_KEY`. No copiar el master ni el upstream a consumidores.
- No se arrancan consumidores ni se ejecuta un benchmark en este cierre.
  Para conectarlos, unir su red privada a la del gateway y usar su DNS interno,
  no el loopback del contenedor consumidor. El runbook general conserva los
  gates de uso real y de migracion vectorial.

| Servicio | Alias permitidos | USD/30 dias | Caducidad UTC |
| --- | --- | ---: | --- |
| Processor | economicon-chat, economicon-embedding | 9 | 2026-11-09 19:31:44 |
| Backend | economicon-embedding | 1 | 2026-11-09 19:31:44 |

Por clave: RPM10, TPM20000, concurrencia1. Gasto leido: cero. Recibo
[JUP-078-operational-receipt.json](JUP-078-operational-receipt.json). El reparto suma el techo aprobado;
ninguna renovacion debe permitir consumirlo otra vez en la misma ventana.
Administracion serializada, sin rotacion automatica. DeepSeek requiere
evaluacion explicita y no esta permitido en estas claves de producto.

## Verificacion actual

- 7 pruebas unitarias de emision/rollback/idempotencia/politica/expiracion/
  rechazo de rotacion y transporte: pasan en Python3.12 de DockerServer.
- 7 pruebas de configuracion del gateway: pasan.
- OpenSpec estricto: 59 elementos antes del archivo; 58 despues, todos pasan.
  Los nueve requisitos de JUP-078 se incorporan a la especificacion canonica
  sin retirar los de JUP-023. Trazabilidad e higiene tambien pasan.
- Gateway real: scopes exactos por `/v1/models`, ambas claves rechazan
  `/key/list`, archivos0600, claves ausentes de logs, limites y claves
  persisten tras recrear el gateway. Solo endpoints administrativos: cero
  llamadas a chat o embeddings.
- Pruebas Docker con upstream simulado: **26/26 controles pasan**, incluida
  emision con la herramienta real, scope, revocacion, caducidad, presupuesto
  que deniega antes del upstream, persistencia, redes internas y logs privados.
  [Recibo completo](JUP-078-product-keys-docker.json). Limpieza sin recursos
  residuales; no se llama a proveedores reales.
- Benchmark safety: 11/11 pruebas pasan; contrato de CI: 12/12 pasan.

Comandos reproducibles desde la raiz del repositorio:

```bash
python3 -m unittest discover -s tools -p test_litellm_product_keys.py -v
JUP078_DOCKER_FAKE=1 python3 tools/test_litellm_product_keys_docker.py
node --test tools/llm-gateway-config.test.mjs
corepack pnpm openspec:validate
node tools/jup-check.mjs --all
```

La instalacion offline de dependencias no encontro OpenSpec1.8.0 en la cache.
Se uso el CLI1.8.0 ya instalado en el checkout principal y YAML2.9.0 existente,
sin alterar el lockfile. Las pruebas de archivos temporales Windows fallaron
por permisos del sandbox; se ejecutaron en Linux con resultado anterior.

## Revision y limites

Pairing/implementacion: subagente `/root/pairing`; revision independiente:
`/root/review`; validacion independiente: `/root/validation`. La revision
detecto riesgo de reiniciar gasto mediante rotacion y se retiro esa operacion.
Revision final del subagente: APPROVE, confianza alta; validacion independiente
26/26. No se atribuyen estas acciones a Lucia, Paris o Victor. Sus aprobaciones
historicas del ADR se conservan. No se han publicado mensajes Discord.

No se revalida el rendimiento de los modelos ni sus precios con llamadas
pagadas. Persisten los gates de ADR-0016 y el limite mas restrictivo aplicable.
El contador de presupuesto es asincrono: no es una reserva atomica y una
llamada puede excederlo. La prueba sintetica de agotamiento no es facturacion
real. El gateway legado4100 sigue activo, fuera de esta nueva ruta operativa.

Contrato de claves contrastado con la [documentacion oficial LiteLLM](https://docs.litellm.ai/docs/proxy/virtual_keys)
el 2026-10-10 y, para la compatibilidad concreta, con el gateway fijado.
