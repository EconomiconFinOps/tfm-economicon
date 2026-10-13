JUP: JUP-108
Base de preparacion: `origin/develop` 2f9a5f530c9fe3b60007ba5060c189133e353bf6,
rama `feat/JUP-108-litellm-compose`.
Proceso del repositorio: 2026-09-30 (JUP-100).

## Contexto

El Compose raiz tiene nueve servicios y cinco volumenes. Backend y processor
apuntan por defecto a `http://litellm:4000/v1`, pero ese nombre no existe en su
red. La configuracion aislada fija LiteLLM 1.103.2 y PostgreSQL 17 por digest,
el archivo de aliases y el callback de logging seguro. No se leeran ni
versionaran claves locales. ADR-0002 rige proveedor, privacidad y presupuesto;
ADR-0017 distingue la clave de embeddings del backend. JUP-078 sigue en
revision en la tarjeta; ello no autoriza gasto ni cambios de modelos.

## Decisiones propuestas

1. Usar el perfil Compose `ai` para los dos servicios nuevos. Reutilizar la
   declaracion aislada como fuente canonica, preferentemente con `include`;
   conservar un comando propio para el proyecto aislado. El gateway estara en
   la red de aplicaciones para que `litellm` resuelva desde backend/processor;
   su PostgreSQL solo estara en una red privada del gateway. Mantener nombres
   de proyecto y volumen gestionados por Compose, sin recursos globales.
2. El Compose sin perfil conservara los nueve servicios y proveedores `mock`.
   La interpolacion del archivo incluido no podra exigir `OPENROUTER_API_KEY`,
   clave maestra ni password de PostgreSQL durante `config` o `up` sin perfil.
   Al activar `ai`, un guard de arranque exigira esos secretos antes de servir;
   la falta de uno dejara el gateway no saludable. Se comprobara este
   comportamiento con la version de Compose disponible antes de darlo por
   resuelto. No se escribiran valores por defecto utilizables.
3. Con `ai`, aplicar ademas `infra/litellm/compose.ai.yml`: backend y processor
   tendran `depends_on.litellm` saludable y obligatorio. El Compose base no
   depende del gateway. La revision reprodujo que `required: false` permite
   iniciar consumidores con el gateway no saludable; Paris autorizo corregirlo.
   El arranque real documentado usa ambos archivos y el perfil en un comando.
   Para pasar de vectores mock de ocho dimensiones a 1536, usar un proyecto
   nuevo con volumenes propios, conservando el anterior sin `down -v` y
   reingiriendo documentos. No modificar tablas existentes ni migrar datos.
4. Pasar `BACKEND_LITELLM_API_KEY` solo al backend y `LITELLM_API_KEY` solo al
   processor. La primera clave se limitara al alias
   `economicon-embedding`; la segunda, a los aliases necesarios del processor.
   Nunca usar la clave maestra o la upstream en consumidores. Una clave invalida
   debera rechazarse en el gateway. El estado de las claves virtuales y los
   registros de gasto residiran solo en `gateway-data`, no en pgvector ni
   CockroachDB. La administracion seguira ligada a loopback y PostgreSQL no
   publicara puerto.
   Para la primera instalacion se levantara el gateway desde el propio Compose
   raiz, se emitiran dos claves virtuales limitadas mediante su API de
   administracion local y se guardaran fuera de Git. Tras esa preparacion, el
   comando normal del perfil `ai` arrancara todos los consumidores; no habra
   que conectar un segundo proyecto. El entorno real fijara explicitamente
   `LLM_PROVIDER=litellm`, `EMBEDDING_PROVIDER=litellm` y dimension `1536`;
   el entorno simulado usara `RUNTIME_ENVIRONMENT=development|test`.
5. Conservar pins, aliases, callback y restricciones de privacidad/logging,
   healthcheck sin llamadas de modelo y reintentos existentes. Reutilizar la
   prueba aislada de JUP-023, adaptando solo su invocacion si el perfil lo
   requiere. No se hara una llamada real a OpenRouter en la validacion local
   sin permiso de gasto separado; un upstream sintetico acredita la ruta
   tecnica, no disponibilidad/precio/privacidad efectiva del proveedor real.

## Verificacion prevista

- Red: controles focalizados que fallen al faltar el perfil o la dependencia,
  al exigir secretos en mock, al mezclar claves o al romper la persistencia.
- Green: `docker compose config --quiet` sin perfil ni secretos AI; config y
  arranque de `ai` con secretos sinteticos, red y salud; requests con cada clave
  permitida y una invalida; recreacion de gateway y base manteniendo volumen.
- Mutacion: retirar el perfil, la separacion de claves o el volumen y comprobar
  que los tests correspondientes detectan el cambio. Regresiones afectadas,
  OpenSpec, trazabilidad y controles del repositorio.
- Evidencia: revision exacta, comando, proyecto aislado, resultados, omisiones
  y limpieza dirigida solo a recursos creados por el ensayo. Sin `down -v`
  sobre el proyecto del usuario.

## Riesgos y limites

- Compose interpola variables antes de filtrar perfiles. La ausencia de
  secretos en mock se comprobara de verdad; no bastan `profiles:` por si solos.
- `include` y los overrides necesitan validacion en la version instalada
  (2.34.0). La guia requiere Compose 2.24.4 o posterior; el perfil sin el
  archivo adicional no garantiza la barrera de salud de los consumidores.
- Dos claves de hasta 10 USD cada una no equivalen al limite agregado de
  desarrollo de ADR-0002. JUP-108 no altera presupuestos ni crea caps; el uso
  pagado queda pendiente de autorizacion y control agregado.
- La restriccion inicial de acceso a Docker se resolvio mediante la ejecucion
  local autorizada. Los recibos de arranque y limpieza constan en la evidencia.

No se necesita ADR nuevo si el diseno conserva las decisiones existentes. Si
para cumplir los criterios hay que cambiar arquitectura, seguridad o
presupuesto, volver a solicitar aprobacion antes del codigo afectado.
