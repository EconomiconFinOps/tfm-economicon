# Operar la landing pública — JUP-089

[Tarjeta](https://trello.com/c/fD7nJKRl). apps/landing es independiente del frontend autenticado. No modifica sus rutas ni autoriza publicar el backend.

## Decisiones antes de publicar

El 19/10/2026 se aprobó el diseño y su implementación local. Dominio, titular/responsable de renovación, alojamiento, DNS/HTTPS público y destino real de demo están pendientes de decisión humana. La demo ilustrativa sigue rotulada. Esta entrega no compra, registra cuentas, configura DNS ni despliega; localhost no cierra la JUP.

Alternativa concreta propuesta, pendiente de aprobación: Direct Upload de un proyecto Cloudflare Pages del equipo, si existe acceso autorizado. Soporta el artefacto estático, _headers, 404.html y HTTPS. Si no existe proyecto/acceso autorizado, solicitar la decisión al liderazgo antes de crearlo. No sustituir automáticamente por la aplicación privada, un fallback SPA o un host que ignore las cabeceras. [Direct Upload](https://developers.cloudflare.com/pages/get-started/direct-upload/) y [cabeceras](https://developers.cloudflare.com/pages/configuration/headers/). Esta propuesta no selecciona proveedor ni autoriza gasto. Direct Upload puede automatizar subidas, pero ese mismo proyecto no puede convertirse a Git integration; esta última modalidad exige otro proyecto.

## Preparar y publicar tras autorización

1. Usar Node22+ y la revisión autorizada. Instalar corepack pnpm install --frozen-lockfile y ejecutar las pruebas de apps/landing/README.md.
2. Establecer SITE_ORIGIN con el origen HTTPS raíz aprobado y construir corepack pnpm --filter @finops/landing build. También se admite el consumidor raíz corepack pnpm build --filter=@finops/landing: su configuración transmite SITE_ORIGIN y LANDING_OUT_DIR en modo estricto y reconstruye siempre sin caché de artefactos. LANDING_OUT_DIR permite un destino externo dedicado terminado en dist; publicar ese directorio exacto. Sin la variable el resultado es noindex para local/staging. No poner claves en SITE_ORIGIN ni construir desde fuentes privadas.
3. Conservar dist/build-manifest.json y sus hashes. Publicar únicamente dist completo, incluidos _headers y 404.html. La configuración aplica CSP restrictiva, no-referrer, nosniff, anti-frame, permisos de navegador desactivados y HSTS en el build HTTPS. HTML usa no-cache.
4. En Direct Upload autorizado, seleccionar el proyecto y subir el dist completo; configurar y verificar dominio/DNS/HTTPS según el proveedor. Registrar titular, responsable/fecha de renovación y recibo. Si el host no interpreta _headers, aplicar su equivalente antes de dar conformidad. El servidor Node de loopback es sólo preview, sin TLS ni uso de producción.

## Verificar publicación real

- Certificado HTTPS válido y HTTP→HTTPS en el dominio aprobado; sin credenciales/cookies de la app privada.
- Cabeceras equivalentes a scripts/security.mjs y HSTS; CSP connect-src none y form-action none mantienen el recorrido sin backend.
- Robots, canonical, OG y sitemap coherentes. Rutas desconocidas HTTP404, nunca portada200; .git/.env/src/scripts no se exponen ni se listan carpetas.
- Menú/tabs/diálogos/fuentes/logo, 1440/390/320, teclado/foco/movimiento reducido. Medir rendimiento/a11y/SEO en el dominio final; las medidas de loopback son sólo laboratorio.
- Registrar URL, revisión/huella, fecha, resultados y reviews/CI que existan; no inventar vídeo, demo real ni participación humana.

## Reversión

Conservar artefacto anterior y manifiesto antes de cada publicación. Ante un fallo, seleccionar la versión previa en el proyecto autorizado o volver a cargar exactamente ese dist. Verificar hashes, HTTPS, canonical,404 y navegación después. Si no hay versión previa, retirar la publicación mediante el mecanismo autorizado del host conservando evidencia; no redirigir al backend privado. DNS, borrado de proyectos y accesos requieren sus permisos específicos.

## Retirada local

Ctrl+C en la terminal propia; verificar que dejó de escuchar sólo su puerto. No detener procesos por número sin comprobar su identidad ni limpiar cachés/recursos compartidos. dist se reconstruye desde src y no contiene datos persistentes.

## Ensayo local de activación y reversión

Desde la raíz, en PowerShell, construir dos directorios propios distintos. Los
destinos deben terminar en dist y no contener otros datos:

```powershell
$env:SITE_ORIGIN = ''
$env:LANDING_OUT_DIR = Join-Path $env:TEMP 'landing-local/dist'
corepack pnpm build --filter=@finops/landing
$env:SITE_ORIGIN = 'https://economicon.example.test'
$env:LANDING_OUT_DIR = Join-Path $env:TEMP 'landing-origin/dist'
corepack pnpm build --filter=@finops/landing
$env:PORT = '49142' # Comprobar antes que esté libre.
node apps/landing/scripts/serve.mjs
```

El dominio de ejemplo no es una selección de dominio público. Comprobar la
portada, canonical, robots.txt, una ruta inexistente404 y las cabeceras. Cerrar
esa terminal con Ctrl+C; volver a seleccionar landing-local/dist y arrancar el
mismo servidor. La respuesta de portada debe recuperar su SHA256 original y
noindex. Conservar y comparar el manifiesto antes de cada arranque: el servidor
comprueba bytes y huellas y rechaza alteraciones. No editar un dist servido:
la preview carga los archivos al arrancar y requiere reinicio para cambiar.

El ensayo del21/10 recuperó exactamente la portada anterior después de activar
el artefacto con origen sintético. Ambos usan el mismo código con distinta
configuración: acredita reversión local de artefacto, no despliegue ni rollback
de una versión pública.

Decisiones conservadoras: no-cache se mantiene para todos los recursos mientras
sus nombres no incorporen hash. La URL directa /404.html sirve el documento con
200; una ruta desconocida devuelve ese contenido con404. No se confunden ambas
comprobaciones ni se añade un fallback SPA.
