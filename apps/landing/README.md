# Economicon · landing pública

[JUP-089](https://trello.com/c/fD7nJKRl), ampliada por [JUP-140](https://trello.com/c/rXLyK4g4) · app pública independiente con assets estáticos y dos destinos de arranque. No requiere backend, sesión, Azure ni claves. Aplica la composición clara/oscura aprobada el23/10/2026, vídeo local nativo y tres perspectivas identificadas como ilustraciones; el diseño anterior conserva su historia en la evidencia.

## Construir y probar

Node.js 22+; sin dependencias de producción. Desde la raíz:

    corepack pnpm install --frozen-lockfile
    corepack pnpm --filter @finops/landing test
    corepack pnpm --filter @finops/landing build
    corepack pnpm --filter @finops/landing preview

Sin pnpm, desde apps/landing: node scripts/build.mjs, node --test tests/*.test.mjs y node scripts/serve.mjs. Abre http://127.0.0.1:41790/; Ctrl+C para parar. PORT elige otro puerto local no privilegiado. dev construye antes de servir; preview verifica y carga el dist existente. Tras cambiar fuentes, reconstruye y reinicia el preview. LANDING_OUT_DIR permite construir/servir en un directorio externo dedicado cuyo nombre final sea dist; es útil para evaluaciones aisladas sin escribir en el checkout. El servidor usa la misma variable.

Sin SITE_ORIGIN: noindex, robots Disallow:/ y sitemap sin URLs públicas. Con un origen HTTPS raíz aprobado, el build genera canonical, OG absoluta, robots y sitemap coherentes; _headers prepara las cabeceras para el host estático. Credenciales, ruta, puerto, query y fragmento se rechazan. Configurar un origen no acredita dominio registrado ni HTTPS real.

## Entrada del workspace

Desde la raíz también se admite corepack pnpm build --filter=@finops/landing y corepack pnpm dev --filter=@finops/landing. La configuración Turbo de esta app declara SITE_ORIGIN y LANDING_OUT_DIR en build/dev y PORT, LANDING_VIDEO_URL y LANDING_APP_URL en dev: el modo estricto conserva estos parámetros. Cada valor declarado afecta a la huella de su tarea; los dos destinos de arranque no afectan al build. Build desactiva la caché sólo para landing: una salida externa dinámica no puede restaurarse mediante outputs relativos al workspace. El artefacto es pequeño y siempre se reconstruye en el destino solicitado. La configuración de otros paquetes no cambia.

Después de instalar el workspace, node --test tools/landing-turbo.test.mjs desde la raíz verifica las entradas efectivas y hashes de Turbo sin ejecutar tareas ni escribir sus logs en el checkout. CI comprueba además la compilación real desde el consumidor raíz con un origen HTTPS sintético y salida en runner.temp; no es un despliegue.

## Docker y destinos públicos

El Compose general incluye landing sin perfil, puerto loopback8088→8080, healthz local y red landing-public propia. LANDING_VIDEO_URL/LANDING_APP_URL se leen al arrancar y se entregan con no-store; no son secretos ni parámetros de build. Ver [operación runtime](../../docs/landing-runtime.md) para requisitos, validación, cambio/reversión A→B con la misma imagen, directorio público de medios fuera del checkout, manifiesto/SHA, límite50MiB, GET/HEAD/Range, procedimiento de traspaso y permisos de publicación. Un dist publicado solo, sin runtime-config.js, no ofrece esos destinos. La composición clara/oscura mantiene un único acceso a app en cabecera y vídeo nativo local con autoplay silenciado, controles y alternativa manual. El preview manual no monta el medio: usar Compose para ensayar el suministro real; no copiar MP4 a src, assets o al checkout.

## Frontera pública

Sólo dist: HTML/CSS/JS, PNG originales, fuentes/licencias, robots/sitemap, _headers y manifiesto SHA256. El build usa una lista cerrada: excluye archivos de entorno, scripts, pruebas, documentación, node_modules y el resto del repositorio. No sirvas la raíz del repositorio. El servidor local sólo acepta GET/HEAD, no lista carpetas, oculta configuración/manifiesto, verifica hashes y da HTTP404 real.

## Comprobación

Pruebas focales: origen/SEO, frontera de archivos, último build válido, symlinks, rutas/métodos/MIME, cabeceras y alteración de artefactos. Navegador: 1440/390/320, menú/enlaces, tabs con flechas/Home/End, demo/cierre/Escape/foco y movimiento reducido. No prueban Azure ni la aplicación privada.

[Operación y reversión](../../docs/operations/public-landing.md) · [Licencias](ATTRIBUTIONS.md) · [Resultado R3 y capturas JUP-140](../../docs/evidence/JUP-140-R3.md) · [Historial JUP-089](../../docs/evidence/JUP-089-validation.md).


## Operación y descripción pública

`LANDING_APP_URL` cambia el único enlace de cabecera y el destino app de `/llms.txt`; `LANDING_VIDEO_URL` selecciona el vídeo. Ambos son snapshots de arranque: editar el entorno y recrear sólo landing con la misma imagen, no reiniciar ni reconstruir. [Recetas de cambio app, reproducción y recuperación](../../docs/landing-runtime.md).

`src/llms.txt` es una entrada explícita verificada del build. El servidor genera GET/HEAD UTF-8 no-store con la app validada, sin variables adicionales ni URL operativa compilada; metadata rel=describedby permite descubrirlo sin cambios visuales. `SITE_ORIGIN` existe sólo en construcción inicial, pasado por Compose al Dockerfile: vacío conserva noindex, origen HTTPS selecciona canonical/sitemap de landing. No garantiza publicación/indexación o acceso a app. [Evidencia R4](../../docs/evidence/JUP-140-R4.md).
