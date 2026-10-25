# Operar la landing pública — JUP-089 y JUP-140

La decisión de Paris del23/10/2026 selecciona contenedor Docker en Compose general para vídeo/enlace de app configurados al arrancar. El procedimiento vigente es [landing-runtime.md](../landing-runtime.md): variables, red/puerto, build inicial, salud, recreación/reversión sobre la misma imagen, directorio externo de medios públicos en sólo lectura, manifiesto verificado y traspaso al operador. La composición clara/oscura y autoplay silenciado se aprobaron después de R2; no heredan sus dictámenes.

La propuesta histórica de Direct Upload/host estático de JUP-089 queda superada para este incremento: subir sólo dist no entrega configuración de ejecución. Se conserva el historial y la evidencia de ese artefacto en [continuidad](../continuidad/landing-publica.md) y [validación JUP-089](../evidence/JUP-089-validation.md). SITE_ORIGIN sigue siendo configuración de SEO durante build, no destino dinámico ni prueba de HTTPS.

La selección de Docker no autoriza despliegue público, DNS/AWS, dominio o renovación. Tras autorización específica, verificar proxy HTTPS/certificado/redirección, cabeceras equivalentes a scripts/security.mjs (incluido HSTS en el proxy público), no-store de runtime-config.js,404 real, exclusión de fuentes/secretos, permisos y reproducción del vídeo, teclado/móvil y enlaces. No redirigir silenciosamente rutas desconocidas al frontend privado. Medidas locales no son medidas de campo ni reviews humanas.

Conservar imagen/digest y manifiesto anterior antes de publicar. Para cambio de destinos o retorno a los anteriores, recrear sólo landing con --no-deps --no-build --pull never y comprobar hashes y enlaces. Una reversión de versión usa la imagen anterior autorizada; no editar archivos servidos. Para retirar recursos locales propios, comprobar proyecto y puerto antes de detenerlos. No retirar datos o recursos compartidos.


R4 añade [llms.txt y su evidencia](../evidence/JUP-140-R4.md) y una receta clara para cambiar app y preparar vídeo. SITE_ORIGIN se pasa ahora desde Compose como ARG de construcción inicial; no es el destino app ni una tercera variable pública runtime. `/runtime-config.js` y `/llms.txt` deben conservar no-store sin ETag en cualquier proxy futuro. Sin origen sigue local noindex; con origen configurado no se presupone disponibilidad o indexación pública.
