# Configurar y operar la landing — JUP-140

La landing usa Compose general, un build estático verificado y exactamente dos destinos públicos de arranque. [Resultado R4 y evidencia HTTP](evidence/JUP-140-R4.md) · [Resultado visual R3 aprobado](evidence/JUP-140-R3.md) · [Historial](evidence/JUP-140-validation.md).

## Qué se configura y cuándo

| Variable existente | Cuándo se aplica | Efecto |
| --- | --- | --- |
| `LANDING_APP_URL` | Al crear/recrear el contenedor | Enlace HTTPS de **Abrir aplicación**, sólo en cabecera, y enlace coherente en `/llms.txt`. No concede acceso al destino. |
| `LANDING_VIDEO_URL` | Al crear/recrear el contenedor | `/media/presentation.mp4` selecciona el vídeo local. HTTPS validado sólo ofrece un enlace secundario, sin cargar un visor externo automáticamente. |
| `SITE_ORIGIN` | Construcción inicial de la imagen | Origen HTTPS de la **landing** para canonical, sitemap y modo público. Compose lo pasa al ARG existente del Dockerfile. No es un tercer destino runtime. Vacío conserva noindex/robots Disallow. |
| `LANDING_HOST_PORT` | Compose | Puerto loopback existente; por defecto 127.0.0.1:8088, contenedor 8080. |

Las URLs runtime deben ser públicas y no contener tokens ni firmas. Se rechazan esquemas ejecutables, credenciales, IP/host local, puertos no estándar, controles y consultas con claves de secretos. Sólo el vídeo admite la forma relativa cerrada `/media/<nombre seguro>.mp4`, sin query, fragmento, traversal o separadores codificados. Un destino ausente/inválido no deshabilita el otro.

El origen de landing confirmado es distinto de la app. En el `.env` **privado existente** del operador, los valores de este corte son:

```dotenv
# Construcción inicial; vacío mantiene el modo local no indexable.
SITE_ORIGIN=https://landing-demo-jupiter.danteinferno.es/
# Destinos públicos al arrancar; no necesitan rebuild para cambiarlos.
LANDING_APP_URL=https://demo-jupiter.danteinferno.es/
LANDING_VIDEO_URL=/media/presentation.mp4
```

No copiar el `.env` a la carpeta pública. El operador conserva los otros requisitos privados del [Compose general](../README.md#con-docker-compose). Configurar estos valores no modifica DNS, TLS, Cloudflare, permisos o servicios remotos.

## Cambiar sólo la dirección de la aplicación

1. Conservar los dos destinos anteriores y el ID de imagen para recuperación.
2. Editar únicamente `LANDING_APP_URL` en el `.env` privado con la nueva URL HTTPS pública real. No cambiar `SITE_ORIGIN` ni reconstruir.
3. Ejecutar la misma recreación de landing con imagen fija indicada abajo: `--no-deps --force-recreate --no-build --pull never landing`.
4. Recargar. Comparar el href de **Abrir aplicación**, `/runtime-config.js` y el enlace de `/llms.txt`: deben coincidir con el nuevo valor. La imagen, el manifiesto estático y sus archivos compilados no cambian. `/llms.txt` es una respuesta generada, por lo que su enlace sí cambia con la configuración.

`restart landing` conserva el entorno anterior y no sustituye esta recreación. El servidor no consulta ni navega al destino; el acceso puede requerir autorización propia.

## Preparar el vídeo para que reproduzca dentro de la página

La carpeta pública está **fuera del checkout**: `../landing-public-media/`, hermana del directorio que contiene docker-compose.yml. Compose GENERAL la monta como `../landing-public-media:/landing/public-media:ro`. Debe contener sólo los medios aprobados y su manifiesto; nunca montar repositorio, Drive, secretos, credenciales o socket Docker.

Para este corte se entregan exactamente `presentation.mp4` y `manifest.json`. El MP4 original no convertido tiene 21.094.149 bytes, vídeo H.264 High 2122×1080/yuv420p y audio AAC-LC 44,1 kHz / 2 canales; duración 18,900998 s. La compatibilidad universal, sonido audible y subtítulos no se presuponen.

```sh
printf '%s  %s\n' '7e9bdfb148cee61acb2e96837f041a5014f3f7048bf2a244a5cb20128f080292' '../landing-public-media/presentation.mp4' | sha256sum -c -
printf '%s  %s\n' '8f55e48b9a02d6a0d3c80d35ddde4263605bce46f4139bd7b8cb5991cb328c1f' '../landing-public-media/manifest.json' | sha256sum -c -
wc -c < ../landing-public-media/presentation.mp4
```

Esperar ambas huellas correctas y 21094149 bytes. En un host POSIX, directorio 0755 / archivos 0644 permiten lectura por node sin abrir una carpeta privada. El manifiesto recibido UTF-8 sin BOM declara exactamente:

```json
{"version":1,"files":[{"name":"presentation.mp4","mimeType":"video/mp4","bytes":21094149,"sha256":"7e9bdfb148cee61acb2e96837f041a5014f3f7048bf2a244a5cb20128f080292"}]}
```

La ruta local seleccionada, el nombre, MIME, bytes, firma ftyp y SHA deben coincidir. Límite por medio 50 MiB, manifiesto 16 KiB y 16 entradas; se rechazan symlinks, campos/nombres inseguros, tamaños o huellas incorrectos. Sólo se lee/expone el archivo seleccionado. El servidor conserva su snapshot: readonly del bind no impide cambios desde el host, pero éstos no cambian los bytes servidos hasta recrear landing. Manifiesto, listados, medios no seleccionados y rutas privadas no se publican. El MP4 y su manifiesto no entran en Git, imagen ni dist.

Con `LANDING_VIDEO_URL=/media/presentation.mp4`, crear/recrear el contenedor con la receta siguiente. Abrir la página local y comprobar avance real de tiempo sin Play, silencio inicial y controles. El navegador puede bloquear autoplay: debe quedar una acción manual útil. Pausar y cambiar tema no reanuda voluntariamente el vídeo; el sonido requiere una acción explícita. Un error de suministro conserva app/config/salud y ofrece un aviso. Un enlace Drive/HTTPS alternativo no demuestra reproducción integrada.

## Construcción inicial y uso de una imagen existente

Esta sección separa dos operaciones. Construir código nuevo o elegir otro `SITE_ORIGIN` exige una construcción inicial autorizada; cambiar app/vídeo después reutiliza la misma imagen. El nombre real del proyecto y la imagen realmente disponible los comunica el operador; los valores entre ángulos son campos por completar, no un servidor/registro inventado.

```sh
composeProject='<proyecto Compose real>'
# Sólo en la etapa inicial de construcción de código/origen, si está autorizada:
docker compose --project-name "$composeProject" --env-file .env -f docker-compose.yml build landing
```

El compañero puede recibir una imagen ya preparada en lugar de construir. Su distribución/importación o referencia remota sigue siendo una acción pendiente; no se presenta el tag local como descargable de un registro. Seleccionar por ID comprobado:

```sh
imageRef='<imagen aprobada ya recibida en este host>'
expectedImageId='<sha256:ID real comunicado con esa imagen>'
test "$(docker image inspect --format '{{.Id}}' "$imageRef")" = "$expectedImageId" || exit 1
mkdir -p .work
printf 'services:\n  landing:\n    image: "%s"\n' "$expectedImageId" > .work/landing-image.override.yaml
docker compose --project-name "$composeProject" --env-file .env -f docker-compose.yml -f .work/landing-image.override.yaml up -d --no-deps --force-recreate --no-build --pull never landing
docker compose --project-name "$composeProject" --env-file .env -f docker-compose.yml -f .work/landing-image.override.yaml ps landing
```

El override y `.env` permanecen fuera de Git. El bind procede del Compose GENERAL versionado; no hay otro servicio ni montaje funcional suplementario. Las pruebas locales sólo añaden configuración propia de subred/imagen. El contenedor sirve el build verificado con usuario node, raíz readonly, init/no-new-privileges, red propia y salud local; no requiere backend o claves. El tmpfs aprobado de processor conserva uid/gid10001 y mode0700.

## Verificar salud, configuración, llms y vídeo

```sh
landingAddress="$(docker compose --project-name "$composeProject" --env-file .env -f docker-compose.yml -f .work/landing-image.override.yaml port landing 8080)"
curl --fail "http://$landingAddress/healthz"
curl -i "http://$landingAddress/runtime-config.js"
curl -i "http://$landingAddress/llms.txt"
curl -I "http://$landingAddress/llms.txt"
curl -I "http://$landingAddress/media/presentation.mp4"
curl -D - -H 'Range: bytes=0-31' "http://$landingAddress/media/presentation.mp4" -o /dev/null
curl -D - -H 'Range: bytes=21094149-' "http://$landingAddress/media/presentation.mp4" -o /dev/null
```

Esperar health 200; runtime y llms 200/no-store/sin ETag; llms GET/HEAD text/plain UTF-8 con longitud correcta y enlace app igual al runtime. Vídeo HEAD 200/Content-Length21094149/Accept-Rangesbytes; rango 206/32 bytes/Content-Range0-31/21094149 y fuera de archivo 416/bytes*/21094149. HEAD ignora Range; unidades desconocidas/multipart o If-Range sin validador coincidente pueden recibir respuesta completa 200. El medio usa no-store. Health no acredita vídeo, autorización, HTTPS o despliegue público: comprobar también la reproducción real.

`/llms.txt` parte de un texto factual versionado y verificado y añade únicamente el destino app validado del mismo snapshot de arranque. No publica variables extra, secretos o URL de vídeo; omite el enlace app ausente/inválido. Rechaza alias/query/rutas privadas y responde GET/HEAD, no POST. La metadata HTML incluye rel=describedby, sin cambio visual ni CSP nueva. La respuesta generada es distinta del template incluido en el manifiesto estático; ambos se conservan sin escribir dist al arrancar.

## Sustituir vídeo y recuperar, sin rebuild

Antes de sustituir, conservar medio/manifiesto/dos destinos e ID anteriores en una ubicación propia recuperable. Preparar únicamente el MP4 nuevo aprobado, comprobar MIME/códec/bytes/SHA, actualizar el manifiesto y `LANDING_VIDEO_URL` y repetir exactamente la recreación con la misma imagen. Si conserva el nombre del archivo, actualizar también bytes y SHA. Más de50MiB o conversión necesitan decisión específica; no ampliar ni convertir unilateralmente.

Para recuperar, restaurar el medio/manifiesto y ambos valores anteriores y ejecutar la misma recreación con la misma imagen. Comparar imageID/manifiesto/hashes estáticos antes/después y containerID nuevo; otros servicios no deben recrearse. No editar archivos servidos ni borrar el único original recuperable.

## Descubribilidad y límites de publicación

Sin `SITE_ORIGIN`, HTML noindex/nofollow, robots Disallow y sitemap sin URLs; llms también responde X-Robots-Tag:noindex,nofollow. Con origen HTTPS válido, la construcción genera canonical/sitemap del origen de **landing**, nunca del destino app. Que el origen esté confirmado y probado en HTTP local no demuestra que DNS/TLS/hosting existan ni que el sitio sea accesible o esté indexado. La publicación requerirá permisos, HTTPS/proxy/cabeceras y rastreo efectivos; no se modifican aquí.

`llms.txt` es una [propuesta de descripción y enlaces](https://llmstxt.org/), no garantía de descubrimiento. Google indica que [no lo utiliza para mejorar visibilidad o ranking](https://developers.google.com/search/docs/fundamentals/ai-optimization-guide) y que [la indexación y aparición no están garantizadas](https://developers.google.com/search/docs/appearance/ai-features). Se conserva contenido factual y legible, sin instrucciones engañosas ni beneficios medidos inventados.

CSP/sandbox/privacidad/Drive/Access no se amplían. Movimiento reducido interactivo permanece NOT_TESTED por dispensa humana, CSS conservado. No afirmar subtítulos/transcripción, anonimato Drive, sonido audible o acceso efectivo sin pruebas. Para retirar sólo la landing propia, verificar proyecto y usar la misma receta con `stop landing`; no limpiar recursos compartidos ni borrar el medio público persistente.
