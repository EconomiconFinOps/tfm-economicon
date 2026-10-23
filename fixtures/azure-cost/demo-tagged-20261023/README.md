# Dataset Azure con etiquetas de la demo — 23/10/2026

[azure-cost-tagged.csv](azure-cost-tagged.csv) contiene los **1.370 registros de
coste normalizados** que usaba DockerDevelop al exportar el 23/10/2026 a las
16:49:57 UTC. Publicación solicitada por el usuario como complemento de JUP-133
en el [PR #156](https://github.com/EconomiconFinOps/tfm-economicon/pull/156).

Son **1.331 registros sintéticos y 39 derivados de muestras públicas** de
Microsoft FinOps Toolkit v14, con fechas desplazadas 822 días. No representan
facturas ni inventario de un cliente real. La ventana completa es del 1 de julio
al 30 de octubre de 2026; la pantalla puede mostrar un subconjunto por sus filtros
y por la fecha de referencia.

## Contenido y procedencia

El CSV conserva tenant, suscripción de demostración, fecha, coste, moneda,
servicio, proyecto y las etiquetas `owner`, `environment`, `application` y
`cost_center` añadidas el 22/10. Las etiquetas están en columnas para facilitar
su lectura. Un campo opcional vacío significa ausente; el coste cero se conserva
explícitamente como número decimal. Importar `pretax_cost` como texto/Decimal,
sin convertirlo a coma flotante ni sumar monedas distintas.

Se conservan las carencias deliberadas: **157 registros sin propietario** y
**119 sin centro de coste**; 1.094 no tienen ninguna de esas dos omisiones.
Además, 36 registros carecen del proyecto original. El número 1.094 no equivale
a conformidad con toda la política de etiquetado.

El conjunto conserva los casos extremos de la fuente, incluido el coste
sintético de `Archive` de **9007199254740993 USD el 03/10/2026**, superior a
2^53. Es un caso de precisión numérica, no gasto real.

La fuente [demo-cost.csv](../demo/demo-cost.csv) tiene 1.381 filas antes de la
agrupación diaria por servicio, proyecto y moneda de la API simulada. La ingesta
produce 1.370 registros. Se comprobaron todas las claves e importes contra esa
fuente y todas las etiquetas contra la regla del enriquecimiento original.
Se retiene el aviso [MIT de Microsoft](../LICENSE.microsoft-finops-toolkit.txt);
la [procedencia original](../../../docs/data/azure-sample-dataset.md) y el
[manifiesto](manifest.json) identifican las fuentes, recuentos y hashes.

La extracción fue de solo lectura. Se excluyen IDs internos de registros e
ingestas, timestamps operativos y campos de cuenta/recurso; estos últimos se
comprobaron vacíos en la base. Las siete suscripciones coinciden con las públicas
o sintéticas ya versionadas. No se incluyen credenciales ni conversaciones.

## Uso y límites

Este archivo es una instantánea normalizada para compartir el dataset y
contrastar costes/etiquetas. **No es una exportación Azure sin procesar ni un
backup de base de datos** y no debe sustituir directamente la entrada del fake
API. La ruta habitual `scripts/demo_data.py apply` sigue usando la fuente sin
estas etiquetas añadidas; esta entrega no implementa otro importador.

No se recargó ninguna base, no se alteró la demo y no se hicieron llamadas al
modelo. El presupuesto, las cuotas y los accesos permanecen como estaban.
Las comprobaciones del dataset no acreditan aceptación de las campañas del chat.

Para comprobar el archivo sin servicios ni dependencias, desde esta carpeta:

```python
import csv, hashlib, json
from pathlib import Path
m = json.loads(Path("manifest.json").read_text(encoding="utf-8"))
p = Path(m["path"])
assert hashlib.sha256(p.read_bytes()).hexdigest() == m["sha256"]
with p.open(encoding="utf-8", newline="") as f:
    rows = list(csv.DictReader(f))
assert len(rows) == m["rows"] == 1370
assert sum(not r["owner"] for r in rows) == 157
assert sum(not r["cost_center"] for r in rows) == 119
```
