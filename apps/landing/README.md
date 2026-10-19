# Economicon · landing pública

[JUP-089](https://trello.com/c/fD7nJKRl) · app estática independiente. No requiere backend, sesión, Azure ni claves. Conserva la composición aprobada el 19/10/2026 y una demo de tres pasos identificada como simulación.

## Construir y probar

Node.js 22+; sin dependencias de producción. Desde la raíz:

    corepack pnpm install --frozen-lockfile
    corepack pnpm --filter @finops/landing test
    corepack pnpm --filter @finops/landing build
    corepack pnpm --filter @finops/landing preview

Sin pnpm, desde apps/landing: node scripts/build.mjs, node --test tests/build.test.mjs tests/server.test.mjs y node scripts/serve.mjs. Abre http://127.0.0.1:41790/; Ctrl+C para parar. PORT elige otro puerto local no privilegiado. dev construye antes de servir; preview verifica y carga el dist existente. Tras cambiar fuentes, reconstruye y reinicia el preview. LANDING_OUT_DIR permite construir/servir en un directorio externo dedicado cuyo nombre final sea dist; es útil para evaluaciones aisladas sin escribir en el checkout. El servidor usa la misma variable.

Sin SITE_ORIGIN: noindex, robots Disallow:/ y sitemap sin URLs públicas. Con un origen HTTPS raíz aprobado, el build genera canonical, OG absoluta, robots y sitemap coherentes; _headers prepara las cabeceras para el host estático. Credenciales, ruta, puerto, query y fragmento se rechazan. Configurar un origen no acredita dominio registrado ni HTTPS real.

## Entrada del workspace

Desde la raíz también se admite corepack pnpm build --filter=@finops/landing y corepack pnpm dev --filter=@finops/landing. La configuración Turbo de esta app declara SITE_ORIGIN y LANDING_OUT_DIR en build/dev y PORT en dev: el modo estricto conserva estos parámetros. Cada valor afecta a la huella de la tarea. Build desactiva la caché sólo para landing: una salida externa dinámica no puede restaurarse mediante outputs relativos al workspace. El artefacto es pequeño y siempre se reconstruye en el destino solicitado. La configuración de otros paquetes no cambia.

Después de instalar el workspace, node --test tools/landing-turbo.test.mjs desde la raíz verifica las entradas efectivas y hashes de Turbo sin ejecutar tareas ni escribir sus logs en el checkout. CI comprueba además la compilación real desde el consumidor raíz con un origen HTTPS sintético y salida en runner.temp; no es un despliegue.

## Frontera pública

Sólo dist: HTML/CSS/JS, PNG originales, fuentes/licencias, robots/sitemap, _headers y manifiesto SHA256. El build usa una lista cerrada: excluye archivos de entorno, scripts, pruebas, documentación, node_modules y el resto del repositorio. No sirvas la raíz del repositorio. El servidor local sólo acepta GET/HEAD, no lista carpetas, oculta configuración/manifiesto, verifica hashes y da HTTP404 real.

## Comprobación

Pruebas focales: origen/SEO, frontera de archivos, último build válido, symlinks, rutas/métodos/MIME, cabeceras y alteración de artefactos. Navegador: 1440/390/320, menú/enlaces, tabs con flechas/Home/End, demo/cierre/Escape/foco y movimiento reducido. No prueban Azure ni la aplicación privada.

[Operación y reversión](../../docs/operations/public-landing.md) · [Licencias](ATTRIBUTIONS.md) · [Evidencia y pendientes](../../docs/evidence/JUP-089-validation.md).
