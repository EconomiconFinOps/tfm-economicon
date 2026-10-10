# JUP-089 — Publicación y rollback de la landing

Fecha: 10/10/2026. [Tarjeta](https://trello.com/c/fD7nJKRl).
Entrega construible: `apps/landing/dist`, origen raíz independiente. Este documento
describe el procedimiento; no acredita despliegue público ni selecciona un dominio.

## Decisión concreta pendiente de publicación

Paris, como liderazgo propuesto en Trello, debe registrar la decisión junto al
equipo, sin que esta preparación reasigne roles:

| Decisión | Dato necesario / estado |
| --- | --- |
| Dominio | Hostname exacto y titularidad comprobada. Sin aprobación ni consulta de disponibilidad en esta entrega. |
| Renovación | Persona/cuenta responsable, plazo de renovación y coste aprobado. Pendiente. |
| Hosting estático | Cuenta/proyecto concreto con origen raíz, HTTPS, cabeceras y 404 HTTP. Pendiente. |
| DNS/HTTPS | Registro indicado por ese hosting y certificado válido para el hostname elegido. Pendiente de aplicar y verificar. |
| M4 funcional / M5 RC1 | Contrastar evidencia de integración y RC1 antes de actualizar mensajes. La landing no los da por aceptados. |
| Vídeo | Revisar audio, subtítulos, autorización editorial y URL pública; no usar rutas privadas o firmadas. Pendiente. |

El dossier menciona identidad y conceptos de producto; una dirección o dominio
allí escrito no prueba propiedad ni habilita cuentas, compras o publicación.
No se abren puertos ni se modifica DockerServer para resolver esta tarjeta.

## Construcción y promoción

1. Usar el SHA revisado de la PR, checkout limpio y Node 22. Ejecutar `npm --prefix
   apps/landing test`, `npm --prefix apps/landing run lint` y el build.
2. Para la preview, ejecutar `node apps/landing/build.mjs` sin variables públicas.
   Para la publicación, definir `PUBLIC_SITE_URL` con la raíz HTTPS **aprobada**,
   y opcionalmente `PUBLIC_VIDEO_URL` con la pieza revisada. En PowerShell:

   ```powershell
   $env:PUBLIC_SITE_URL = 'https://DOMINIO-APROBADO'
   node apps/landing/build.mjs
   ```

   `DOMINIO-APROBADO` es deliberadamente un marcador inválido: reemplazarlo con la
   decisión registrada. No ejecutar usando un dominio inventado. En shells POSIX,
   definir las mismas variables mediante `export`.
3. Guardar el `dist` completo como release inmutable asociado al SHA; generar un
   manifest SHA-256 del artefacto y conservar el release anterior fuera del
   directorio de promoción. No subir el checkout, `.env`, `materiales/` ni `src`.
4. Servir exclusivamente ese directorio mediante el hosting elegido. No configurar
   rewrite global a `index.html`; una ruta desconocida debe devolver status 404 con
   `404.html`. El sitio no admite prefijos como `/tfm-economicon/` sin adaptar sus
   rutas absolutas.
5. Aplicar las cabeceras de `dist/_headers` si el host soporta ese formato; si no,
   trasladarlas a su configuración. No dar por aplicadas las cabeceras por subir
   el archivo. La CSP bloquea scripts, conexiones, iframes y formularios; solo
   estilos, fuentes e imágenes propios. La preview Node no es hosting productivo.
6. Terminar HTTPS con certificado renovable, redirigir HTTP a HTTPS y verificar
   que ninguna ruta pública sirve archivos privados. Aplicar HSTS solo una vez
   comprobado HTTPS y su política de subdominios. Registrar respuesta HTTP,
   certificado, cabeceras, fecha, release y operador real.
7. Verificar inicio, anclas, imágenes, fuentes, CTA externo, vídeo si configurado,
   favicon, canonical/OG, robots/sitemap y ruta inexistente; repetir móvil/teclado
   y mediciones en el **dominio real**. Retirar noindex únicamente en la release
   aprobada. La medición local no predice latencia de hosting ni comportamiento de
   crawlers o reproductores externos.

El workflow `Public landing` ejecuta pruebas y build, **no publica automáticamente**
ni cambia DNS. La CI existente de aplicación se conserva.

## Rollback

1. Seleccionar el último artefacto aprobado, con SHA/manifest y configuración de
   origen compatibles; no reconstruir un commit antiguo con variables nuevas.
2. Promover el artefacto anterior mediante el mecanismo de releases del hosting;
   conservar el fallido para diagnóstico. La promoción debe ser atómica o usar la
   vista previa del proveedor, sin mezclar archivos de dos releases.
3. Si hay CDN, invalidar HTML/robots/sitemap y los assets de nombres estables.
   Verificar cabeceras, inicio, 404, canonical y media contra el manifest anterior.
4. Registrar quién ejecutó el rollback, ambos SHA y motivo en la tarjeta/evidencia.
   Si el problema afecta DNS/certificado, resolverlo en el hosting elegido; no
   redirigir a la aplicación privada como alternativa.

El borrado/reconstrucción local de `dist` está probado. La promoción/rollback del
proveedor y el HTTPS real quedan pendientes hasta disponer de esas decisiones.
