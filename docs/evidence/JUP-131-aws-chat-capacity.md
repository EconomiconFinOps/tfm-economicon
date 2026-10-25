# JUP-131: capacidad de chat en la receta de AWS

Verificado el 25/10/2026. Base `92e792cec74e62f9fe1ae5b609a76fa482757a74`.
Trello: https://trello.com/c/NtiH8R4Z.
OpenSpec: `openspec/changes/jup-131-aws-cicd-defensa/`.

## Problema y cambio

En ensayo2, backend y processor terminaron con exit 1 y
`StartupError: Chat capacity configuration is invalid.` La receta especificaba
CHAT_MAX_ACTIVE=2, mientras el código integrado admite 5–8. La infraestructura y
las seis tareas de bootstrap habían terminado correctamente; esto no acreditaba
el arranque de las aplicaciones ni la aceptación del despliegue.

La receta usa 5 en ambos componentes. `validate_recipe` comprueba el rango y que
ambos coincidan cuando tienen chat habilitado, respetando el valor predeterminado 8
y el tratamiento de espacios del runtime. La validación se ejecuta en prepare
y runner antes de AWS. No cambia la cantidad de tareas ECS, CPU, memoria, IAM,
modelos ni el código de las aplicaciones. ApiError y starlette==1.9.0 se conservan.

## Verificación

- Regresión nueva antes del cambio: 6 métodos, 20 fallos esperados. Detectó el 2
  de la receta y la ausencia de validación preventiva.
- Después del cambio: 6 métodos nuevos PASS. La prueba extrae y ejecuta la función
  pura `configured_capacity` del código real de processor, sin importar ASGI ni
  construir clientes. Comprueba la receta versionada, valores 5–8, espacios,
  omisión del valor, discrepancia entre componentes y chat deshabilitado.
- `test_release_readiness` verifica que una receta con capacidad 2 bloquea
  prepare y runner y no permite llamadas AWS.
- `python -m unittest discover -s tools/aws_demo -p 'test_*.py'`:
  112 pruebas, 103 correctas, 9 omitidas; Python 3.14. Las pruebas de archivos
  temporales requirieron ejecución fuera del sandbox por sus ACL de Windows.
- Las pruebas no ejecutan AWS ni inferencia. La aceptación histórica de aplicación
  se conserva y no se renueva a partir de estas pruebas del controlador.

## Evidencia operativa y límites

Cuenta del máster 323188184300, región eu-west-1. Release
`economicon-defensa:fcf9baed-e629-422e-bb87-1a29f19917d0` detenido el 25Oct
a las 18:01:32 UTC. Resumen sin secretos en
`.work/master-rehearsal/ensayo2/runtime-failure-public-details.json` y
`bootstrap-public-summary.json`. La continuidad conserva tiempos y retirada en
`docs/continuidad/cloud-aws.md`.

Este cambio corrige el fallo de configuración observado. No demuestra todavía
el arranque real completo, la salud AMQP, el frontend o la aceptación pública;
requieren otro ensayo tras integrar la corrección. No incorpora una excepción
de revisiones humanas ni autoriza un bypass nuevo.

OpenSpec estricto y trazabilidad JUP conformes. El digest de aplicación
`3c2a471c9cb35ddafaa8d9a956361f18da5dda53a6e4cb58a1223a15ee997479`
coincide con el aceptado; `validate_recipe_files` confirma la integridad de sus
evidencias sin renovarlas. `git diff --check` no presenta errores.
