# JUP-131 — contexto de compilación Azure en el ensayo AWS

Verificado el25/10/2026, chat «Preparar despliegue en AWS»
`01a15abb-d5f3-7fd3-a622-ea9e73b0db18`.

El ensayo autorizado en la cuenta323188184300, fuente2087855c, pasó validate
pero falló al construir Azure. Backend/processor se habían construido. El
Dockerfile Azure usa rutas desde la raíz (`apps/azure-cost-api`, `docs/api`,
`fixtures/azure-cost`), mientras el runner pasaba la subcarpeta de la API como
contexto. Compose ya utiliza la raíz. Ejecución
`0c9fb3aa-5e75-492a-a187-073ece7e70ce`; build
`economicon-defensa:4333abf6-c759-4f78-afa3-715c9092cb18`.

El cambio selecciona raíz para Azure y conserva el contexto de processor y de
las otras imágenes. No cambia Dockerfiles, ApiError, dependencias, aplicación,
permisos ni arquitectura. `starlette==1.9.0` permanece.

Validación:

- Regresión inspeccionando los COPY reales de las cinco imágenes: primero falla
  en las cinco rutas Azure; después pasa. No compara un contexto literal: exige
  que los archivos/directorios que el Dockerfile usa existan en el contexto.
- `python -m unittest discover -s tools/aws_demo -p 'test_*.py' -v`:91 pruebas,
  84 correctas y7 omitidas por integraciones opt-in.
- Compilación Docker real `linux/amd64` usando archivos versionados y el
  contexto corregido:SUCCESS. Imagen de prueba
  `sha256:4b5e6019301737b8d992f482e06e46a62f4e651899a873c5a99426655de04ea1`.
- Contenedor aislado sin red: fixtureCSV y ambos JSON presentes, Starlette1.9.0,
  UID10001. Contenedor/volumen anónimo y etiqueta temporal retirados.

El primer intento no llegó a plan/apply/release. Esta evidencia no declara la
aplicación disponible en AWS: requiere revisión/integración, CI exacta de develop,
configuración regenerada y nuevo ensayo. El bootstrap/control separado permanece.
Recibos y logs públicos locales en `.work/master-rehearsal/`;
`azure-build-context-docker-receipt.json` recoge la compilación y su limpieza.
