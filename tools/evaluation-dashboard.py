"""Carga de los resultados de evaluación del asistente en la base del dashboard de Grafana (JUP-121).

Por ahora este módulo contiene once capas. La primera es la de manifiestos: lee y valida los manifiestos
que dicen qué informes alimentan el dashboard (`docs/validation/evaluation-runs.json` y los locales). La
segunda es el adaptador del informe JSON de JUP-070 (`adapt_jup070`), que normaliza ese informe al
contrato de filas planas `rows-v1` de `docs/validation/evaluation-dashboard.md`. La tercera es el
adaptador del benchmark de modelos de JUP-078 (`adapt_jup078`), que produce el mismo contrato a partir
del informe de `tools/llm-benchmark.py`. La cuarta es el adaptador de la calibración de la recuperación
de JUP-022 (`adapt_jup022`), que convierte cada punto del barrido (`top_k`, `max_distance`) en cinco
filas del mismo contrato. La quinta es el adaptador de las métricas de negocio de JUP-068
(`adapt_jup068`), que convierte el informe de `tools/business-metrics.mjs` en 23 filas de tipo B, junto con
`read_business_report`, que ejecuta ese generador de Node. La sexta es la validación común de filas
(`validate_rows`), la barrera final del contrato `rows-v1` que se aplica a la salida de todos los
adaptadores y a la entrada `rows-v1`. La séptima es el adaptador `adapt_rows_v1`, que normaliza un
documento `rows-v1` ya escrito (por ejemplo, el informe de robustez de JUP-071) y lo pasa por esa misma
validación. La octava es la clasificación de ejecuciones: `classify_run` dice por qué motivos una ejecución no
es real (plantilla, doble, sintética o sin modelo verificado), `comparability_key` calcula el hash que agrupa
las ejecuciones comparables entre sí, `unclassified_metrics` avisa de las métricas del catálogo que no están
declaradas como humanas ni como automáticas y `classify_run_row` añade las tres columnas de clasificación a una
ejecución. La novena une todo lo anterior sin base de datos: `normalize_entry` convierte una entrada del
manifiesto en `{"run", "results"}` (con `run_id`, huella del informe, clasificación y ruta), `build_dataset`
reúne los manifiestos en un conjunto de datos sin `run_id` repetidos y `main` lo expone como el subcomando `rows`.
La décima es la generación del script SQL: `sql_literal` es el único camino por el que un valor entra en el SQL
(siempre como literal escapado, nunca por interpolación directa) y `build_sql` convierte el conjunto de datos en
un script transaccional (esquema `evaluation`, sus dos vistas `config_changes` y `comparable_runs`, vaciado y
carga) que `main` expone como el subcomando `sql`. La undécima es la carga: `build_role_sql` genera, en un script
APARTE del anterior, el rol de solo lectura de Grafana con su contraseña y sus permisos mínimos, `load_command` arma
el comando de `psql` y `run_load` pasa los dos scripts a `psql` por la entrada estándar; `main` lo expone como el
subcomando `load`.
Usa solo la biblioteca estándar y no tiene efectos al importarse. `rows` y `sql` nunca abren una conexión de red ni a
la base de datos y sus resultados no llevan credenciales; solo `load` lanza `psql`, y la contraseña del rol, que lee de
la variable de entorno `GRAFANA_EVALUATION_DB_PASSWORD`, viaja únicamente por la entrada estándar de `psql` (nunca en
los argumentos ni en el entorno del proceso hijo) y se tapa con `***` en cualquier mensaje de error.

Uso por línea de comandos (el resultado sale por la salida estándar, o a `--output`; un error sale como
`error: <mensaje>` por la salida de errores con código 1 y no escribe nada): `rows` imprime el conjunto de datos
en JSON y `sql` el script SQL, con las mismas opciones; `load` carga el conjunto en la base, crea o actualiza el rol
y solo imprime un resumen de una línea. `--output` es de `rows` y `sql`; `--psql-command` es de `load`.

    python tools/evaluation-dashboard.py rows [--manifest RUTA]... [--no-versioned] [--output FICHERO] [--root DIR]
    python tools/evaluation-dashboard.py sql [--manifest RUTA]... [--no-versioned] [--output FICHERO] [--root DIR]
    GRAFANA_EVALUATION_DB_PASSWORD=... python tools/evaluation-dashboard.py load [--manifest RUTA]... [--no-versioned]
        [--root DIR] [--psql-command COMANDO]
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import os
import re
import shlex
import subprocess
import sys
import tempfile
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

MANIFEST_VERSION = 1
# El orden es parte del contrato (docs/validation/evaluation-dashboard.md): añadir o quitar un formato
# cambia lo que la herramienta acepta, por eso se declara como tupla inmutable y no como un conjunto.
FORMATS = (
    "jup-070-report-v1",
    "jup-078-benchmark-v1",
    "jup-022-calibration-v1",
    "jup-068-input-v1",
    "rows-v1",
    "jup-063-paired-v1",
)
# Regla 3 del contrato: los identificadores no pueden ser texto libre (un enunciado de pregunta, por
# ejemplo). Se admite solo un alfabeto cerrado de hasta 80 caracteres. El patrón conserva `$` porque es
# el literal del contrato, pero `$` también casa antes de un salto de línea final; por eso SIEMPRE se
# valida con `fullmatch` (ver `_is_identifier`) y así "abc\n" se rechaza sin tocar el patrón.
IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:=,/+@-]{0,79}$")

ROOT_KEYS = {"manifest_version", "runs"}
ENTRY_KEYS = {"path", "format", "milestone", "run_id", "model_identity"}


class ManifestError(ValueError):
    """Manifiesto ilegible o que incumple el contrato.

    Hereda de ValueError para que los llamadores puedan capturarla de forma genérica, y es la única
    excepción que sale de esta capa: los fallos de disco o de JSON se convierten en ella para que la
    línea de comandos muestre siempre un mensaje accionable en lugar de una traza.
    """


def _is_identifier(value: object) -> bool:
    # fullmatch y no match: con `$` en el patrón, match aceptaría un salto de línea final.
    return isinstance(value, str) and IDENTIFIER_RE.fullmatch(value) is not None


def _fail(manifest: Path, where: str, problem: str) -> ManifestError:
    # Todo error nombra el fichero del manifiesto y el campo, como exige el contrato, para que quien
    # edita un manifiesto local sepa qué corregir sin abrir el código.
    location = f"{manifest}: {where}" if where else f"{manifest}"
    return ManifestError(f"{location}: {problem}")


def _load_json(manifest: Path) -> object:
    try:
        # utf-8-sig tolera el BOM que añaden algunos editores de Windows y no altera el UTF-8 normal.
        text = manifest.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError) as error:
        raise _fail(manifest, "", f"no se puede leer el manifiesto ({error})") from error
    try:
        return json.loads(text)
    except (ValueError, RecursionError) as error:
        # JSONDecodeError es subclase de ValueError; se convierte para no filtrar su tipo al llamador.
        raise _fail(manifest, "", f"JSON inválido ({error})") from error


def _resolve_report(manifest: Path, where: str, raw: str, root: Path) -> Path:
    candidate = Path(raw)
    # Una ruta relativa se resuelve desde la raíz del repositorio (no desde el manifiesto ni desde el
    # cwd) para que el manifiesto versionado funcione igual desde cualquier directorio. resolve()
    # normaliza `..` y alias, necesario para detectar después el mismo informe citado de dos formas.
    if not candidate.is_absolute():
        candidate = root / candidate
    try:
        resolved = candidate.resolve()
        exists = resolved.is_file()
    except (OSError, ValueError) as error:
        raise _fail(manifest, f"{where}.path", f"ruta no válida {raw!r} ({error})") from error
    if not exists:
        raise _fail(manifest, f"{where}.path", f"el informe no existe: {resolved}")
    return resolved


def _check_entry(manifest: Path, index: int, item: object) -> dict:
    where = f"runs[{index}]"
    if not isinstance(item, dict):
        raise _fail(manifest, where, "cada ejecución debe ser un objeto")
    # Las claves desconocidas se rechazan para que una errata (`milstone`) no pase en silencio.
    for key in item:
        if key not in ENTRY_KEYS:
            raise _fail(manifest, where, f"clave desconocida {key!r}")
    raw_path = item.get("path")
    if not isinstance(raw_path, str) or not raw_path:
        raise _fail(manifest, f"{where}.path", "debe ser una cadena no vacía")
    fmt = item.get("format")
    if not isinstance(fmt, str) or fmt not in FORMATS:
        raise _fail(manifest, f"{where}.format", f"formato desconocido {fmt!r}; los válidos son {', '.join(FORMATS)}")
    # `type(...) is bool`: en Python 1 y 0 no son bool para el contrato JSON, y "true" tampoco.
    milestone = item.get("milestone")
    if type(milestone) is not bool:
        raise _fail(manifest, f"{where}.milestone", "debe ser un booleano true o false")
    run_id = None
    if "run_id" in item:
        run_id = item["run_id"]
        if not _is_identifier(run_id):
            raise _fail(manifest, f"{where}.run_id", f"identificador no válido {run_id!r} (alfabeto cerrado, máximo 80 caracteres)")
    model_identity = None
    if "model_identity" in item:
        model_identity = item["model_identity"]
        if not isinstance(model_identity, dict):
            raise _fail(manifest, f"{where}.model_identity", "debe ser un objeto con la identidad del modelo")
        for key in model_identity:
            if key not in IDENTITY_KEYS:
                raise _fail(manifest, f"{where}.model_identity",
                            f"clave desconocida {_key_label(str(key))!r}; las válidas son {', '.join(IDENTITY_KEYS)}")
        model_identity = dict(model_identity)
    return {"path": raw_path, "format": fmt, "milestone": milestone, "run_id": run_id,
            "model_identity": model_identity, "manifest": manifest}


def read_manifest(path, root=ROOT) -> list[dict]:
    """Lee y valida un manifiesto; devuelve sus entradas en el orden del fichero.

    Cada entrada tiene `path` (Path absoluto y normalizado), `format`, `milestone`, `run_id`
    (None si no se declara) y `manifest` (el manifiesto de origen).
    """
    manifest = Path(path)
    base = Path(root)
    data = _load_json(manifest)
    if not isinstance(data, dict):
        raise _fail(manifest, "", "la raíz debe ser un objeto")
    for key in data:
        if key not in ROOT_KEYS:
            raise _fail(manifest, "", f"clave desconocida {key!r}")
    # `type(...) is int`: bool es subclase de int y `True == 1` aceptaría un `true` por error.
    version = data.get("manifest_version")
    if type(version) is not int or version != MANIFEST_VERSION:
        raise _fail(manifest, "manifest_version", f"debe ser {MANIFEST_VERSION}")
    runs = data.get("runs")
    if not isinstance(runs, list):
        raise _fail(manifest, "runs", "debe ser una lista")
    # Dos pasadas a propósito: primero se valida la forma de TODAS las entradas y solo después se
    # comprueba que los informes existan. Así un error de esquema en `runs[1]` no queda tapado por un
    # informe ausente en `runs[0]`, y el mensaje apunta al fallo de contrato, que es el más barato de corregir.
    entries = [_check_entry(manifest, index, item) for index, item in enumerate(runs)]
    for index, entry in enumerate(entries):
        entry["path"] = _resolve_report(manifest, f"runs[{index}]", entry["path"], base)
    return entries


def merge_manifests(paths, root=ROOT) -> list[dict]:
    """Lee varios manifiestos y devuelve sus entradas concatenadas en orden.

    No reordena ni deduplica: un informe repetido o un `run_id` repetido es un error, porque
    cargarlo dos veces duplicaría filas o chocaría en la base. Si cualquier manifiesto falla se
    lanza la excepción sin devolver nada (regeneración atómica).
    """
    merged: list[dict] = []
    seen_paths: dict[Path, Path] = {}
    seen_ids: dict[str, Path] = {}
    for manifest_path in paths:
        for index, entry in enumerate(read_manifest(manifest_path, root=root)):
            manifest = entry["manifest"]
            where = f"runs[{index}]"
            report = entry["path"]
            if report in seen_paths:
                raise _fail(manifest, f"{where}.path", f"el informe {report} ya está listado en {seen_paths[report]}")
            seen_paths[report] = manifest
            run_id = entry["run_id"]
            # Los run_id None no chocan: se derivan del informe más adelante y ya son distintos por ruta.
            if run_id is not None:
                if run_id in seen_ids:
                    raise _fail(manifest, f"{where}.run_id", f"run_id {run_id!r} repetido; ya está en {seen_ids[run_id]}")
                seen_ids[run_id] = manifest
            merged.append(entry)
    return merged


# --- Adaptador del informe de JUP-070 -----------------------------------------------------------------

# Catálogo de JUP-067: fuente única de la familia (`grp`) y la unidad de cada métrica, así que el
# adaptador no lleva su propia tabla que pueda divergir de él. Se lee al adaptar, no al importar.
CATALOGUE_PATH = ROOT / "docs" / "validation" / "JUP-067-metrics-catalogue.json"

REPORT_VERSION = 1

# Claves del contrato `rows-v1`. Son tuplas, no conjuntos: el orden fija la forma de salida y lo comparten
# el validador de `rows-v1` y la carga a la base, que deben leerlas desde aquí y no repetirlas.
# Identidad del modelo que generó las respuestas (JUP-133). `generation_model` es el alias del gateway y no cambia
# cuando cambia el modelo que hay detrás; estos cuatro campos distinguen el modelo servido, quien lo sirvió, su
# cuantización y la configuración del gateway que resolvió el alias. Todos son opcionales: nulo es «no registrado».
IDENTITY_KEYS = ("generation_model_id", "generation_provider", "generation_quantization", "gateway_config_sha256")
RUN_KEYS = (
    "run_id", "source", "run_at", "commit", "suite", "suite_version", "suite_sha256", "corpus_sha256",
    "embedding_provider", "embedding_alias", "retrieval", "generation_model", "prompt_sha256", "synthetic",
) + IDENTITY_KEYS
# Huella de la configuración del gateway: sha256 hexadecimal en minúsculas (`fullmatch` rechaza un salto final).
GATEWAY_HASH_RE = re.compile(r"[0-9a-f]{64}")
RESULT_KEYS = (
    "measure_type", "grp", "metric_id", "behavior", "status", "count", "value", "unit",
    "numerator", "denominator", "ci_low", "ci_high", "judgment", "selected",
)
# `status` se parte en dos vocabularios: los estados de caso solo los usa la métrica `cases`; el resto de
# filas dice si el valor se midió o no (regla 1 del contrato: lo no medido es null, nunca cero).
CASE_STATUSES = ("pass", "fail", "blocked", "not_run")
VALUE_STATUSES = ("measured", "not_measured")

# Tabla «Juicio humano o automático» de docs/validation/evaluation-dashboard.md. `outcome` mezcla reglas
# objetivas y puntos juzgados por personas, así que lo que cuenta casos `pass`/`fail` o depende de él
# (ACC-1, ACC-3 y la fila `judged` de ACC-2) es humano; todo lo demás es automático. Se declara lo humano
# y no lo automático porque es la excepción y lo que hay que revisar a mano cuando el catálogo crezca:
# clasificar de menos como `human` falsearía la separación de las series de juicio humano.
HUMAN_CASE_STATUSES = ("pass", "fail")
HUMAN_METRICS = frozenset({"ACC-1", "ACC-3"})
HUMAN_ROWS = frozenset({("ACC-2", "judged")})

COUNT_KEYS = ("cases", "pass", "fail", "blocked", "not_run")
# Campos que el informe de JUP-070 siempre trae dentro de `run` (pueden valer null, salvo date/synthetic).
RUN_REQUIRED = (
    "commit", "date", "provider", "alias", "suite_version", "suite_sha256",
    "corpus", "generation", "retrieval", "synthetic",
)


class AdapterError(ValueError):
    """Informe ilegible o que incumple el contrato de su formato.

    Hereda de ValueError, como ManifestError, para que la carga trate ambos como errores de datos. El
    mensaje es siempre `<campo>: <problema>` y empieza por la ruta del campo dentro del informe.
    """


def _bad(where: str, problem: str) -> AdapterError:
    return AdapterError(f"{where}: {problem}")


# Máximo de caracteres de un nombre ajeno (clave de un informe) que se vuelca dentro de un mensaje.
KEY_LABEL_LIMIT = 80


def _escape_control(text: str) -> str:
    # Solo se escapa lo no imprimible (saltos de línea, ESC, NUL...): las tildes y los espacios se dejan tal cual
    # para que el mensaje siga siendo legible. `unicode_escape` carácter a carácter y no `repr()` para no añadir
    # comillas ni cambiar el mensaje de las claves normales.
    return "".join(char if char.isprintable() else char.encode("unicode_escape").decode("ascii") for char in text)


def _key_label(key: str) -> str:
    # Los mensajes citan la clave desconocida para que se pueda corregir, pero una clave es texto del informe:
    # una clave con un salto de línea partiría el error en dos líneas, una con ESC inyectaría secuencias de terminal y una de
    # medio megabyte inundaría la salida. Se escapa y se trunca (escapar primero acota el resultado final).
    label = _escape_control(key)
    return label if len(label) <= KEY_LABEL_LIMIT else label[:KEY_LABEL_LIMIT] + "..."


def _load_catalogue() -> dict:
    try:
        return json.loads(CATALOGUE_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        # Mismo criterio que los manifiestos: un fallo de disco o de JSON sale como error de contrato.
        raise _bad("catalogue", f"no se puede leer el catálogo de JUP-067 ({error})") from error


def _check_object(value: object, where: str) -> dict:
    if not isinstance(value, dict):
        raise _bad(where, "debe ser un objeto")
    return value


def _check_counts(report: dict) -> dict:
    counts = _check_object(report.get("counts"), "counts")
    for key in COUNT_KEYS:
        value = counts.get(key)
        # `type(...) is int`: bool es subclase de int y `True` sumaría 1 sin ser un recuento.
        if type(value) is not int or value < 0:
            raise _bad("counts", f"{key!r} debe ser un entero mayor o igual que 0")
    if sum(counts[key] for key in CASE_STATUSES) != counts["cases"]:
        raise _bad("counts", "pass + fail + blocked + not_run debe ser igual a cases")
    return counts


def _check_run(report: dict) -> dict:
    run = _check_object(report.get("run"), "run")
    for field in RUN_REQUIRED:
        if field not in run:
            raise _bad(f"run.{field}", "campo obligatorio ausente")
    for field, inner in (("corpus", "sha256"), ("generation", "model_alias")):
        if inner not in _check_object(run[field], f"run.{field}"):
            raise _bad(f"run.{field}.{inner}", "campo obligatorio ausente")
    _check_object(run["retrieval"], "run.retrieval")
    # Una ejecución sin fecha no se puede ordenar en las series, así que `date` no admite null. No se
    # normaliza la `Z` final: desde Python 3.11 datetime.fromisoformat la acepta y el repositorio exige 3.12+.
    date = run["date"]
    try:
        if not isinstance(date, str):
            raise ValueError("no es una cadena")
        datetime.fromisoformat(date)
    except ValueError as error:
        raise _bad("run.date", f"debe ser una fecha ISO 8601 ({error})") from error
    if type(run["synthetic"]) is not bool:
        raise _bad("run.synthetic", "debe ser un booleano true o false")
    return run


def _check_metrics(report: dict, catalogue_by_id: dict) -> dict:
    metrics = _check_object(report.get("metrics"), "metrics")
    for metric_id, data in metrics.items():
        # Una métrica fuera del catálogo es un informe de otra versión: se rechaza en lugar de inventarle
        # familia y unidad. Una métrica del catálogo que falta no es error (no se inventa lo ausente).
        if metric_id not in catalogue_by_id:
            raise _bad(f"metrics.{_key_label(metric_id)}", "métrica desconocida (no está en el catálogo de JUP-067)")
        _check_object(data, f"metrics.{_key_label(metric_id)}")
    return metrics


def _validate_report(report: object, catalogue: dict, catalogue_by_id: dict) -> tuple[dict, dict, dict]:
    if not isinstance(report, dict):
        raise _bad("report", "debe ser un objeto")
    version = report.get("report_version")
    if type(version) is not int or version != REPORT_VERSION:
        raise _bad("report_version", f"debe ser {REPORT_VERSION}")
    # El catálogo da familia y unidad; un informe de otra versión del catálogo podría significar otra cosa.
    if report.get("catalogue_version") != catalogue.get("catalogue_version"):
        raise _bad("catalogue_version", f"debe ser {catalogue.get('catalogue_version')!r}, la del catálogo")
    return _check_counts(report), _check_run(report), _check_metrics(report, catalogue_by_id)


def _adapt_run(run: dict, run_id: str) -> dict:
    # Se copia lo que el informe trae y nada se deduce: un null del informe queda null («no registrado»).
    return {
        "run_id": run_id,
        "source": "JUP-070",
        "run_at": run["date"],
        "commit": run["commit"],
        "suite": "JUP-069",
        "suite_version": run["suite_version"],
        "suite_sha256": run["suite_sha256"],
        "corpus_sha256": run["corpus"]["sha256"],
        "embedding_provider": run["provider"],
        "embedding_alias": run["alias"],
        # Copia profunda: la salida no comparte estructura con el informe, que es la fuente de verdad.
        "retrieval": copy.deepcopy(run["retrieval"]),
        "generation_model": run["generation"]["model_alias"],
        # Ningún informe de JUP-070 registra el prompt.
        "prompt_sha256": None,
        "synthetic": run["synthetic"],
        **dict.fromkeys(IDENTITY_KEYS),
    }


def _judgment(metric_id: str, behavior: str) -> str:
    if metric_id in HUMAN_METRICS or (metric_id, behavior) in HUMAN_ROWS:
        return "human"
    return "automatic"


def _row(grp: str, metric_id: str, behavior: str, unit: str, judgment: str, **fields) -> dict:
    # Toda fila nace con todas las claves a None (salvo tipo A y no seleccionada) para que la forma sea
    # idéntica en cada caso y lo no indicado quede como «no registrado», nunca como un valor inventado.
    row = dict.fromkeys(RESULT_KEYS)
    row.update(measure_type="A", selected=False, grp=grp, metric_id=metric_id, behavior=behavior,
               unit=unit, judgment=judgment)
    row.update(fields)
    return row


def _count_rows(counts: dict) -> list[dict]:
    # Los cuatro estados son filas propias y `cases` es el denominador de todas: blocked y not_run no se
    # suman a fail (regla 2 del contrato), porque «no se pudo ejecutar» no es «falló».
    return [
        _row("cases", "cases", "all", "casos", "human" if status in HUMAN_CASE_STATUSES else "automatic",
             status=status, count=counts[status], denominator=counts["cases"])
        for status in CASE_STATUSES
    ]


def _metric_row(item: dict, behavior: str, **fields) -> dict:
    return _row(item["family"], item["id"], behavior, item["unit"], _judgment(item["id"], behavior), **fields)


def _not_measured(item: dict, behavior: str, denominator) -> dict:
    # Se conserva el denominador (cuántos casos había) pero valor, numerador e intervalo quedan None.
    return _metric_row(item, behavior, status="not_measured", denominator=denominator)


def _shape_error(item: dict, path: tuple[str, ...], problem: str) -> AdapterError:
    # Todo mensaje de forma rota empieza por `metrics.<ID>: ` (campo exacto de la métrica, como exige el spec) y
    # el elemento anidado concreto va después, en el problema: `metrics.ACC-3: groups.clarify debe ser un objeto`.
    where = ".".join(path)
    return _bad(f"metrics.{item['id']}", f"{where} {problem}" if where else problem)


def _object_at(item: dict, value: object, *path: str) -> dict:
    if not isinstance(value, dict):
        raise _shape_error(item, path, "debe ser un objeto")
    return value


def _object_field(item: dict, data: dict, key: str) -> dict:
    # Comprobación explícita en lugar de un `try/except` genérico alrededor del adaptador: ese capturaría
    # también errores de programación (un KeyError nuestro) y los disfrazaría de «informe mal formado».
    if key not in data:
        raise _bad(f"metrics.{item['id']}", f"falta {key!r}")
    return _object_at(item, data[key], key)


def _is_count(value: object) -> bool:
    # `type(...) is int`: bool es subclase de int y `True` no es un recuento (mismo criterio que `counts`).
    return type(value) is int


def _proportion_row(item: dict, behavior: str, data: dict, path: tuple[str, ...] = ()) -> dict:
    # `path` es la ubicación de la proporción dentro de la métrica (vacía si la métrica es la proporción).
    _object_at(item, data, *path)
    # `available` False manda sobre `rate`: un informe incoherente no debe publicar como medido un 0.0 que
    # en realidad significa «sin datos». Con rate None tampoco hay nada que copiar.
    if data.get("available") is False or data.get("rate") is None:
        # Lo no medido no copia `k` ni `ci95`, así que su ausencia no es un error.
        return _not_measured(item, behavior, data.get("n"))
    # Una proporción medida copia `k`, `n` y `ci95`: se exige antes de construir la fila para no inventar
    # un 0 ni publicar como intervalo algo que no lo es (p. ej. una cadena de dos caracteres).
    for key in ("k", "n"):
        if key not in data:
            raise _shape_error(item, path, f"falta {key!r}")
        if not _is_count(data[key]):
            raise _shape_error(item, path, f"{key!r} debe ser un entero")
    # Un 0.0 o un k=0 con `available` True SÍ es una medición (cero fallos), y sigue siendo `measured`.
    ci = data.get("ci95")
    if ci is None:
        ci_low, ci_high = None, None
    elif isinstance(ci, list) and len(ci) == 2:
        ci_low, ci_high = ci
    else:
        raise _shape_error(item, path, "'ci95' debe ser null o una lista de exactamente 2 límites")
    return _metric_row(item, behavior, status="measured", value=data["rate"], numerator=data["k"],
                       denominator=data["n"], ci_low=ci_low, ci_high=ci_high)


def _value_row(item: dict, behavior: str, value, denominator=None, available: bool = True) -> dict:
    # Para lo que no es una proporción (cuantiles, latencias, recuentos): el valor se copia tal cual. Un 0
    # medido (0 ms de una etapa de plantilla, 0 fallos) es una medición; solo None o `available` False no.
    if not available or value is None:
        return _not_measured(item, behavior, denominator)
    return _metric_row(item, behavior, status="measured", value=value, denominator=denominator)


def _single_proportion(item: dict, data: dict) -> list[dict]:
    return [_proportion_row(item, "all", data)]


def _acc_2_rows(item: dict, data: dict) -> list[dict]:
    rows = _single_proportion(item, data)
    # `judged` es el sub-objeto con los puntos juzgados por personas; si el informe no lo trae no se inventa.
    if "judged" in data:
        rows.append(_proportion_row(item, "judged", data["judged"], ("judged",)))
    return rows


def _group_rows(item: dict, data: dict) -> list[dict]:
    groups = _object_field(item, data, "groups")
    return [_proportion_row(item, name, group, ("groups", name)) for name, group in groups.items()]


def _rel_4_rows(item: dict, data: dict) -> list[dict]:
    available = data.get("available") is not False
    return [_value_row(item, name, data.get(name), data.get("n"), available) for name in ("median", "q1", "q3")]


def _grd_2_rows(item: dict, data: dict) -> list[dict]:
    # Una fila `all` con el total y una por caso con fallos (el id de caso va en `behavior`). Con
    # `available` False solo queda la fila `all`, como no medida: si la métrica no se midió, el desglose
    # por caso del informe tampoco es un dato y no se publica ni como medido ni como no medido.
    if data.get("available") is False:
        return [_not_measured(item, "all", None)]
    rows = [_value_row(item, "all", data.get("total"))]
    by_case = _object_field(item, data, "by_case")
    rows += [_value_row(item, case, count) for case, count in by_case.items()]
    return rows


def _check_stages(item: dict, stages: dict) -> list[tuple[str, dict]]:
    # Cada etapa debe ser un objeto antes de leerle `value`/`n`; se valida toda la lista antes de construir filas.
    return [(stage, _object_at(item, entry, "stages", stage)) for stage, entry in stages.items()]


def _stage_value_rows(item: dict, data: dict) -> list[dict]:
    # LAT-1..3: la ausencia de una etapa no contamina a las demás, cada una decide su propio estado.
    stages = _object_field(item, data, "stages")
    return [_value_row(item, stage, entry.get("value"), entry.get("n"))
            for stage, entry in _check_stages(item, stages)]


def _stage_rate_rows(item: dict, data: dict) -> list[dict]:
    stages = _object_field(item, data, "stages")
    return [_proportion_row(item, stage, entry, ("stages", stage)) for stage, entry in stages.items()]


def _str_2_rows(item: dict, data: dict) -> list[dict]:
    by_category = _object_field(item, data, "by_category")
    rows = [_value_row(item, name, count) for name, count in by_category.items()]
    return rows + [_value_row(item, "all", data.get("total"))]


# Forma de cada métrica del catálogo. Se despacha por identificador y no por la forma del dict porque
# las formas se parecen pero significan cosas distintas, y así un identificador nuevo falla de forma explícita.
METRIC_ROWS = {
    "ACC-1": _single_proportion, "ACC-2": _acc_2_rows, "ACC-3": _group_rows,
    "REL-1": _single_proportion, "REL-2": _single_proportion, "REL-3": _group_rows, "REL-4": _rel_4_rows,
    "GRD-1": _single_proportion, "GRD-2": _grd_2_rows, "GRD-3": _single_proportion,
    "LAT-1": _stage_value_rows, "LAT-2": _stage_value_rows, "LAT-3": _stage_value_rows,
    "LAT-4": _stage_rate_rows,
    "STR-1": _single_proportion, "STR-2": _str_2_rows,
    "AVL-1": _single_proportion,
}


def adapt_jup070(report, run_id: str) -> tuple[dict, list[dict]]:
    """Normaliza un informe de JUP-070 (ya parseado) a `(run, results)` del contrato `rows-v1`.

    Función pura: no lee el informe, no lo muta y no comparte estructuras con él; solo lee el catálogo
    de JUP-067. Copia los valores sin recalcularlos ni redondearlos (regla 4). Las filas salen con los
    cuatro recuentos de casos primero y las métricas después, en el orden del informe.
    """
    catalogue = _load_catalogue()
    catalogue_by_id = {item["id"]: item for item in catalogue["metrics"]}
    counts, run, metrics = _validate_report(report, catalogue, catalogue_by_id)
    results = _count_rows(counts)
    for metric_id, data in metrics.items():
        results += METRIC_ROWS[metric_id](catalogue_by_id[metric_id], data)
    return _adapt_run(run, run_id), results


# --- Adaptador del benchmark de JUP-078 ---------------------------------------------------------------

BENCHMARK_SCHEMA_VERSION = 1
# Campos que cada modelo del informe debe traer. El orden fija cuál se reporta primero si faltan varios.
MODEL_REQUIRED = ("alias", "cases", "successful", "mean_keyword_score", "p95_latency_ms", "cost_usd")
# (campo del informe, metric_id de la fila, unidad, ¿el denominador es `successful`?). El coste no lleva
# denominador: es un total del modelo, no una media sobre las llamadas correctas.
BENCHMARK_MEASURES = (
    ("mean_keyword_score", "keyword_score", "puntuacion", True),
    ("p95_latency_ms", "latency_p95", "ms", True),
    ("cost_usd", "cost", "usd", False),
)


def _is_number(value: object) -> bool:
    # Solo int o float exactos: bool es subclase de int y `True` no es una medición. NaN e infinito no son
    # mediciones y se rechazan en lugar de publicarse como valores.
    if type(value) not in (int, float):
        return False
    # `json.loads` produce enteros de Python de precisión arbitraria (p. ej. 10**400), y `math.isfinite` los
    # convierte a float internamente: si no caben lanza OverflowError crudo y se escaparía del contrato de los
    # adaptadores (AdapterError con prefijo de campo). Un entero no representable como float no es una medición
    # que ningún informe real produzca, así que se rechaza igual que NaN o infinito. Se captura aquí, en el
    # único predicado compartido, en lugar de comprobar el tamaño en cada adaptador (duplicaría la regla).
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


def _benchmark_run(run_id: str) -> dict:
    # El benchmark no registra commit, fecha, batería, corpus, embeddings ni prompt, y un informe trae varios
    # modelos, así que ni siquiera `generation_model` se rellena: el alias de cada modelo va en `behavior`.
    run = dict.fromkeys(RUN_KEYS)
    run.update(run_id=run_id, source="JUP-078", synthetic=False)
    return run


def _check_benchmark_header(report: object) -> list:
    if not isinstance(report, dict):
        raise _bad("report", "debe ser un objeto")
    version = report.get("schema_version")
    if type(version) is not int or version != BENCHMARK_SCHEMA_VERSION:
        raise _bad("schema_version", f"debe ser {BENCHMARK_SCHEMA_VERSION}")
    # Solo el booleano False garantiza que el informe no guarda texto de las respuestas (privacidad): un
    # informe que no lo declara no se carga, no se supone nada.
    if report.get("content_retained") is not False:
        raise _bad("content_retained", "debe ser false: el informe no puede retener texto")
    models = report.get("models")
    if not isinstance(models, list):
        raise _bad("models", "debe ser una lista")
    return models


def _check_benchmark_model(model: object, index: int, seen_aliases: set) -> dict:
    where = f"models[{index}]"
    if not isinstance(model, dict):
        raise _bad(where, "debe ser un objeto")
    for field in MODEL_REQUIRED:
        if field not in model:
            raise _bad(f"{where}.{field}", "campo obligatorio ausente")
    alias = model["alias"]
    # El alias acaba en `behavior`, y la regla 3 del contrato prohíbe en él el texto libre.
    if not _is_identifier(alias):
        raise _bad(f"{where}.alias", "debe ser un identificador (alfabeto cerrado, máximo 80 caracteres)")
    if alias in seen_aliases:
        raise _bad(f"{where}.alias", f"alias {alias!r} repetido")
    seen_aliases.add(alias)
    for field in ("cases", "successful"):
        if not _is_count(model[field]) or model[field] < 0:
            raise _bad(f"{where}.{field}", "debe ser un entero mayor o igual que 0")
    if model["successful"] > model["cases"]:
        raise _bad(f"{where}.successful", "no puede ser mayor que cases")
    # Se validan siempre, también sin llamadas correctas: un NaN no debe esconderse como «no medido».
    for field, _, _, _ in BENCHMARK_MEASURES:
        if model[field] is not None and not _is_number(model[field]):
            raise _bad(f"{where}.{field}", "debe ser un número finito o null")
    return model


def _benchmark_row(metric_id: str, alias: str, unit: str, **fields) -> dict:
    return _row("benchmark", metric_id, alias, unit, "automatic", **fields)


def _benchmark_measure_rows(model: dict) -> list[dict]:
    alias, successful = model["alias"], model["successful"]
    rows = []
    for field, metric_id, unit, per_successful in BENCHMARK_MEASURES:
        denominator = successful if per_successful else None
        value = model[field]
        # Con `successful == 0` el generador (`summarize` de tools/llm-benchmark.py) escribe
        # `mean_keyword_score = 0` porque no tiene qué promediar: ese 0 significa «sin datos», no «puntuación
        # nula», y publicarlo como medido violaría la regla 1 (lo no medido nunca es cero). Sin llamadas
        # correctas tampoco puede haber latencia ni coste, así que se descartan aunque el informe traiga un
        # número. Con `successful > 0` un 0 sí es una medición y se copia tal cual.
        if successful == 0 or value is None:
            rows.append(_benchmark_row(metric_id, alias, unit, status="not_measured", denominator=denominator))
        else:
            rows.append(_benchmark_row(metric_id, alias, unit, status="measured", value=value,
                                       denominator=denominator))
    return rows


def _benchmark_model_rows(model: dict) -> list[dict]:
    alias, cases, successful = model["alias"], model["cases"], model["successful"]
    # `pass` = successful y `fail` = cases - successful, con `cases` de denominador: el benchmark solo
    # distingue llamadas correctas de las que no lo fueron.
    rows = [
        _benchmark_row("cases", alias, "casos", status="pass", count=successful, denominator=cases),
        _benchmark_row("cases", alias, "casos", status="fail", count=cases - successful, denominator=cases),
    ]
    return rows + _benchmark_measure_rows(model)


def adapt_jup078(report, run_id: str) -> tuple[dict, list[dict]]:
    """Normaliza el informe del benchmark de JUP-078 (ya parseado) a `(run, results)` de `rows-v1`.

    Función pura: no lee ficheros, no muta el informe ni comparte estructuras con él. Por cada modelo, en
    el orden del informe, produce cinco filas: casos `pass`, casos `fail`, puntuación de palabras clave,
    latencia p95 y coste. No copia texto libre: ni los resultados por caso ni los tipos de error.
    """
    models = _check_benchmark_header(report)
    seen_aliases: set = set()
    results: list[dict] = []
    for index, model in enumerate(models):
        results += _benchmark_model_rows(_check_benchmark_model(model, index, seen_aliases))
    return _benchmark_run(run_id), results


# --- Comparación local pareada de JUP-063 -------------------------------------------------------------

PAIRED_STATE = "PAIRED_LOCAL_PROVISIONAL_COMPARISON"
PAIRED_MODELS = ("DeepSeekV4.1Flash", "GLM5.2")
PAIRED_VERDICTS = ("provisional_pass", "provisional_fail", "pending")
PAIRED_LATENCY_SCOPE = (
    "provider generation phases only; excludes startup, resources, preflight and scheduler"
)


def adapt_jup063_paired(report, run_id: str) -> tuple[dict, list[dict]]:
    """Proyecta agregados publicados, nunca textos ni una aceptación funcional.

    Los juicios provisionales NO son estados `cases/pass` ni ACC-1. Se conservan como
    recuentos de rúbrica local provisional bajo `paired_local_provisional`, separados del benchmark
    JUP-078 y de las campañas canónicas. La observación del agregador no fecha la
    ejecución y no aporta hashes de corpus/configuración: esos metadatos quedan null.
    """
    if not isinstance(report, dict) or report.get("state") != PAIRED_STATE:
        raise _bad("state", f"debe ser {PAIRED_STATE}")
    models = report.get("models")
    if not isinstance(models, dict) or set(models) != set(PAIRED_MODELS):
        raise _bad("models", "se requieren exactamente DeepSeekV4.1Flash y GLM5.2")
    run = dict.fromkeys(RUN_KEYS)
    # Este formato conserva la comparación de llamadas de proveedor, no un doble.
    # `synthetic` es obligatorio booleano en rows-v1; no equivale a aceptación.
    run.update(run_id=run_id, source="JUP-063", synthetic=False)
    results = []
    totals = []
    for alias in PAIRED_MODELS:
        model = models[alias]
        where = f"models.{alias}"
        if not isinstance(model, dict):
            raise _bad(where, "debe ser un objeto")
        if model.get("acceptance") != "NOT_ASSESSED":
            raise _bad(f"{where}.acceptance", "debe ser NOT_ASSESSED")
        n = model.get("responses")
        if not _is_count(n) or n <= 0:
            raise _bad(f"{where}.responses", "debe ser un entero positivo")
        totals.append(n)
        verdicts = model.get("verdicts")
        if not isinstance(verdicts, dict) or set(verdicts) - set(PAIRED_VERDICTS):
            raise _bad(f"{where}.verdicts", "solo admite los tres juicios provisionales")
        if any(not _is_count(value) or value < 0 for value in verdicts.values()):
            raise _bad(f"{where}.verdicts", "los recuentos deben ser enteros no negativos")
        if sum(verdicts.values()) != n:
            raise _bad(f"{where}.verdicts", "la suma debe coincidir con responses")
        for metric in PAIRED_VERDICTS:
            # Un estado omitido tiene cero ocurrencias únicamente tras conciliar la
            # partición completa del total. No se convierte una medición ausente en cero.
            results.append(_row("paired_local_provisional", metric, alias, "recuento", None,
                                status="measured", value=verdicts.get(metric, 0), denominator=n))
        results.append(_row("paired_local_provisional", "sample_size", alias, "recuento", "automatic",
                            status="measured", value=n, denominator=n))
        unknown = model.get("phases_with_unknown_cost")
        if not _is_count(unknown) or unknown < 0:
            raise _bad(f"{where}.phases_with_unknown_cost", "debe ser un entero no negativo")
        results.append(_row("paired_local_provisional", "unknown_cost_phases", alias, "recuento", "automatic",
                            status="measured", value=unknown))
        cost = model.get("reported_phase_cost_usd")
        # El informe registra decimales como cadenas. No aceptar NaN/Infinity ni bool,
        # y no confundir coste de fases con liquidación de cuenta o gasto total.
        if cost is not None:
            if not isinstance(cost, str) or re.fullmatch(r"[0-9]+(?:\.[0-9]+)?", cost) is None:
                raise _bad(f"{where}.reported_phase_cost_usd", "debe ser decimal no negativo o null")
            cost = float(cost)
            if not math.isfinite(cost):
                raise _bad(f"{where}.reported_phase_cost_usd", "debe ser finito")
        results.append(_row("paired_local_provisional", "reported_phase_cost_usd", alias, "usd", "automatic",
                            status="not_measured" if cost is None else "measured", value=cost))
        if model.get("latency_scope") != PAIRED_LATENCY_SCOPE:
            raise _bad(f"{where}.latency_scope", "el alcance no es el de fases de generación")
        latency_values = []
        for quantile in ("p50", "p95", "max"):
            metric = f"generation_seconds_{quantile}"
            value = model.get(metric)
            if value is not None and (not _is_number(value) or value < 0):
                raise _bad(f"{where}.{metric}", "debe ser finito no negativo o null")
            latency_values.append(value)
            results.append(_row("paired_local_provisional", metric, alias, "s", "automatic",
                                status="not_measured" if value is None else "measured", value=value,
                                denominator=n))
        measured = [value for value in latency_values if value is not None]
        if measured != sorted(measured):
            raise _bad(f"{where}.generation_seconds", "se exige p50 <= p95 <= max")
    if totals[0] != totals[1]:
        raise _bad("models.responses", "la comparación pareada exige el mismo tamaño")
    return run, results


# --- Adaptador de la calibración de JUP-022 -----------------------------------------------------------

CALIBRATION_SCHEMA_VERSION = 1
CALIBRATION_JUP = "JUP-022"
# El informe redondea las tasas a 4 decimales, así que `round(k / n, 4)` se aleja como mucho 5e-5 de `k / n`.
# Esa es la tolerancia con la que se acepta que `round(tasa * casos)` reproduce la tasa publicada: más
# estricta rechazaría tasas legítimas (1/3 se escribe 0.3333) y más laxa inventaría numeradores que el
# informe no respalda (regla 5 del contrato: el numerador se publica solo si es exacto).
CALIBRATION_TOLERANCE = 5e-5
# (metric_id, grupo del punto, campo de la tasa, campo del denominador). El orden es el de las cinco filas de
# cada punto y es parte del contrato. La sección de los casos `answer` tiene su propio denominador
# (`section_cases`) porque no todos los casos tienen sección esperada; mezclarlo con `cases` falsearía la tasa.
CALIBRATION_METRICS = (
    ("document_hit_answer", "answer", "document_hit_rate", "cases"),
    ("section_hit_answer", "answer", "section_hit_rate", "section_cases"),
    ("empty_answer", "answer", "empty_rate", "cases"),
    ("document_hit_non_answer", "non_answer", "document_hit_rate", "cases"),
    ("empty_non_answer", "non_answer", "empty_rate", "cases"),
)
# Recuentos de casos que cada grupo debe traer; `non_answer` no tiene sección y no se le exige.
CALIBRATION_CASE_FIELDS = (("answer", ("cases", "section_cases")), ("non_answer", ("cases",)))


def _check_identifier_field(parent: dict, key: str, where: str) -> None:
    # Lo que acaba en `run` no puede ser texto libre (regla 3): se exige un identificador. La clave ausente
    # da None y se rechaza por la misma vía, así que no hace falta una rama aparte para «falta».
    if not _is_identifier(parent.get(key)):
        raise _bad(f"{where}.{key}", "debe ser un identificador (alfabeto cerrado, máximo 80 caracteres)")


def _check_calibration_header(report: object) -> None:
    if not isinstance(report, dict):
        raise _bad("report", "debe ser un objeto")
    version = report.get("schema_version")
    if type(version) is not int or version != CALIBRATION_SCHEMA_VERSION:
        raise _bad("schema_version", f"debe ser {CALIBRATION_SCHEMA_VERSION}")
    # Solo un informe de JUP-022 se interpreta como calibración: otro con la misma forma significaría otra cosa.
    if report.get("jup") != CALIBRATION_JUP:
        raise _bad("jup", f"debe ser {CALIBRATION_JUP!r}")
    date = report.get("generated_at")
    try:
        if not isinstance(date, str):
            raise ValueError("no es una cadena")
        datetime.fromisoformat(date)
    except ValueError as error:
        raise _bad("generated_at", f"debe ser una fecha ISO 8601 ({error})") from error


def _check_calibration_sections(report: dict) -> None:
    # Solo se valida lo que se usa. Rutas, textos y el resto de claves del informe se ignoran a propósito: no
    # se copian a la salida (regla 3) y exigirlas haría fallar el adaptador por datos que no publica.
    provider = _check_object(report.get("provider"), "provider")
    _check_identifier_field(provider, "name", "provider")
    _check_identifier_field(provider, "alias", "provider")
    corpus = _check_object(report.get("corpus"), "corpus")
    if not corpus:
        raise _bad("corpus", "debe tener al menos un documento")
    for key, entry in corpus.items():
        entry = _check_object(entry, f"corpus.{_key_label(key)}")
        sha = entry.get("sha256")
        if not isinstance(sha, str) or not sha:
            raise _bad(f"corpus.{_key_label(key)}.sha256", "debe ser una cadena no vacía")
    _check_identifier_field(_check_object(report.get("bank"), "bank"), "suite_version", "bank")
    chunking = _check_object(report.get("chunking"), "chunking")
    for field in ("size", "overlap"):
        if not _is_count(chunking.get(field)) or chunking[field] < 0:
            raise _bad(f"chunking.{field}", "debe ser un entero mayor o igual que 0")


def _check_top_k(parent: dict, where: str) -> None:
    value = parent.get("top_k")
    if not _is_count(value) or value < 1:
        raise _bad(f"{where}.top_k", "debe ser un entero mayor o igual que 1")


def _check_max_distance(parent: dict, where: str) -> None:
    # None es «sin umbral» y es válido; la clave AUSENTE no, porque podría ser un informe incompleto.
    if "max_distance" not in parent:
        raise _bad(f"{where}.max_distance", "campo obligatorio ausente")
    value = parent["max_distance"]
    if value is not None and (not _is_number(value) or value <= 0):
        raise _bad(f"{where}.max_distance", "debe ser un número finito mayor que 0 o null")


def _check_calibration_group(point: dict, group: str, case_fields: tuple, where: str) -> None:
    where = f"{where}.{group}"
    data = _check_object(point.get(group), where)
    for field in case_fields:
        if not _is_count(data.get(field)) or data[field] < 0:
            raise _bad(f"{where}.{field}", "debe ser un entero mayor o igual que 0")
    for _, rate_group, rate_key, _ in CALIBRATION_METRICS:
        if rate_group != group:
            continue
        if rate_key not in data:
            raise _bad(f"{where}.{rate_key}", "campo obligatorio ausente")
        rate = data[rate_key]
        # None es «no medido»; un valor fuera de [0, 1] no es una tasa (un 2 o un NaN no deben publicarse).
        if rate is not None and (not _is_number(rate) or not 0 <= rate <= 1):
            raise _bad(f"{where}.{rate_key}", "debe ser un número entre 0 y 1 o null")


def _check_calibration_points(report: dict) -> list:
    points = report.get("points")
    if not isinstance(points, list):
        raise _bad("points", "debe ser una lista")
    seen: set = set()
    for index, point in enumerate(points):
        where = f"points[{index}]"
        _check_object(point, where)
        _check_top_k(point, where)
        _check_max_distance(point, where)
        for group, case_fields in CALIBRATION_CASE_FIELDS:
            _check_calibration_group(point, group, case_fields, where)
        # Dos puntos con la misma pareja serían filas con el mismo `behavior`, y la base no admite duplicados.
        key = (point["top_k"], point["max_distance"])
        if key in seen:
            raise _bad(where, "punto repetido (mismos top_k y max_distance)")
        seen.add(key)
    return points


def _check_calibration_candidates(report: dict, swept: set) -> set:
    selection = _check_object(report.get("selection"), "selection")
    candidates = selection.get("candidates")
    if not isinstance(candidates, list):
        raise _bad("selection.candidates", "debe ser una lista")
    chosen: set = set()
    for index, candidate in enumerate(candidates):
        where = f"selection.candidates[{index}]"
        _check_object(candidate, where)
        _check_top_k(candidate, where)
        _check_max_distance(candidate, where)
        key = (candidate["top_k"], candidate["max_distance"])
        # Un candidato que no está en el barrido es un informe incoherente: no habría fila que marcar.
        if key not in swept:
            raise _bad(where, "el candidato no corresponde a ningún punto del barrido")
        chosen.add(key)
    return chosen


def _corpus_sha256(corpus: dict) -> str:
    # El informe lista varios documentos, pero `rows-v1` tiene una sola huella de corpus. Se deriva de las
    # líneas `<clave>=<sha256>` ordenadas por clave: así no depende del orden del JSON ni de las rutas (que
    # cambian entre máquinas sin que cambie el contenido) y cambia si cambia el contenido de cualquier
    # documento. Se descarta tomar solo un sha (ignoraría los demás) o hashear el JSON entero (arrastraría rutas).
    lines = [f"{key}={corpus[key]['sha256']}" for key in sorted(corpus)]
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


def _calibration_run(report: dict, run_id: str) -> dict:
    run = dict.fromkeys(RUN_KEYS)
    run.update(
        run_id=run_id, source=CALIBRATION_JUP, run_at=report["generated_at"], suite="JUP-069",
        suite_version=report["bank"]["suite_version"], corpus_sha256=_corpus_sha256(report["corpus"]),
        embedding_provider=report["provider"]["name"], embedding_alias=report["provider"]["alias"],
        # `top_k` y `max_distance` varían por punto y van en cada fila; aquí solo lo común a todo el barrido.
        retrieval={"chunk_size": report["chunking"]["size"], "chunk_overlap": report["chunking"]["overlap"]},
        # La calibración no registra commit, huella de la batería, modelo de generación ni prompt.
        synthetic=False,
    )
    return run


def _calibration_row(metric_id: str, behavior: str, selected: bool, rate, denominator: int) -> dict:
    # Una tasa sobre cero casos es «sin datos» aunque el informe traiga un número (incluso 0.0): publicarlo
    # como medido violaría la regla 1 (lo no medido nunca es cero). Con casos, un 0.0 SÍ es una medición.
    if rate is None or denominator == 0:
        return _row("calibration", metric_id, behavior, "tasa", "automatic", status="not_measured",
                    denominator=denominator, selected=selected)
    # Regla 5: el numerador no se inventa. Se publica solo si `round(tasa * casos)` reproduce la tasa dentro
    # del redondeo del informe; una tasa que no es ninguna fracción k/n queda sin numerador.
    numerator = round(rate * denominator)
    if abs(numerator / denominator - rate) > CALIBRATION_TOLERANCE:
        numerator = None
    return _row("calibration", metric_id, behavior, "tasa", "automatic", status="measured", value=rate,
                numerator=numerator, denominator=denominator, selected=selected)


def _calibration_point_rows(point: dict, chosen: set) -> list[dict]:
    top_k, max_distance = point["top_k"], point["max_distance"]
    distance = "none" if max_distance is None else str(max_distance)
    behavior = f"top_k={top_k},max_distance={distance}"
    selected = (top_k, max_distance) in chosen
    return [
        _calibration_row(metric_id, behavior, selected, point[group][rate_key], point[group][cases_key])
        for metric_id, group, rate_key, cases_key in CALIBRATION_METRICS
    ]


def adapt_jup022(report, run_id: str) -> tuple[dict, list[dict]]:
    """Normaliza el informe de calibración de JUP-022 (ya parseado) a `(run, results)` de `rows-v1`.

    Función pura: no lee ficheros, no muta el informe ni comparte estructuras con él. Por cada punto del
    barrido, en el orden del informe, produce cinco filas: acierto de documento y de sección y resultado
    vacío de los casos `answer`, y acierto de documento y resultado vacío de los `non_answer`. Copia las
    tasas sin recalcularlas; no publica `by_category` (no trae denominador) ni rutas ni texto libre.
    """
    _check_calibration_header(report)
    _check_calibration_sections(report)
    points = _check_calibration_points(report)
    chosen = _check_calibration_candidates(report, {(p["top_k"], p["max_distance"]) for p in points})
    results: list[dict] = []
    for point in points:
        results += _calibration_point_rows(point, chosen)
    return _calibration_run(report, run_id), results


# --- Adaptador de las métricas de negocio de JUP-068 --------------------------------------------------

BUSINESS_SCHEMA_VERSION = 1
BUSINESS_JUP = "JUP-068"
# Generador de Node: el informe se obtiene ejecutándolo y no reimplementando sus fórmulas en Python, para
# que el dashboard no pueda divergir de él (regla 4: los adaptadores copian, no recalculan).
BUSINESS_CLI = ROOT / "tools" / "business-metrics.mjs"
# Plazo máximo del generador: evita que un `node` colgado bloquee la carga entera.
BUSINESS_TIMEOUT_SECONDS = 60
# Solo `synthetic` marca la ejecución como sintética; `measured` es una ejecución con datos observados.
BUSINESS_PROVENANCES = ("synthetic", "measured")
# Moneda en mayúsculas de tres letras. Se valida con `fullmatch` por la misma razón que los identificadores:
# un `$` casaría antes de un salto de línea final y dejaría pasar "EUR\n".
CURRENCY_RE = re.compile(r"[A-Z]{3}")
# Campos que se publican, por bloque. Todo lo demás del informe se ignora a propósito: `scope`,
# `configuration`, `reviewer`, `evidence` y `cost_basis` son texto libre, `period` son fechas de calendario y
# `pairs` y `estimates` llevan identificadores arbitrarios de parejas, recursos y estimaciones (regla 3). Los
# agregados que sí se publican ya resumen todo lo que esas listas contienen.
BUSINESS_TIME_COUNTS = ("eligible_pairs", "manual_ms", "assisted_ms")
BUSINESS_ALLOCATION_COUNTS = ("allocated", "shared", "unallocated", "excluded", "total_minor", "eligible_minor")
BUSINESS_SAVINGS_COUNTS = ("estimated_count", "candidate_count", "not_evaluable_count")
# Enteros que pueden ser null: `saved_ms` (null sin parejas elegibles; puede ser negativo si el asistente
# tardó más), `potential_minor` (null sin estimaciones) y `realized_minor` (ver `_business_savings_rows`).
BUSINESS_NULLABLE_INTS = (
    ("time", "saved_ms"), ("savings", "potential_minor"), ("savings", "realized_minor"),
)
# Porcentajes que pueden ser null (división por cero o magnitud ausente). Pueden ser negativos o mayores de
# 100, y un entero del JSON (40) es tan válido como un flotante (14.000000000000002).
BUSINESS_NULLABLE_NUMBERS = (
    ("time", "saved_percent"), ("allocation", "assigned_percent"), ("allocation", "governed_percent"),
    ("allocation", "unallocated_percent"), ("savings", "potential_percent"),
)
# (etiqueta de `behavior`, campo del informe) de los tres recuentos de oportunidades.
BUSINESS_OPPORTUNITIES = (
    ("estimated", "estimated_count"), ("candidate", "candidate_count"),
    ("not_evaluable", "not_evaluable_count"),
)
# (metric_id, campo del informe) de los seis importes de asignación, en el orden del contrato.
BUSINESS_AMOUNTS = (
    ("allocated", "allocated"), ("shared", "shared"), ("unallocated", "unallocated"),
    ("excluded", "excluded"), ("total", "total_minor"), ("eligible", "eligible_minor"),
)


def _check_business_header(report: object) -> None:
    if not isinstance(report, dict):
        raise _bad("report", "debe ser un objeto")
    version = report.get("schema_version")
    if type(version) is not int or version != BUSINESS_SCHEMA_VERSION:
        raise _bad("schema_version", f"debe ser {BUSINESS_SCHEMA_VERSION}")
    # Solo un informe de JUP-068 se interpreta como negocio: otro con la misma forma significaría otra cosa.
    if report.get("jup") != BUSINESS_JUP:
        raise _bad("jup", f"debe ser {BUSINESS_JUP!r}")
    if report.get("provenance") not in BUSINESS_PROVENANCES:
        raise _bad("provenance", f"debe ser uno de {', '.join(BUSINESS_PROVENANCES)}")
    # Commit, versión del dataset y huella acaban en `run`, donde la regla 3 solo admite identificadores.
    for field in ("commit", "dataset_version", "input_sha256"):
        if not _is_identifier(report.get(field)):
            raise _bad(field, "debe ser un identificador (alfabeto cerrado, máximo 80 caracteres)")
    currency = report.get("currency")
    if not isinstance(currency, str) or CURRENCY_RE.fullmatch(currency) is None:
        raise _bad("currency", "debe ser un código de moneda de tres letras mayúsculas")
    digits = report.get("minor_unit_digits")
    if not _is_count(digits) or digits < 0:
        raise _bad("minor_unit_digits", "debe ser un entero mayor o igual que 0")


def _check_business_counts(parent: dict, keys: tuple, where: str) -> None:
    for key in keys:
        value = parent.get(key)
        # `_is_count` exige `type(...) is int`: bool y los flotantes, incluso 1.0, no son recuentos. La clave
        # ausente da None y se rechaza por la misma vía.
        if not _is_count(value) or value < 0:
            raise _bad(f"{where}.{key}", "debe ser un entero mayor o igual que 0")


def _check_business_nullable(report: dict, paths: tuple, valid, problem: str) -> None:
    for block, key in paths:
        parent = report[block]
        # La clave AUSENTE no vale aunque null sí: sería un informe incompleto y no «no medido».
        if key not in parent:
            raise _bad(f"{block}.{key}", "campo obligatorio ausente")
        if parent[key] is not None and not valid(parent[key]):
            raise _bad(f"{block}.{key}", problem)


def _check_business_blocks(report: dict) -> None:
    time = _check_object(report.get("time"), "time")
    results = _check_object(time.get("results"), "time.results")
    allocation = _check_object(report.get("allocation"), "allocation")
    savings = _check_object(report.get("savings"), "savings")
    _check_business_counts(results, CASE_STATUSES, "time.results")
    _check_business_counts(time, BUSINESS_TIME_COUNTS, "time")
    _check_business_counts(allocation, BUSINESS_ALLOCATION_COUNTS, "allocation")
    _check_business_counts(savings, BUSINESS_SAVINGS_COUNTS, "savings")
    _check_business_nullable(report, BUSINESS_NULLABLE_INTS, _is_count, "debe ser un entero o null")
    _check_business_nullable(report, BUSINESS_NULLABLE_NUMBERS, _is_number, "debe ser un número finito o null")


def _business_run(report: dict, run_id: str) -> dict:
    # Solo lo que el informe registra de verdad; corpus, embeddings, recuperación, modelo y prompt no existen
    # en JUP-068 y quedan en None («no registrado»). `run_at` también: el informe trae un periodo (fechas
    # de calendario del registro), no la marca de ejecución, y no se inventa una a partir de él.
    run = dict.fromkeys(RUN_KEYS)
    run.update(
        run_id=run_id, source=BUSINESS_JUP, commit=report["commit"], suite=BUSINESS_JUP,
        suite_version=report["dataset_version"], suite_sha256=report["input_sha256"],
        # Solo `synthetic` es sintético: una ejecución medida no puede esconderse de las series reales.
        synthetic=report["provenance"] == "synthetic",
    )
    return run


def _business_row(grp: str, metric_id: str, unit: str, behavior: str = "all", **fields) -> dict:
    # Tipo B: `judgment` es None porque «automático o humano» solo describe el juicio sobre los casos de una
    # rúbrica (tipo A); aquí no hay rúbrica ni revisor por fila, y la tabla del contrato fija null.
    return _row(grp, metric_id, behavior, unit, None, measure_type="B", **fields)


def _business_value(grp: str, metric_id: str, unit: str, value, denominator=None, numerator=None,
                    behavior: str = "all", measured: bool = True) -> dict:
    # `measured` False manda sobre el valor (regla 6): una suma de nada que el informe escribe como 0 no es una
    # medición. Un 0 con `measured` True SÍ lo es y se copia. Lo no medido conserva el denominador (regla 5)
    # y deja valor y numerador a None (regla 1). El valor se copia con su tipo, sin redondear (regla 4).
    if not measured or value is None:
        return _business_row(grp, metric_id, unit, behavior, status="not_measured", denominator=denominator)
    return _business_row(grp, metric_id, unit, behavior, status="measured", value=value,
                         numerator=numerator, denominator=denominator)


def _business_time_rows(time: dict) -> list[dict]:
    results = time["results"]
    trials = sum(results[status] for status in CASE_STATUSES)
    # Los cuatro estados son recuentos de parejas con el total de intentos como denominador, igual que los
    # estados de casos (regla 2): `blocked` y `not_run` no se suman a `fail`.
    rows = [_business_row("time", "time_trials", "parejas", status=status, count=results[status],
                          denominator=trials) for status in CASE_STATUSES]
    pairs, manual = time["eligible_pairs"], time["manual_ms"]
    # Sin parejas elegibles (ninguna `pass`) el tiempo manual y el asistido son sumas de nada: el generador
    # escribe 0, pero ese 0 significa «sin datos», no «cero milisegundos», y publicarlo como medido violaría
    # la regla 1. Con parejas elegibles un 0 sí es una medición. Lo decide `eligible_pairs`, no que valga 0;
    # el ahorro y su porcentaje dependen de esas mismas parejas, así que comparten el criterio.
    measured = pairs > 0
    return rows + [
        _business_value("time", "manual_time", "ms", manual, pairs, measured=measured),
        _business_value("time", "assisted_time", "ms", time["assisted_ms"], pairs, measured=measured),
        _business_value("time", "time_saved", "ms", time["saved_ms"], pairs, measured=measured),
        # El porcentaje es proporción del tiempo manual: ese es su denominador aunque valga 0, y su numerador
        # es el ahorro. Con manual 0 el informe lo deja en null y queda no medido con denominador 0.
        _business_value("time", "time_saved_percent", "porcentaje", time["saved_percent"], manual,
                        numerator=time["saved_ms"], measured=measured),
    ]


def _business_allocation_rows(allocation: dict, money: str) -> list[dict]:
    # Los importes van en la unidad `<moneda en minúsculas>_minor_<dígitos>` (p. ej. `eur_minor_2`: importes
    # enteros en céntimos). Se publican en unidad menor y enteros para no perder exactitud con flotantes, y la
    # moneda y la escala forman parte de la unidad para que nunca se sumen ni comparen importes de monedas o
    # escalas distintas. Va en minúsculas porque la regla 3 usa el mismo alfabeto para unidades e identificadores.
    rows = [_business_value("allocation", metric, money, allocation[key]) for metric, key in BUSINESS_AMOUNTS]
    eligible = allocation["eligible_minor"]
    # Numeradores: lo que `tools/business-metrics.mjs` divide entre el gasto elegible. «Gobernado» es lo
    # asignado más lo compartido; el gasto excluido queda fuera de los tres porcentajes.
    for metric, numerator in (
        ("assigned_percent", allocation["allocated"]),
        ("governed_percent", allocation["allocated"] + allocation["shared"]),
        ("unallocated_percent", allocation["unallocated"]),
    ):
        rows.append(_business_value("allocation", metric, "porcentaje", allocation[metric], eligible,
                                    numerator=numerator))
    return rows


def _business_savings_rows(savings: dict, eligible: int, money: str) -> list[dict]:
    rows = [_business_value("savings", "opportunities", "recuento", savings[key], behavior=behavior)
            for behavior, key in BUSINESS_OPPORTUNITIES]
    return rows + [
        _business_value("savings", "potential_savings", money, savings["potential_minor"]),
        _business_value("savings", "potential_savings_percent", "porcentaje", savings["potential_percent"],
                        eligible, numerator=savings["potential_minor"]),
        # El informe de hoy deja `realized_minor` SIEMPRE en null por diseño: el beneficio realizado está fuera
        # de alcance mientras no haya un piloto real, así que la fila sale no medida («beneficio realizado no
        # medido») y nunca como 0. Si un informe futuro trae un entero, es una medición y se copia.
        _business_value("savings", "realized_savings", money, savings["realized_minor"]),
    ]


def adapt_jup068(report, run_id: str) -> tuple[dict, list[dict]]:
    """Normaliza el informe de JUP-068 (ya parseado) a `(run, results)` del contrato `rows-v1`.

    Función pura: no lee ficheros, no muta el informe ni comparte estructuras con él. Produce 23 filas de
    tipo B en este orden: 8 de tiempo (estados de las parejas, tiempo manual, asistido, ahorrado y su
    porcentaje), 9 de asignación (seis importes y tres porcentajes) y 6 de ahorro (tres recuentos de
    oportunidades, ahorro potencial, su porcentaje y ahorro realizado). Copia los valores sin recalcularlos;
    no publica texto libre (`scope`, `configuration`, `reviewer`, `evidence`), el periodo ni las listas de
    parejas y estimaciones.
    """
    _check_business_header(report)
    _check_business_blocks(report)
    money = f"{report['currency'].lower()}_minor_{report['minor_unit_digits']}"
    results = _business_time_rows(report["time"])
    results += _business_allocation_rows(report["allocation"], money)
    results += _business_savings_rows(report["savings"], report["allocation"]["eligible_minor"], money)
    return _business_run(report, run_id), results


def _business_failure(path, problem: str) -> AdapterError:
    # Todo fallo del generador sale con el mismo prefijo y el nombre del fichero, para que quien edita el
    # manifiesto sepa qué registro de negocio falló sin abrir el código.
    return AdapterError(f"business-metrics: {Path(path).name}: {problem}")


def read_business_report(path) -> dict:
    """Ejecuta `node tools/business-metrics.mjs report <ruta>` y devuelve el informe como dict.

    Cualquier fallo (Node ausente, plazo agotado, código de salida distinto de 0, salida que no es un objeto
    JSON) es un `AdapterError` que empieza por `business-metrics: ` y nombra el fichero.
    """
    command = ["node", str(BUSINESS_CLI), "report", str(path)]
    try:
        # Sin `shell` y con la ruta como argumento propio: nada se interpreta ni se escapa. `cwd=ROOT` para que
        # el generador se ejecute igual desde cualquier directorio de trabajo.
        completed = subprocess.run(command, capture_output=True, text=True, encoding="utf-8",
                                   timeout=BUSINESS_TIMEOUT_SECONDS, cwd=ROOT)
    except (OSError, subprocess.SubprocessError, ValueError) as error:
        # Aquí SÍ se capturan excepciones concretas: son las fronteras del proceso (Node no instalado, permisos,
        # plazo agotado, argumentos con caracteres nulos), no errores de programación que deban salir tal cual.
        raise _business_failure(path, f"no se pudo ejecutar el generador ({error})") from error
    if completed.returncode != 0:
        # El código de salida manda sobre el stdout aunque parezca un informe. Se incluye la primera línea no
        # vacía del stderr (el motivo del generador); el resto suele ser una traza que no ayuda a quien edita.
        reason = next((line for line in completed.stderr.splitlines() if line.strip()), "sin mensaje")
        raise _business_failure(path, f"el generador terminó con código {completed.returncode}: {reason}")
    try:
        report = json.loads(completed.stdout)
    except (ValueError, RecursionError) as error:
        raise _business_failure(path, f"la salida del generador no es JSON ({error})") from error
    if not isinstance(report, dict):
        raise _business_failure(path, "la salida del generador debe ser un objeto JSON")
    return report


# --- Validación común de filas y adaptador rows-v1 ----------------------------------------------------

ROWS_CONTRACT_VERSION = 1
# Claves de primer nivel de un documento `rows-v1`, en el orden en que se exigen.
ROWS_DOCUMENT_KEYS = ("contract_version", "run", "results")
# Los únicos campos de `run.retrieval`. Se rechaza cualquier otra clave para que una errata (`topk`) o un texto
# libre no lleguen a la base; no se exigen las cuatro porque JUP-022 solo publica el troceado (`top_k` y
# `max_distance` van por fila) y un informe puede traer solo algunas.
RETRIEVAL_KEYS = ("top_k", "max_distance", "chunk_size", "chunk_overlap")
MEASURE_TYPES = ("A", "B")
JUDGMENTS = ("automatic", "human")
ROW_STATUSES = CASE_STATUSES + VALUE_STATUSES
# Campos de la fila por clase de validación; el orden de la validación es el de RESULT_KEYS, no el de estas tuplas.
ROW_IDENTIFIERS = ("grp", "metric_id", "behavior", "unit")
ROW_COUNTS = ("count", "denominator")
ROW_NUMBERS = ("value", "numerator", "ci_low", "ci_high")
# Única unidad cuyo numerador es un recuento de aciertos acotado por el denominador (0 <= numerador <=
# denominador). En `porcentaje` o `ms` el numerador puede ser negativo (un ahorro de tiempo) o mayor.
RATE_UNIT = "tasa"
# Mayor entero seguro (2**53 - 1): el que un float de doble precisión representa sin pérdida y la misma cota que
# impone `tools/business-metrics.mjs`. Acota los enteros de las filas para que la carga SQL no los trunque:
# `count` y `denominator` caben en `bigint` y `value`, `numerator` y el intervalo en `double precision` sin
# perder enteros. Los floats finitos no tienen cota nueva.
ROW_MAX_INTEGER = 2 ** 53 - 1
# Formato exacto de `run.run_at`: `AAAA-MM-DDThh:mm:ss[.f{1,6}](Z|±hh:mm)`. Se usa con `fullmatch`. `re.ASCII`
# para que `\d` solo case 0-9 y no los dígitos de otros alfabetos que Unicode también llama dígitos.
RUN_AT_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|[+-]\d{2}:\d{2})", re.ASCII)
RUN_AT_PROBLEM = "debe ser null o una fecha AAAA-MM-DDThh:mm:ss[.ffffff](Z|+hh:mm) real"
# Campos del formato `rows-v1` de entrada que el documento no puede omitir. El resto es opcional: se rellena con
# None (`synthetic` y `selected` con False, el valor del contrato para «no declarado») y la validación común
# decide después si esa fila lo admite. `unit` y `judgment` son opcionales en el formato, pero la validación
# común los exige en las filas que los necesitan.
ROWS_RUN_REQUIRED = ("run_id", "source")
ROWS_RESULT_REQUIRED = ("measure_type", "grp", "metric_id", "behavior", "status")
ROWS_FALSE_DEFAULTS = frozenset({"synthetic", "selected"})


def _check_keys(item: dict, expected: tuple, where: str) -> None:
    # Primero las claves desconocidas y después las ausentes, cada una en la ruta de ESA clave. Un único
    # ayudante para `run` y para las filas evita dos versiones de la misma regla. `milestone` es una clave
    # desconocida de `run`: aunque la documentación la lista, la fija el manifiesto y no el informe, y aceptarla
    # dejaría que un informe se declarara de hito por su cuenta.
    for key in item:
        if key not in expected:
            raise _bad(f"{where}.{_key_label(key)}", "clave desconocida")
    for key in expected:
        if key not in item:
            raise _bad(f"{where}.{key}", "campo obligatorio ausente")


def _check_member(parent: dict, key: str, allowed: tuple, where: str) -> None:
    value = parent[key]
    # `isinstance(value, str)` antes de `in`: así un 1 o un True no se comparan con cadenas ni se cuelan.
    if not (isinstance(value, str) and value in allowed):
        raise _bad(f"{where}.{key}", f"debe ser uno de {', '.join(allowed)}")


def _check_bool(parent: dict, key: str, where: str) -> None:
    # `type(...) is bool`: 1, 0 o "true" no son booleanos del contrato JSON.
    if type(parent[key]) is not bool:
        raise _bad(f"{where}.{key}", "debe ser un booleano true o false")


def _check_count_or_null(parent: dict, key: str, where: str) -> None:
    value = parent[key]
    # `_is_count` exige `type(...) is int`: bool y los flotantes, incluso 3.0, no son recuentos.
    if value is not None and (not _is_count(value) or value < 0):
        raise _bad(f"{where}.{key}", "debe ser un entero mayor o igual que 0 o null")
    # La cota va aquí y no en `_is_count`: ese predicado lo comparten los adaptadores de informes y su
    # comportamiento ya está cubierto; esta función solo la usan las filas. Con ella `count` y `denominator`
    # caben en una columna `bigint` sin desbordar. El mensaje no incluye el valor recibido.
    if value is not None and value > ROW_MAX_INTEGER:
        raise _bad(f"{where}.{key}", f"debe ser un entero menor o igual que {ROW_MAX_INTEGER}")


def _check_number_or_null(parent: dict, key: str, where: str) -> None:
    value = parent[key]
    # `_is_number` ya rechaza bool, NaN, infinito y los enteros que no caben en un float (sin OverflowError).
    if value is not None and not _is_number(value):
        raise _bad(f"{where}.{key}", "debe ser un número finito o null")


def _check_row_number_or_null(row: dict, key: str, where: str) -> None:
    # Número de una fila: lo de `_check_number_or_null` más la cota de enteros. Función aparte porque
    # `_check_number_or_null` también valida `run.retrieval`, que no lleva esta cota. Solo se acotan los ENTEROS
    # (`type(...) is int`; un bool ya lo rechazó `_is_number`): un float finito, aunque enorme (1e308), cabe en
    # `double precision` y no pierde nada que el float no hubiera perdido ya al parsearse. Con `abs(x) <=
    # ROW_MAX_INTEGER` los enteros de `value`, `numerator` y del intervalo se guardan en `double precision` sin
    # pérdida. El mensaje no incluye el valor recibido.
    _check_number_or_null(row, key, where)
    value = row[key]
    if type(value) is int and abs(value) > ROW_MAX_INTEGER:
        raise _bad(f"{where}.{key}", f"un entero debe cumplir |valor| <= {ROW_MAX_INTEGER}")


def _validate_run_at(run: dict) -> None:
    value = run["run_at"]
    if value is None:
        return
    # Formato exacto y, además, fecha real. `datetime.fromisoformat` de Python 3.13 por sí solo no basta: acepta
    # CUALQUIER carácter como separador entre fecha y hora (comillas, `;`, NUL) y formas como `2026-W42-3` o
    # `20261014`, y este texto acabará dentro de un script SQL. La expresión regular fija la forma
    # (`fullmatch`, para que ni un salto de línea final se cuele como haría `$`) y `fromisoformat` descarta lo
    # que cumple el patrón de dígitos pero no existe (mes 13, 30 de febrero, hora 25). El mensaje NO cita el valor
    # ni el texto de la excepción de `fromisoformat` (que lo repite): sería volcar texto de un informe en un error.
    if not (isinstance(value, str) and RUN_AT_PATTERN.fullmatch(value)):
        raise _bad("run.run_at", RUN_AT_PROBLEM)
    try:
        datetime.fromisoformat(value)
    except ValueError:
        raise _bad("run.run_at", RUN_AT_PROBLEM) from None


def _validate_run_retrieval(run: dict) -> None:
    retrieval = run["retrieval"]
    if retrieval is None:
        return
    _check_object(retrieval, "run.retrieval")
    for key in retrieval:
        if key not in RETRIEVAL_KEYS:
            raise _bad(f"run.retrieval.{_key_label(key)}", "clave desconocida")
    for key in RETRIEVAL_KEYS:
        # Se recorre RETRIEVAL_KEYS y no el dict para que el orden del error no dependa del orden del documento.
        if key in retrieval:
            _check_number_or_null(retrieval, key, "run.retrieval")


def _validate_run_values(run: dict) -> None:
    # Los campos se validan en el orden de RUN_KEYS (no en el del dict del documento) para que el primer
    # error sea siempre el mismo con independencia de cómo llegue ordenado.
    for key in RUN_KEYS:
        if key in ("run_id", "source"):
            _check_identifier_field(run, key, "run")
        elif key == "run_at":
            _validate_run_at(run)
        elif key == "retrieval":
            _validate_run_retrieval(run)
        elif key == "synthetic":
            _check_bool(run, key, "run")
        elif key == "gateway_config_sha256":
            if run[key] is not None and not (isinstance(run[key], str) and GATEWAY_HASH_RE.fullmatch(run[key])):
                raise _bad(f"run.{key}", "debe ser un sha256 hexadecimal de 64 caracteres en minúsculas")
        elif run[key] is not None:
            # El resto son huellas, versiones y alias: opcionales (None es «no registrado»), pero nunca texto libre.
            _check_identifier_field(run, key, "run")


def _validate_row_judgment(row: dict, where: str) -> None:
    # El tipo A es `automatic` o `human`; el B no tiene rúbrica y su juicio es null (tabla del contrato).
    # Cuando se llega aquí `measure_type` ya está validado, así que la comparación con "A" es segura.
    if row["measure_type"] == "A":
        # La rúbrica local provisional no acredita ni checks automáticos ni
        # adjudicación humana independiente. NULL conserva esa atribución ausente
        # sin cambiar el CHECK existente de PostgreSQL ni clasificar otros datos.
        if (row["judgment"] is None and row["grp"] == "paired_local_provisional"
                and row["metric_id"] in PAIRED_VERDICTS):
            return
        _check_member(row, "judgment", JUDGMENTS, where)
    elif row["judgment"] is not None:
        raise _bad(f"{where}.judgment", "debe ser null en el tipo B")


def _validate_row_types(row: dict, where: str) -> None:
    # Orden de RESULT_KEYS. Los tipos van antes que la coherencia: un campo mal tipado no se puede comparar.
    for key in RESULT_KEYS:
        if key == "measure_type":
            _check_member(row, key, MEASURE_TYPES, where)
        elif key in ROW_IDENTIFIERS:
            _check_identifier_field(row, key, where)
        elif key == "status":
            _check_member(row, key, ROW_STATUSES, where)
        elif key in ROW_COUNTS:
            _check_count_or_null(row, key, where)
        elif key in ROW_NUMBERS:
            _check_row_number_or_null(row, key, where)
        elif key == "judgment":
            _validate_row_judgment(row, where)
        else:
            _check_bool(row, key, where)


def _status_rules(status: str) -> tuple[tuple, tuple]:
    # (campos que no pueden ser None, campos que deben ser None) según el estado. Regla 2: los estados de caso
    # llevan recuento y no valor ni numerador. Regla 1: lo medido lleva valor y no recuento; lo no medido no
    # lleva ni valor, ni numerador, ni recuento, ni intervalo, pero SÍ conserva el denominador (regla 5).
    if status in CASE_STATUSES:
        return ("count",), ("value", "numerator")
    if status == "measured":
        return ("value",), ("count",)
    return (), ("count", "value", "numerator", "ci_low", "ci_high")


def _validate_row_status_fields(row: dict, where: str) -> None:
    required, forbidden = _status_rules(row["status"])
    for key in RESULT_KEYS:
        # `is None` y no la veracidad: un 0 o un 0.0 no son None y publicarlos como «no medido» sería un cero.
        if key in required and row[key] is None:
            raise _bad(f"{where}.{key}", f"obligatorio en el estado {row['status']}")
        if key in forbidden and row[key] is not None:
            raise _bad(f"{where}.{key}", f"debe ser null en el estado {row['status']}")


def _validate_row_interval(row: dict, where: str) -> None:
    # Un intervalo con un solo límite no es un intervalo. Se informa en el límite que falta.
    if row["ci_low"] is None and row["ci_high"] is not None:
        raise _bad(f"{where}.ci_low", "falta el límite inferior: el intervalo lleva los dos límites o ninguno")
    if row["ci_high"] is None and row["ci_low"] is not None:
        raise _bad(f"{where}.ci_high", "falta el límite superior: el intervalo lleva los dos límites o ninguno")


def _validate_row_rate(row: dict, where: str) -> None:
    numerator, denominator = row["numerator"], row["denominator"]
    # Sin numerador o sin denominador no hay nada que comparar: el numerador solo se publica cuando es exacto
    # (regla 5). Solo la unidad `tasa` acota el numerador; en las demás puede ser negativo o mayor.
    if row["unit"] != RATE_UNIT or numerator is None or denominator is None:
        return
    if not 0 <= numerator <= denominator:
        raise _bad(f"{where}.numerator", "en una tasa debe cumplirse 0 <= numerador <= denominador")


def _validate_row(row: dict, where: str) -> None:
    _check_keys(row, RESULT_KEYS, where)
    _validate_row_types(row, where)
    _validate_row_status_fields(row, where)
    _validate_row_interval(row, where)
    _validate_row_rate(row, where)


def validate_rows(run, results) -> None:
    """Valida `run` y `results` con el contrato de filas planas `rows-v1` (reglas 7 y 8 del contrato).

    Es la barrera final de los adaptadores: ellos copian valores sin comprobar su tipo ni su alfabeto (regla
    4), así que un texto libre o una tasa que no es un número llegarían a la base sin esta validación. No
    devuelve nada ni muta nada; ante el primer incumplimiento lanza `AdapterError` cuyo mensaje empieza por la
    ruta exacta del campo (`run.commit`, `run.retrieval.top_k`, `results[3].value`...). Orden: primero `run` y
    después las filas en el orden de la lista; en cada una, claves, tipos, coherencia entre campos y, por último,
    duplicados. Se prefiere fallar en el primer error a acumularlos: la carga es atómica y quien corrige el
    informe repite la ejecución, así que un único error accionable basta y el código se mantiene simple.
    """
    _check_object(run, "run")
    _check_keys(run, RUN_KEYS, "run")
    _validate_run_values(run)
    if not isinstance(results, list):
        raise _bad("results", "debe ser una lista")
    seen: dict = {}
    for index, row in enumerate(results):
        where = f"results[{index}]"
        _validate_row(_check_object(row, where), where)
        # La base no admite dos filas con la misma clave natural. `measure_type` no forma parte de ella; la clave
        # es una tupla de cuatro componentes y no una concatenación para que `a`+`bc` y `ab`+`c` no choquen.
        key = (row["grp"], row["metric_id"], row["behavior"], row["status"])
        if key in seen:
            raise _bad(where, f"fila duplicada: mismos grp, metric_id, behavior y status que results[{seen[key]}]")
        seen[key] = index


def _document_field(document: dict, key: str):
    if key not in document:
        raise _bad(key, "campo obligatorio ausente")
    return document[key]


def _fill_optional(item: dict, keys: tuple, required: tuple) -> dict:
    # Copia superficial con lo opcional ausente rellenado. Las claves desconocidas se CONSERVAN a propósito: así
    # las rechaza `validate_rows` con su ruta y su orden, en lugar de que el adaptador las compruebe aparte (o,
    # peor, las descarte en silencio al construir la salida).
    filled = dict(item)
    for key in keys:
        if key not in required and key not in filled:
            filled[key] = False if key in ROWS_FALSE_DEFAULTS else None
    return filled


def adapt_rows_v1(document, run_id=None) -> tuple[dict, list[dict]]:
    """Normaliza un documento `rows-v1` (ya parseado) a `(run, results)`.

    Función pura: no muta el documento ni comparte estructuras con él. Rellena con None lo opcional que falta
    (`synthetic` y `selected` con False), devuelve `run` con exactamente RUN_KEYS y las filas con exactamente
    RESULT_KEYS en ese orden, y valida lo construido con `validate_rows`, cuyo `AdapterError` propaga. Si
    `run_id` no es None sustituye al `run_id` del documento (un hito de un informe repetido necesita otro
    identificador); la cadena vacía SÍ sustituye y se rechaza como identificador.
    """
    document = _check_object(document, "document")
    for key in document:
        if key not in ROWS_DOCUMENT_KEYS:
            raise _bad(f"document.{_key_label(key)}", "clave desconocida")
    # `type(...) is int`: True == 1 y 1.0 == 1 en Python, y solo el entero 1 exacto es la versión del contrato.
    version = _document_field(document, "contract_version")
    if type(version) is not int or version != ROWS_CONTRACT_VERSION:
        raise _bad("contract_version", f"debe ser {ROWS_CONTRACT_VERSION}")
    run = _fill_optional(_check_object(_document_field(document, "run"), "run"), RUN_KEYS, ROWS_RUN_REQUIRED)
    results = _document_field(document, "results")
    if not isinstance(results, list):
        raise _bad("results", "debe ser una lista")
    # `is not None` y no la veracidad: "" es un identificador inválido que hay que rechazar, no ignorar.
    if run_id is not None:
        run["run_id"] = run_id
    # Lo que no es un objeto pasa tal cual: `validate_rows` lo informa en `results[i]` sin que el adaptador
    # duplique esa comprobación ni adelante el error de una fila al de la ejecución.
    rows = [_fill_optional(row, RESULT_KEYS, ROWS_RESULT_REQUIRED) if isinstance(row, dict) else row
            for row in results]
    validate_rows(run, rows)
    # Tras validar, todo valor de la fila es un escalar inmutable; solo `retrieval` es un objeto mutable y se
    # copia en profundidad para que la salida no comparta estructura con el documento.
    return (
        {key: copy.deepcopy(run[key]) for key in RUN_KEYS},
        [{key: row[key] for key in RESULT_KEYS} for row in rows],
    )


# --- Clasificación de ejecuciones y clave de comparabilidad ---------------------------------------------------

# Motivos por los que una ejecución no es real, en el orden fijo del contrato («Ejecuciones no reales»). Es una
# tupla y no un conjunto porque el orden es parte del contrato: ordena los motivos de cada ejecución, entra en
# la clave de comparabilidad y hace reproducible la columna `non_real_reasons`.
NON_REAL_REASONS = ("plantilla", "doble", "sintetica", "sin_modelo_verificado")
# Columnas que la clasificación añade a la ejecución, al final y en este orden.
CLASSIFICATION_KEYS = ("is_real", "non_real_reasons", "comparability_key")

# Valores exactos que delatan una ejecución no real. Igualdad exacta (no `in`, `startswith` ni minúsculas):
# un nombre parecido («Mock», «mock2», «plantilla») es otro valor y no debe descartar una ejecución real.
TEMPLATE_MODEL = "plantilla-sin-modelo"
DOUBLE_NAME = "mock"
# Campañas sobre el chat: solo ellas deberían registrar el modelo que generó la respuesta.
CHAT_CAMPAIGN_SOURCES = ("JUP-070", "JUP-071")

# Campos de la ejecución que definen la comparabilidad, en el orden del contrato. Se enumeran aquí y no se
# derivan de `RUN_KEYS` por exclusión: añadir un campo a la ejecución no debe cambiar en silencio las claves
# ya guardadas (eso rompería la comparación con el histórico).
COMPARABILITY_FIELDS = (
    "source", "suite_version", "suite_sha256", "corpus_sha256", "embedding_provider", "embedding_alias",
    "retrieval", "generation_model", "prompt_sha256",
)

# Métricas del catálogo de JUP-067 que se miden sin juicio humano. Junto con `HUMAN_METRICS` debe cubrir el
# catálogo entero (`unclassified_metrics`). `ACC-2` figura aquí aunque su fila `judged` sea humana (`HUMAN_ROWS`):
# la disjunción se exige entre métricas enteras, y esa fila es una excepción por fila, no por métrica.
AUTOMATIC_METRICS = frozenset({
    "ACC-2", "REL-1", "REL-2", "REL-3", "REL-4", "GRD-1", "GRD-2", "GRD-3",
    "LAT-1", "LAT-2", "LAT-3", "LAT-4", "STR-1", "STR-2", "AVL-1",
})


def classify_run(run) -> tuple[str, ...]:
    """Devuelve los motivos por los que `run` no es real, en el orden fijo de `NON_REAL_REASONS`; `()` si lo es.

    Valida primero con `validate_rows(run, [])` y deja propagar su `AdapterError`: sin validar, un `synthetic`
    como `1` o `"true"` (truthy) se clasificaría mal, y la regla `is True` solo tiene sentido sobre un booleano
    ya garantizado. Cada motivo se evalúa por separado y se añade en el orden de la tupla, así que no depende
    del orden de las claves del diccionario ni puede repetirse.
    """
    validate_rows(run, [])
    reasons = []
    if run["generation_model"] == TEMPLATE_MODEL:
        reasons.append("plantilla")
    # `doble` mira proveedor y alias: un doble puede declararse en cualquiera de los dos (JUP-070 lo escribe en
    # el proveedor; un alias `mock` también apunta a un embedding simulado). Mirar solo uno dejaría pasar
    # como real una ejecución con recuperación simulada. Una sola condición `or` evita repetir el motivo.
    if run["embedding_provider"] == DOUBLE_NAME or run["embedding_alias"] == DOUBLE_NAME:
        reasons.append("doble")
    if run["synthetic"] is True:
        reasons.append("sintetica")
    # `sin_modelo_verificado` solo se aplica a campañas sobre el chat: JUP-078 trae varios modelos y no registra
    # ninguno en `run`, y JUP-022 y JUP-068 no generan respuestas. Allí `generation_model` nulo es lo normal y
    # marcarlas como no reales sería un falso positivo.
    # La proyección descriptiva JUP-133 contiene operaciones del chat, pero su
    # modelo sigue declarado, no atestado; no elevarla a real por cambiar source.
    chat_projection = run["source"] == "JUP-133" and run["suite"] == "descriptive-friday-sunday"
    if (run["source"] in CHAT_CAMPAIGN_SOURCES or chat_projection) and run["generation_model"] is None:
        reasons.append("sin_modelo_verificado")
    return tuple(reasons)


def _check_reasons(reasons) -> None:
    # Solo tupla o lista: una cadena se confundiría con una secuencia de letras y un conjunto o un diccionario
    # no tienen orden fiable, y el orden entra en la clave.
    if not isinstance(reasons, (tuple, list)):
        raise _bad("reasons", "debe ser una tupla o una lista de motivos")
    for reason in reasons:
        # `type(...) is str` antes de la pertenencia: rechaza `None`, números y listas anidadas (no hashables)
        # sin que salte otra excepción por el camino.
        if type(reason) is not str or reason not in NON_REAL_REASONS:
            raise _bad("reasons", f"motivo desconocido {reason!r}; los válidos son {list(NON_REAL_REASONS)}")
    # Orden fijo y sin repetidos a la vez: las posiciones en `NON_REAL_REASONS` deben crecer estrictamente. Dos
    # listas con los mismos motivos en distinto orden darían claves distintas para lo mismo.
    positions = [NON_REAL_REASONS.index(reason) for reason in reasons]
    if any(left >= right for left, right in zip(positions, positions[1:])):
        raise _bad("reasons", "los motivos deben ir sin repetir y en el orden fijo de NON_REAL_REASONS")


def comparability_key(run, reasons) -> str:
    """Clave de comparabilidad: sha256 hexadecimal (64 minúsculas) de la configuración de `run` y sus motivos.

    Dos ejecuciones con la misma clave son comparables en una misma serie del dashboard. Es un hash y no un
    texto concatenado para que sea una columna de tamaño fijo, indexable y que no deje ver la configuración; y
    es `hashlib` y no `hash()` porque `hash()` de una cadena cambia entre procesos (PYTHONHASHSEED) y la clave
    se guarda y se compara en otras ejecuciones. Se serializa una LISTA en JSON canónico (`sort_keys` ordena
    las claves de `retrieval`; separadores compactos; `ensure_ascii`; UTF-8) para que ni `a`+`bc` frente a
    `ab`+`c` ni `null` frente a `"null"` colisionen. Los motivos entran porque una plantilla y una ejecución
    real con la misma configuración no son comparables. NO entran `run_id`, `run_at` ni `commit` (identifican
    una ejecución concreta: con ellos nunca habría dos iguales), `suite` (es el nombre del informe de origen,
    no de la batería; la batería la identifican `suite_version` y `suite_sha256`) ni `synthetic` (ya está
    representado por el motivo `sintetica`).

    Solo valida `reasons`; no vuelve a validar `run` (de eso se ocupa `classify_run`, que produce los motivos).
    """
    _check_reasons(reasons)
    payload = [run[field] for field in COMPARABILITY_FIELDS] + [list(reasons)]
    # La identidad del modelo entra solo si alguna parte está registrada: una ejecución sin identidad conserva la
    # clave que ya tenía, y «registrada» frente a «no registrada» son claves distintas por construcción.
    if any(run[field] is not None for field in IDENTITY_KEYS):
        payload.append([run[field] for field in IDENTITY_KEYS])
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def unclassified_metrics(catalogue=None) -> list[str]:
    """Identificadores del catálogo que no están ni en `HUMAN_METRICS` ni en `AUTOMATIC_METRICS`, ordenados.

    La tabla «Juicio humano o automático» se declara completa y se comprueba contra el catálogo (y no se
    deduce de él) porque la clasificación es una decisión de personas: si el catálogo de JUP-067 incorpora una
    métrica nueva, una prueba que exija `[]` avisa de que hay que decidir si es humana o automática antes de
    que sus filas lleguen al dashboard con un juicio por defecto equivocado. Un catálogo con menos métricas que
    las clasificadas no falla: lo que falta en el catálogo no es un error de clasificación. Con `catalogue=None`
    lee el de JUP-067 con `_load_catalogue` (resuelto al llamar, no al importar).
    """
    if catalogue is None:
        catalogue = _load_catalogue()
    classified = HUMAN_METRICS | AUTOMATIC_METRICS
    return sorted(metric["id"] for metric in catalogue["metrics"] if metric["id"] not in classified)


def classify_run_row(run) -> dict:
    """Copia de `run` con `is_real`, `non_real_reasons` y `comparability_key` añadidas al final.

    Es una copia (con `retrieval` copiado en profundidad) y no una mutación de `run` porque `rows-v1` rechaza
    las claves desconocidas: la ejecución original debe seguir siendo válida para `validate_rows`. `is_real`
    es un `bool` estricto (`not reasons`) y `non_real_reasons` una lista nueva en cada llamada, que es lo que
    espera la columna de la base y evita que dos filas compartan el mismo objeto mutable.
    """
    reasons = classify_run(run)
    row = copy.deepcopy(run)
    row["is_real"] = not reasons
    row["non_real_reasons"] = list(reasons)
    row["comparability_key"] = comparability_key(run, reasons)
    return row


# --- Normalización de entradas y subcomando rows ---------------------------------------------------------------

DEFAULT_MANIFEST = ROOT / "docs" / "validation" / "evaluation-runs.json"
DATASET_VERSION = 1
# Columnas de la ejecución que salen al conjunto de datos: las del contrato `rows-v1`, las tres de clasificación
# y las cuatro que añade la carga (formato, hito, ruta y huella del informe). Es una tupla porque el orden es
# parte del contrato de salida.
RUN_OUTPUT_KEYS = RUN_KEYS + CLASSIFICATION_KEYS + ("format", "milestone", "report_path", "report_sha256")

# Alfabeto de `report_path`: más estricto que el de los identificadores (sin `:=,+@`) porque la ruta se guarda
# tal cual en la base y en un script SQL, y un nombre con espacios o tildes no aporta nada que la huella no dé.
REPORT_PATH_RE = re.compile(r"[A-Za-z0-9._/-]+")
# `run_id` con el que los adaptadores devuelven la ejecución mientras no se conoce el definitivo: el derivado
# necesita la fecha y la huella, y la fecha solo la conoce el adaptador. Es un identificador válido para que
# `validate_rows` revise el resto de la ejecución antes de derivar nada.
PROVISIONAL_RUN_ID = "pendiente"
# Formatos cuyo `run_id` se deriva si la entrada no lo fija: los tres informes de los que el adaptador recibe el
# documento ya parseado. JUP-068 (lo lee Node) y `rows-v1` traen su propio `run_id`.
DERIVED_RUN_ID_FORMATS = ("jup-070-report-v1", "jup-078-benchmark-v1", "jup-022-calibration-v1", "jup-063-paired-v1")


def derive_run_id(source: str, run_at, report_sha256: str) -> str:
    """`run_id` derivado: `<fuente en minúsculas>-<AAAAMMDDThhmmssZ en UTC o undated>-<8 primeros hex>`.

    Es determinista (misma fuente, fecha y huella dan el mismo identificador) para que regenerar el conjunto de
    datos no cambie los `run_id` ya cargados. La fecha se pasa a UTC y se truncan las fracciones de segundo, sin
    redondear: redondear podría subir al segundo siguiente y dos informes del mismo segundo ya se distinguen por
    la huella. `run_at` ya viene validado (`validate_rows`), por lo que `fromisoformat` no puede fallar aquí.
    """
    if run_at is None:
        stamp = "undated"
    else:
        try:
            moment = datetime.fromisoformat(run_at).astimezone(timezone.utc)
        except OverflowError:
            # Un año 0001 con desfase positivo no cabe en UTC: se informa como dato inválido y no como traza.
            raise _bad("run.run_at", "la fecha no se puede pasar a UTC") from None
        # Campos numéricos y no `strftime`: `%Y` no rellena con ceros los años de menos de cuatro cifras en todas
        # las plataformas y el identificador cambiaría de una máquina a otra.
        stamp = (f"{moment.year:04d}{moment.month:02d}{moment.day:02d}"
                 f"T{moment.hour:02d}{moment.minute:02d}{moment.second:02d}Z")
    return f"{source.lower()}-{stamp}-{report_sha256[:8]}"


def report_digest(document) -> str:
    """sha256 del JSON canónico del documento YA PARSEADO (no de los bytes del fichero).

    Los bytes de un informe cambian según el fin de línea (`autocrlf` de Git en Windows), la sangría o el orden
    de las claves, y los `run_id` derivados llevan esta huella: tienen que ser iguales en todas las máquinas y no
    depender de cómo se guardó el fichero. Se serializa con claves ordenadas, separadores compactos y
    `ensure_ascii` (mismo criterio que `comparability_key`), así que dos documentos iguales dan siempre la misma
    huella y uno distinto (otro valor, otro tipo, otro orden de una lista) da otra.
    """
    text = json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _report_location(path, root) -> tuple[str, str | None]:
    # Devuelve (etiqueta para los errores, ruta relativa con barras si el informe cuelga de `root`, si no None).
    # Se comparan rutas RESUELTAS y por componentes (`relative_to`), no cadenas: un prefijo textual daría por
    # dentro `raiz-otra` respecto a `raiz`, y un `..` haría pasar por fuera un informe que está dentro.
    # Fuera de la raíz solo se usa el nombre del fichero: una ruta absoluta local puede llevar nombres de usuario
    # y estos mensajes acaban en registros de CI y en revisiones públicas.
    location = Path(path)
    try:
        relative = location.resolve().relative_to(Path(root).resolve())
    except (ValueError, OSError, RuntimeError):
        return _escape_control(location.name), None
    posix = relative.as_posix()
    return _escape_control(posix), posix


def _read_report(path) -> object:
    # Todo fallo de lectura o de JSON sale como AdapterError (el prefijo del fichero lo añade el llamador). Del
    # error del sistema solo se cita `strerror`: su texto completo repite la ruta absoluta, que aquí no debe salir.
    try:
        # utf-8-sig tolera el BOM de los editores de Windows sin alterar el UTF-8 normal (como en los manifiestos).
        text = Path(path).read_text(encoding="utf-8-sig")
    except OSError as error:
        raise _bad("report", f"no se puede leer el informe ({error.strerror or type(error).__name__})") from error
    except UnicodeDecodeError as error:
        raise _bad("report", f"no se puede leer el informe ({error})") from error
    try:
        return json.loads(text)
    except (ValueError, RecursionError) as error:
        raise _bad("report", f"JSON inválido ({error})") from error


def _adapt_entry(entry: dict, document) -> tuple[dict, list[dict]]:
    # Aplica el adaptador del formato. Con `run_id` explícito el adaptador ya lo recibe; sin él, los de JUP-070,
    # JUP-078 y JUP-022 devuelven uno provisional que `normalize_entry` sustituye por el derivado.
    fmt, explicit = entry["format"], entry["run_id"]
    if fmt == "rows-v1":
        # El formato trae su propio `run_id`; el de la entrada lo sustituye (un hito de un informe repetido).
        return adapt_rows_v1(document, run_id=explicit)
    if fmt == "jup-068-input-v1":
        # La entrada de JUP-068 no es el informe: lo genera Node, que ya trae un `run_id` (el del ejemplo versionado
        # lo declara). Por eso aquí el orden es explícito > informe, y no se deriva nunca.
        report = read_business_report(entry["path"])
        run_id = explicit if explicit is not None else report.get("run_id")
        if run_id is None:
            raise _bad("run_id", "el informe de negocio no trae run_id y la entrada del manifiesto tampoco")
        return adapt_jup068(report, run_id)
    run_id = PROVISIONAL_RUN_ID if explicit is None else explicit
    # Cadena de `if` y no una tabla `formato -> función`: la tabla guardaría las funciones al importar y un
    # cambio posterior de `adapt_*` (o un doble en las pruebas) no se vería; así siempre se llama a la actual.
    if fmt == "jup-070-report-v1":
        return adapt_jup070(document, run_id)
    if fmt == "jup-078-benchmark-v1":
        return adapt_jup078(document, run_id)
    if fmt == "jup-063-paired-v1":
        return adapt_jup063_paired(document, run_id)
    return adapt_jup022(document, run_id)


def _apply_model_identity(run: dict, annotation: dict) -> None:
    """Rellena en `run` la identidad que anota el manifiesto, solo donde el informe no trae nada.

    El informe es la fuente de verdad: si trae un valor distinto del anotado, es un conflicto y se nombra el
    campo con los dos valores. `run` ya está validado, así que su valor se puede citar; el anotado todavía no, y
    solo se cita si es una cadena corta de alfabeto cerrado (si no, lo informa la validación posterior con la
    ruta del campo y sin volcar el valor).
    """
    for key in IDENTITY_KEYS:
        if key not in annotation:
            continue
        declared = annotation[key]
        if run[key] is not None and run[key] != declared:
            shown = repr(declared) if _is_identifier(declared) else "(valor no válido)"
            raise _bad(f"model_identity.{key}", f"el informe declara {run[key]!r} y la anotación del manifiesto {shown}")
        run[key] = declared


def normalize_entry(entry, root=ROOT) -> dict:
    """Convierte una entrada de `read_manifest` en `{"run": {...}, "results": [...]}`.

    `run` tiene exactamente `RUN_OUTPUT_KEYS`. El `run_id` es, por orden, el explícito de la entrada, el del
    informe (JUP-068 y `rows-v1`) o el derivado de la fuente, la fecha y la huella. Todo fallo es un
    `AdapterError` que empieza por `<fichero>: `, con la ruta relativa a `root` si el informe cuelga de ella y solo
    el nombre en otro caso. Función sin efectos: solo lee el informe (y, en JUP-068, ejecuta Node).
    """
    label, report_path = _report_location(entry["path"], root)
    # `report_path` solo se guarda si el informe está dentro de la raíz del repositorio Y su ruta cumple el
    # alfabeto cerrado: una ruta local absoluta puede llevar nombres de usuario y una con espacios o tildes no es
    # un identificador seguro. En esos casos queda None y el informe se identifica solo por su huella.
    if report_path is not None and REPORT_PATH_RE.fullmatch(report_path) is None:
        report_path = None
    try:
        document = _read_report(entry["path"])
        run, results = _adapt_entry(entry, document)
        # Validación común SIEMPRE sobre la salida cruda del adaptador (también la de `rows-v1`, que ya la hizo):
        # los adaptadores copian valores sin comprobar su alfabeto y esta es la barrera que lo hace. Va antes de
        # derivar el `run_id` para que una fecha inadmisible sea un error de `run.run_at` y no un identificador.
        validate_rows(run, results)
        if entry.get("model_identity"):
            _apply_model_identity(run, entry["model_identity"])
            validate_rows(run, results)
        # Un informe sin filas es un error y no un conjunto vacío: lo más probable es un informe truncado o un
        # barrido sin puntos, y cargarlo en silencio dejaría una ejecución sin datos en el dashboard.
        if not results:
            raise _bad("results", "el informe no produce ninguna fila")
        digest = report_digest(document)
        if entry["run_id"] is None and entry["format"] in DERIVED_RUN_ID_FORMATS:
            run["run_id"] = derive_run_id(run["source"], run["run_at"], digest)
        # La clasificación se calcula sobre el `run` CRUDO: `rows-v1` rechaza las claves desconocidas, así que
        # clasificar después de añadir formato, hito, ruta y huella haría fallar la validación de `classify_run`.
        output_run = classify_run_row(run)
        output_run.update(format=entry["format"], milestone=entry["milestone"], report_path=report_path,
                          report_sha256=digest)
    except (AdapterError, ManifestError) as error:
        # ManifestError también: un fallo de un adaptador no debe escaparse con otro tipo, y la línea de comandos
        # solo trata los errores de datos. El mensaje original se conserva tal cual tras el prefijo.
        raise AdapterError(f"{label}: {error}") from error
    except RecursionError as error:
        raise AdapterError(f"{label}: el documento está demasiado anidado") from error
    return {"run": output_run, "results": results}


def build_dataset(manifest_paths, root=ROOT) -> dict:
    """Une los manifiestos en `{"dataset_version": 1, "runs": [...]}`, en el orden de los manifiestos dados.

    Es atómico: cualquier fallo (manifiesto, informe o `run_id` repetido) lanza la excepción sin devolver nada,
    para que la línea de comandos no deje un conjunto de datos a medias. `merge_manifests` ya rechaza el mismo
    informe o el mismo `run_id` explícito en dos entradas; aquí se detectan los choques que solo se ven al
    normalizar: la misma ejecución copiada a otro nombre (mismo contenido, mismo `run_id` derivado) o un `run_id`
    explícito igual al que trae otro informe.
    """
    runs = []
    owners: dict[str, str] = {}
    for entry in merge_manifests(list(manifest_paths), root=root):
        item = normalize_entry(entry, root=root)
        run_id = item["run"]["run_id"]
        label = _report_location(entry["path"], root)[0]
        if run_id in owners:
            raise _bad("run_id", f"{run_id!r} repetido en {label}; ya lo usa {owners[run_id]}")
        owners[run_id] = label
        runs.append(item)
    return {"dataset_version": DATASET_VERSION, "runs": runs}


# --- Generación del script SQL ---------------------------------------------------------------------------

SCHEMA_NAME = "evaluation"
# Máximo de tuplas por `INSERT` de resultados. Un único `INSERT` con miles de tuplas es válido, pero su tamaño
# crece sin límite con los informes; 500 mantiene cada sentencia pequeña (fácil de leer y de localizar en un
# error de `psql`) sin multiplicar los viajes: con los datos versionados cabe todo en un solo bloque.
INSERT_CHUNK = 500

# Clave del contrato -> columna de la base, en el orden del contrato. Son dicts (y no listas de pares) porque el
# script lee cada valor por clave y escribe la cabecera por columna desde la MISMA fuente: así el nombre y la
# posición no pueden divergir. Se derivan de las tuplas de claves existentes y solo se declara lo que cambia de
# nombre (`commit` es palabra reservada en SQL; `count` es una función agregada): si el contrato `rows-v1`
# añade una clave, la columna aparece aquí sola y el DDL de `SCHEMA_DDL` obliga a decidir su tipo.
_RENAMED_COLUMNS = {"commit": "commit_sha", "count": "case_count"}
RUN_COLUMNS = {key: _RENAMED_COLUMNS.get(key, key) for key in RUN_OUTPUT_KEYS}
RESULT_COLUMNS = {key: _RENAMED_COLUMNS.get(key, key) for key in RESULT_KEYS}
# `INSERT` de resultados lleva delante el `run_id` de la ejecución a la que pertenece cada fila.
RESULT_INSERT_COLUMNS = ("run_id",) + tuple(RESULT_COLUMNS.values())

# Esquema y tablas. Reglas de diseño (ADR-0022, `design.md` D4):
# * `IF NOT EXISTS` en todo: el script se puede ejecutar cuantas veces haga falta (regeneración idempotente).
# * `retrieval` es `jsonb` y no columnas sueltas: sus claves (`top_k`, `max_distance`...) dependen de la fuente
#   y de la versión del contrato, y `jsonb` conserva el objeto tal cual sin migrar la tabla cuando cambian.
# * Lo que el informe no trae es NULL (columnas sin NOT NULL); solo son obligatorias las que el contrato exige.
# * `evaluation.results` borra en cascada con su ejecución, y su clave primaria es la clave natural de la fila
#   (la que `validate_rows` ya garantiza única), de modo que la base y la herramienta rechazan lo mismo.
# * Las dos `CHECK` de tabla repiten en la base la regla 1 del contrato (lo no medido nunca es cero): un
#   `not_measured` no puede traer valor, numerador, recuento ni intervalo (el denominador SÍ se conserva) y un
#   `measured` siempre trae `value`. Se declaran como `CHECK` de tabla porque cruzan varias columnas. Es una
#   segunda barrera: si alguien carga filas por otra vía (un `INSERT` a mano), la base no admite un 0 inventado.
# * Sin comentarios SQL: el script se lee y se trocea por sentencias, y los porqués viven aquí, en Python.
SCHEMA_DDL = f"""\
CREATE SCHEMA IF NOT EXISTS {SCHEMA_NAME};

CREATE TABLE IF NOT EXISTS {SCHEMA_NAME}.runs (
  run_id text PRIMARY KEY,
  source text NOT NULL,
  run_at timestamptz,
  commit_sha text,
  suite text,
  suite_version text,
  suite_sha256 text,
  corpus_sha256 text,
  embedding_provider text,
  embedding_alias text,
  retrieval jsonb,
  generation_model text,
  prompt_sha256 text,
  synthetic boolean NOT NULL,
  generation_model_id text,
  generation_provider text,
  generation_quantization text,
  gateway_config_sha256 text,
  is_real boolean NOT NULL,
  non_real_reasons text[] NOT NULL,
  comparability_key text NOT NULL,
  format text NOT NULL,
  milestone boolean NOT NULL,
  report_path text,
  report_sha256 text NOT NULL
);

ALTER TABLE {SCHEMA_NAME}.runs ADD COLUMN IF NOT EXISTS generation_model_id text;
ALTER TABLE {SCHEMA_NAME}.runs ADD COLUMN IF NOT EXISTS generation_provider text;
ALTER TABLE {SCHEMA_NAME}.runs ADD COLUMN IF NOT EXISTS generation_quantization text;
ALTER TABLE {SCHEMA_NAME}.runs ADD COLUMN IF NOT EXISTS gateway_config_sha256 text;

CREATE TABLE IF NOT EXISTS {SCHEMA_NAME}.results (
  run_id text NOT NULL REFERENCES {SCHEMA_NAME}.runs (run_id) ON DELETE CASCADE,
  measure_type text NOT NULL CHECK (measure_type IN ('A', 'B')),
  grp text NOT NULL,
  metric_id text NOT NULL,
  behavior text NOT NULL,
  status text NOT NULL CHECK (status IN ('pass', 'fail', 'blocked', 'not_run', 'measured', 'not_measured')),
  case_count bigint,
  value double precision,
  unit text NOT NULL,
  numerator double precision,
  denominator bigint,
  ci_low double precision,
  ci_high double precision,
  judgment text CHECK (judgment IS NULL OR judgment IN ('automatic', 'human')),
  selected boolean NOT NULL DEFAULT false,
  PRIMARY KEY (run_id, grp, metric_id, behavior, status),
  CHECK (status <> 'not_measured' OR (value IS NULL AND numerator IS NULL AND case_count IS NULL
    AND ci_low IS NULL AND ci_high IS NULL)),
  CHECK (status <> 'measured' OR value IS NOT NULL)
);"""

# Vaciado previo a la carga. Va en la misma transacción que las inserciones: si algo falla, `ROLLBACK` deja los
# datos anteriores intactos y nunca se queda una base vacía o a medias (regeneración atómica); y como vacía todo
# y vuelve a cargar todo, ejecutarlo dos veces da el mismo resultado (idempotente). Es `TRUNCATE` y no `DROP`:
# el esquema, las tablas y los permisos que se concedan después (el rol de lectura de Grafana) sobreviven a cada
# regeneración. Las dos tablas van en UNA sentencia porque `results` referencia a `runs` y PostgreSQL no deja
# vaciar solo la referenciada; así tampoco hace falta `CASCADE`, que arrastraría tablas ajenas que algún día
# referencien estas.
TRUNCATE_SQL = f"TRUNCATE {SCHEMA_NAME}.results, {SCHEMA_NAME}.runs;"

# `standard_conforming_strings = on` hace que dentro de `'...'` la barra invertida sea un carácter normal, que es
# lo que supone `sql_literal` (solo duplica la comilla simple y no toca la barra). Sin esto, con el ajuste
# desactivado en el servidor o en el rol, `\\` o `\'` de un dato cambiarían de significado y abrirían una
# inyección. `SET LOCAL` y no `SET`: dura solo hasta el `COMMIT` y no deja la sesión alterada.
SESSION_SQL = "SET LOCAL standard_conforming_strings = on;"

# Vistas del panel (`design.md` D5 y D6). Se calculan en la base y no en el dashboard para que Grafana solo lea y
# para que la regla viva en UN sitio, probada contra un PostgreSQL real. Decisiones:
# * `CREATE OR REPLACE VIEW` y no `DROP VIEW` + `CREATE`: el script es idempotente sin destruir nada; un borrado
#   se llevaría por delante los permisos que se concedan después a la vista (el rol de lectura de Grafana, tarea
#   3.3) y rompería cualquier consulta abierta. Es además lo que exige `build_sql`, que no admite `DROP` en su DDL.
#   Limitación conocida: `CREATE OR REPLACE VIEW` no permite quitar ni reordenar columnas de una vista ya creada;
#   si el contrato de columnas cambiara habría que migrar a mano, no regenerar.
# * Vistas normales y no materializadas: la carga hace `TRUNCATE` + `INSERT` y una materializada se quedaría vieja
#   hasta el siguiente `REFRESH`, un paso más que se podría olvidar.
# * Solo cuentan las ejecuciones CON `run_at`: sin fecha no hay orden, así que no se puede decir cuál es la anterior
#   de cuál. Se filtran ANTES de calcular la anterior (y no después), para que una ejecución sin fecha ni aparezca
#   ni interrumpa la cadena de las demás. Sin ese filtro, `ORDER BY run_at` pondría los NULL al final (NULLS LAST)
#   y fabricaría pares falsos.
# * `ORDER BY run_at, run_id`: el instante (`timestamptz`, no el texto) y, a igualdad, el identificador, para que el
#   resultado no dependa del orden físico de las filas ni de la zona horaria de la sesión.
# * `config_changes` compara cada ejecución con la inmediatamente anterior DE LA MISMA `source` (`PARTITION BY
#   source`), no con la primera ni con otra fuente: así una vuelta a la configuración anterior cuenta como cambio.
# * `IS DISTINCT FROM` y no `<>` en batería, modelo y corpus: `<>` con un NULL da NULL (ni verdadero ni falso) y un
#   cambio de «sin dato» a «con dato» se perdería. Aquí la ausencia de dato frente a un valor SÍ es un cambio, y
#   dos NULL no lo son.
# * `prompt` es la excepción y exige las DOS huellas registradas y distintas: «prompt no registrado» no es un
#   cambio de prompt, es desconocimiento, y anotarlo sería inventar un dato (escenario «Prompt no registrado»).
#   Por eso tampoco se usa `IS DISTINCT FROM` ahí.
# * `changes` sale en el orden fijo batería, modelo, prompt, corpus (el de los `CASE`), no alfabético; la anotación
#   lo reutiliza con `array_to_string`, así que anotación y array no pueden divergir. Los `CASE` sin `ELSE` dan
#   NULL y `array_remove(..., NULL)` los descarta; un par sin cambios queda con el array vacío y se filtra.
# * `comparable_runs` cuenta las ejecuciones con fecha de cada clave de comparabilidad con una función de ventana
#   (`count(*) OVER (PARTITION BY comparability_key)`), no un `GROUP BY`: así cada fila conserva sus propias
#   columnas (`is_real`, `milestone`) y se queda con el tamaño de SU serie. Una clave con una sola ejecución con
#   fecha no aparece: de ahí sale el aviso «Sin datos: no hay con qué comparar» del panel (escenario «Una sola
#   ejecución comparable»), sin que el dashboard tenga que contar nada.
# * Nombres siempre cualificados con el esquema y sin comentarios SQL ni `;` dentro de cadenas: el script se trocea
#   por sentencias y los porqués viven aquí, en Python.
VIEWS_DDL = f"""\
CREATE OR REPLACE VIEW {SCHEMA_NAME}.config_changes AS
WITH ordered AS (
  SELECT
    run_id,
    source,
    run_at,
    suite_version,
    suite_sha256,
    generation_model,
    generation_model_id,
    generation_provider,
    generation_quantization,
    gateway_config_sha256,
    identity_registered,
    prompt_sha256,
    corpus_sha256,
    lag(run_id) OVER w AS previous_run_id,
    lag(suite_version) OVER w AS previous_suite_version,
    lag(suite_sha256) OVER w AS previous_suite_sha256,
    lag(generation_model) OVER w AS previous_generation_model,
    lag(generation_model_id) OVER w AS previous_generation_model_id,
    lag(generation_provider) OVER w AS previous_generation_provider,
    lag(generation_quantization) OVER w AS previous_generation_quantization,
    lag(gateway_config_sha256) OVER w AS previous_gateway_config_sha256,
    lag(identity_registered) OVER w AS previous_identity_registered,
    lag(prompt_sha256) OVER w AS previous_prompt_sha256,
    lag(corpus_sha256) OVER w AS previous_corpus_sha256
  FROM (
    SELECT
      runs.*,
      (generation_model_id IS NOT NULL OR generation_provider IS NOT NULL OR generation_quantization IS NOT NULL
        OR gateway_config_sha256 IS NOT NULL) AS identity_registered
    FROM {SCHEMA_NAME}.runs
  ) AS runs
  WHERE run_at IS NOT NULL
  WINDOW w AS (PARTITION BY source ORDER BY run_at, run_id)
),
detected AS (
  SELECT
    run_id,
    previous_run_id,
    source,
    run_at,
    array_remove(ARRAY[
      CASE WHEN suite_version IS DISTINCT FROM previous_suite_version
             OR suite_sha256 IS DISTINCT FROM previous_suite_sha256 THEN 'bateria'::text END,
      CASE WHEN generation_model IS DISTINCT FROM previous_generation_model THEN 'modelo'::text END,
      CASE WHEN identity_registered <> previous_identity_registered
             THEN 'identidad del modelo no registrada en una de las dos'::text END,
      CASE WHEN identity_registered AND previous_identity_registered
             AND generation_model_id IS DISTINCT FROM previous_generation_model_id THEN 'identificador de modelo'::text END,
      CASE WHEN identity_registered AND previous_identity_registered
             AND generation_provider IS DISTINCT FROM previous_generation_provider THEN 'proveedor del modelo'::text END,
      CASE WHEN identity_registered AND previous_identity_registered
             AND generation_quantization IS DISTINCT FROM previous_generation_quantization THEN 'cuantizacion'::text END,
      CASE WHEN identity_registered AND previous_identity_registered
             AND gateway_config_sha256 IS DISTINCT FROM previous_gateway_config_sha256 THEN 'configuracion del gateway'::text END,
      CASE WHEN prompt_sha256 IS NOT NULL AND previous_prompt_sha256 IS NOT NULL
             AND prompt_sha256 <> previous_prompt_sha256 THEN 'prompt'::text END,
      CASE WHEN corpus_sha256 IS DISTINCT FROM previous_corpus_sha256 THEN 'corpus'::text END
    ], NULL) AS changes
  FROM ordered
  WHERE previous_run_id IS NOT NULL
)
SELECT
  run_id,
  previous_run_id,
  source,
  run_at,
  changes,
  'Cambia: ' || array_to_string(changes, ', ') AS annotation
FROM detected
WHERE cardinality(changes) > 0;

CREATE OR REPLACE VIEW {SCHEMA_NAME}.comparable_runs AS
SELECT
  comparability_key,
  run_id,
  source,
  run_at,
  is_real,
  milestone,
  series_runs
FROM (
  SELECT
    comparability_key,
    run_id,
    source,
    run_at,
    is_real,
    milestone,
    count(*) OVER (PARTITION BY comparability_key) AS series_runs
  FROM {SCHEMA_NAME}.runs
  WHERE run_at IS NOT NULL
) AS dated
WHERE series_runs >= 2;"""

# Los bloques de DDL van en una tupla y no pegados dentro de `build_sql` para que las tareas siguientes (el rol de
# lectura) añadan su constante aquí, entre las vistas y el vaciado, sin tocar el orden del resto. El orden importa:
# esquema y tablas primero, porque una vista no se puede crear sobre una tabla que aún no existe; el `TRUNCATE`
# va después y no toca las vistas (solo vacía las tablas). Nunca llevan credenciales: la contraseña del rol viaja
# aparte (por la entrada estándar de `psql`), nunca en el texto de este script, que se imprime, se guarda con
# `--output` y se puede compartir.
DDL_BLOCKS = (SCHEMA_DDL, VIEWS_DDL)


class SqlError(ValueError):
    """Valor que no se puede escribir como literal SQL (NaN, infinito, NUL, tipo ajeno).

    Hereda de ValueError, como `AdapterError`, para que quien la capture la trate como un error de datos. La
    línea de comandos la muestra como `error: <mensaje>` con el código 1 y sin escribir nada.
    """


# Un NUL escapado dentro del texto JSON: `\u0000` precedido de un número PAR de barras (las barras de a pares
# son barras literales del dato y la `u` ya no es parte de un escape). Se busca en el texto serializado porque
# `json.dumps` escribe el NUL como `\u0000` y `jsonb` no lo admite; mirar solo `\u0000` daría un falso positivo
# con el dato `\u0000` escrito como texto, que se serializa `\\u0000`.
_JSON_NUL_RE = re.compile(r"(?<!\\)(?:\\\\)*\\u0000")


def _string_literal(text: str) -> str:
    # PostgreSQL no admite NUL en un `text`: se rechaza aquí con un error accionable en lugar de truncar el
    # dato en silencio o fallar a mitad de la transacción.
    if "\x00" in text:
        raise SqlError("el texto contiene un carácter NUL, que PostgreSQL no admite")
    # Con `standard_conforming_strings = on` solo la comilla simple es especial dentro de `'...'`, y se escapa
    # duplicándola. No se toca la barra invertida ni se usan cadenas `E'...'` ni `$$...$$`: una sola regla de
    # escape es más fácil de revisar que varias, y la prueba la invierte con un desescapador independiente.
    return "'" + text.replace("'", "''") + "'"


def _json_literal(value: dict) -> str:
    # Claves ordenadas, separadores compactos y `ensure_ascii`: el mismo JSON canónico que `report_digest`, para
    # que dos objetos iguales den el mismo texto (script reproducible) y el script sea ASCII puro, sin depender
    # de la codificación del terminal. `allow_nan=False` porque `NaN` no es JSON y `jsonb` lo rechazaría.
    try:
        text = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
    except (ValueError, TypeError, RecursionError) as error:
        # TypeError: tipo no serializable o claves de tipos mezclados que no se pueden ordenar.
        raise SqlError(f"el objeto no se puede escribir como jsonb ({type(error).__name__})") from error
    if _JSON_NUL_RE.search(text):
        raise SqlError("el objeto contiene un carácter NUL, que jsonb no admite")
    # La duplicación de comillas se aplica al JSON ya serializado: así una comilla dentro de una clave o un valor
    # no cierra la cadena SQL. No pasa por `_string_literal` porque el NUL ya se ha comprobado sobre el JSON.
    return "'" + text.replace("'", "''") + "'::jsonb"


def sql_literal(value) -> str:
    """Único camino por el que un valor entra en el script SQL: devuelve su literal escapado.

    `None` es `NULL`; `bool` es `TRUE`/`FALSE`; `int` y `float` salen en decimal (`repr` del float, la forma más
    corta que lo reconstruye exacto); `str` va entre comillas con las comillas duplicadas; una lista de cadenas
    es `ARRAY[...]::text[]`; un `dict` es `jsonb`. NaN, infinitos, NUL y cualquier otro tipo son `SqlError`.
    Se comparan tipos exactos (`type(x) is ...`) y `bool` va antes que `int` (es su subclase): un tipo ajeno o
    una subclase con otro `__repr__` no debe colarse en el texto SQL. Nunca se interpola un valor sin pasar por
    aquí; la alternativa descartada, parámetros del driver, exigiría una base y una dependencia (ADR-0022 D2).
    """
    kind = type(value)
    if value is None:
        return "NULL"
    if kind is bool:
        return "TRUE" if value else "FALSE"
    if kind is int:
        return str(value)
    if kind is float:
        if not math.isfinite(value):
            raise SqlError("un número no finito (NaN o infinito) no se puede escribir como literal SQL")
        return repr(value)
    if kind is str:
        return _string_literal(value)
    if kind is list:
        if not all(type(item) is str for item in value):
            raise SqlError("una lista solo se puede escribir como ARRAY de cadenas")
        # El cast es obligatorio: `ARRAY[]` sin tipo no es válido en PostgreSQL.
        return "ARRAY[" + ",".join(_string_literal(item) for item in value) + "]::text[]"
    if kind is dict:
        return _json_literal(value)
    raise SqlError(f"un valor de tipo {kind.__name__} no se puede escribir como literal SQL")


def _check_dataset_shape(dataset) -> list:
    if not isinstance(dataset, dict):
        raise _bad("dataset", "debe ser un objeto")
    for key in dataset:
        if key not in ("dataset_version", "runs"):
            raise _bad("dataset", f"clave desconocida {_key_label(key)!r}")
    # `type(...) is int`: `True` y `1.0` valen 1 en Python pero no son el entero 1 del contrato.
    version = dataset.get("dataset_version")
    if type(version) is not int or version != DATASET_VERSION:
        raise _bad("dataset", f"dataset_version debe ser {DATASET_VERSION}")
    runs = dataset.get("runs")
    if not isinstance(runs, list):
        raise _bad("dataset", "runs debe ser una lista")
    return runs


def _check_entry_shape(entry, where: str) -> tuple[dict, list]:
    if not isinstance(entry, dict):
        raise _bad(where, "debe ser un objeto")
    for key in entry:
        if key not in ("run", "results"):
            raise _bad(where, f"clave desconocida {_key_label(key)!r}")
    for key in ("run", "results"):
        if key not in entry:
            raise _bad(where, f"falta {key!r}")
    run, results = entry["run"], entry["results"]
    if not isinstance(run, dict):
        raise _bad(f"{where}.run", "debe ser un objeto")
    if not isinstance(results, list):
        raise _bad(f"{where}.results", "debe ser una lista")
    return run, results


def _validate_dataset(dataset) -> list[tuple[dict, list]]:
    # Se valida TODO antes de generar una sola línea: el script es una transacción única y un conjunto a medias
    # no debe producir texto. La forma exacta se comprueba aquí y la semántica de cada ejecución se delega en
    # `validate_rows` (la misma barrera que ya pasó al normalizar), con el prefijo `runs[i].` de su posición.
    pairs = []
    owners: dict[str, int] = {}
    for index, entry in enumerate(_check_dataset_shape(dataset)):
        where = f"runs[{index}]"
        run, results = _check_entry_shape(entry, where)
        # Claves exactas de la ejecución: una ausente dejaría un NULL donde la base exige NOT NULL, y una
        # desconocida se perdería sin avisar (el script solo escribe las columnas conocidas).
        for key in run:
            if key not in RUN_COLUMNS:
                raise _bad(f"{where}.run", f"clave desconocida {_key_label(key)!r}")
        for key in RUN_COLUMNS:
            if key not in run:
                raise _bad(f"{where}.run", f"falta {key!r}")
        try:
            # `validate_rows` solo conoce las claves del contrato `rows-v1`: se le pasa la ejecución reducida a
            # `RUN_KEYS` (sin las de clasificación y carga, que se escapan con `sql_literal`).
            validate_rows({key: run[key] for key in RUN_KEYS}, results)
        except AdapterError as error:
            raise AdapterError(f"{where}.{error}") from error
        # `validate_rows` ya garantiza que `run_id` es un identificador. La clave primaria distingue mayúsculas,
        # igual que este diccionario, así que `Run-1` y `run-1` no chocan.
        run_id = run["run_id"]
        if run_id in owners:
            raise _bad(f"{where}.run.run_id", f"{run_id!r} repetido; ya lo usa runs[{owners[run_id]}]")
        owners[run_id] = index
        pairs.append((run, results))
    return pairs


def _cell(key: str, value) -> str:
    literal = sql_literal(value)
    # `run_at` es una cadena ISO 8601 y la columna es `timestamptz`: el cast explícito evita depender del
    # formato de fecha de la sesión. Un NULL no lleva cast (`NULL::timestamptz` también valdría, pero no aporta).
    if key == "run_at" and value is not None:
        literal += "::timestamptz"
    return literal


def _tuple_line(keys, source: dict, prefix: tuple = ()) -> str:
    # Los valores se leen por clave en el orden de `RUN_COLUMNS`/`RESULT_COLUMNS` y no recorriendo el dict del
    # conjunto de datos: el orden de sus claves no puede alterar el script.
    cells = list(prefix) + [_cell(key, source[key]) for key in keys]
    return "  (" + ", ".join(cells) + ")"


def _insert_statement(table: str, columns, lines: list[str]) -> str:
    # Una tupla por línea: un cambio en una fila se ve como una sola línea en `git diff` y el error de `psql`
    # (que cita la sentencia) es localizable.
    return (f"INSERT INTO {SCHEMA_NAME}.{table} ({', '.join(columns)}) VALUES\n"
            + ",\n".join(lines) + ";")


def _insert_blocks(pairs: list[tuple[dict, list]]) -> list[str]:
    blocks = []
    if pairs:
        lines = [_tuple_line(RUN_COLUMNS, run) for run, _ in pairs]
        blocks.append(_insert_statement("runs", RUN_COLUMNS.values(), lines))
    # El troceado es sobre la lista GLOBAL de filas (todas las ejecuciones, en orden) y no por ejecución: así
    # el número de sentencias solo depende del total de filas y un bloque puede mezclar ejecuciones. Sin filas no
    # se emite ningún `INSERT` (un `VALUES` sin tuplas no es SQL válido).
    lines = [_tuple_line(RESULT_COLUMNS, row, (sql_literal(run["run_id"]),)) for run, results in pairs for row in results]
    for start in range(0, len(lines), INSERT_CHUNK):
        blocks.append(_insert_statement("results", RESULT_INSERT_COLUMNS, lines[start:start + INSERT_CHUNK]))
    return blocks


def build_sql(dataset) -> str:
    """Genera el script SQL transaccional que carga `dataset` (la salida de `build_dataset`) en `evaluation`.

    Función pura y determinista: solo produce texto (sin base, sin credenciales, sin red) y no muta el conjunto
    de datos. El script va en una sola transacción: `BEGIN`, `SET LOCAL standard_conforming_strings`, el DDL de
    `DDL_BLOCKS`, el `TRUNCATE`, las inserciones (ejecuciones y después resultados en bloques de `INSERT_CHUNK`)
    y `COMMIT`. Un conjunto inválido lanza `AdapterError` (`dataset: `, `runs[i]: ` o `runs[i].<campo>: `) y un
    valor no escribible, `SqlError`; en ambos casos no se devuelve texto parcial.
    """
    pairs = _validate_dataset(dataset)
    # Fuente única del orden de las secciones: las tareas siguientes añaden bloques a `DDL_BLOCKS`.
    blocks = ["BEGIN;", SESSION_SQL, *DDL_BLOCKS, TRUNCATE_SQL, *_insert_blocks(pairs), "COMMIT;"]
    # Línea en blanco entre bloques para que sea legible; un solo `\n` final, sin línea vacía tras `COMMIT;`.
    return "\n\n".join(blocks) + "\n"


def build_comparison_sql(dataset) -> str:
    """Proyecta SOLO el informe pareado en una base evaluation ya existente.

    No crea/migra esquema, no cambia permisos, no vacía otras ejecuciones. La
    repetición del mismo informe reemplaza sus mismas filas en una transacción.
    Un run_id preexistente con otra huella/fuente no se borra: el INSERT colisiona
    con su PK y aborta TODO (psql debe usar ON_ERROR_STOP=1). No es un importador
    genérico ni una sustitución silenciosa del modo histórico de carga.
    """
    pairs = _validate_dataset(dataset)
    if len(pairs) != 1:
        raise SqlError("comparison: se requiere exactamente un informe pareado")
    run, rows = pairs[0]
    digest = run["report_sha256"]
    if (run["source"] != "JUP-063" or run["format"] != "jup-063-paired-v1"
            or not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None
            or run["run_id"] != derive_run_id(run["source"], run["run_at"], digest)
            or {r["behavior"] for r in rows} != set(PAIRED_MODELS)
            or any(r["grp"] != "paired_local_provisional" for r in rows)):
        raise SqlError("comparison: solo admite el informe JUP-063 con identidad derivada y sus dos modelos")
    # Borrado acotado por identidad COMPLETA, no por el prefijo de 8 caracteres.
    # El caso de colisión no elimina nada; el INSERT posterior aborta por PK.
    predicate = (f"run_id = {sql_literal(run['run_id'])} AND source = 'JUP-063' "
                 f"AND report_sha256 = {sql_literal(digest)}")
    blocks = [
        "BEGIN;", SESSION_SQL,
        f"DELETE FROM {SCHEMA_NAME}.results WHERE run_id IN "
        f"(SELECT run_id FROM {SCHEMA_NAME}.runs WHERE {predicate});",
        f"DELETE FROM {SCHEMA_NAME}.runs WHERE {predicate};",
        *_insert_blocks(pairs), "COMMIT;",
    ]
    return "\n\n".join(blocks) + "\n"


def _write_atomically(target: Path, text: str) -> None:
    # Se escribe a un fichero temporal del MISMO directorio y se renombra al final: `os.replace` es atómico en el
    # mismo sistema de ficheros, así que una interrupción o un error de disco nunca deja un `--output` truncado ni
    # pisa el anterior. En bytes UTF-8 y no en modo texto para que el fin de línea sea `\n` en todas las
    # plataformas y el fichero versionado no cambie de una máquina a otra.
    handle, temporary = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".tmp", dir=target.parent)
    try:
        with os.fdopen(handle, "wb") as stream:
            stream.write(text.encode("utf-8"))
        os.replace(temporary, target)
    except BaseException:
        # Se limpia el temporal también ante Ctrl+C; la excepción sigue su camino.
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


# --- Carga a PostgreSQL y rol de solo lectura ----------------------------------------------------------

# Rol con el que Grafana lee el esquema `evaluation`. Es un nombre fijo y no un parámetro: el datasource aprovisionado
# de Grafana y las pruebas lo citan por este nombre, y un rol configurable abriría la puerta a darle permisos al que no toca.
READER_ROLE = "grafana_evaluation_reader"
# Variable de entorno de la que `load` lee la contraseña del rol. Nunca se acepta como argumento de la línea de
# comandos: un argumento queda en el historial del shell y en la lista de procesos.
PASSWORD_ENV = "GRAFANA_EVALUATION_DB_PASSWORD"
# `PGCLIENTENCODING=UTF8` va DENTRO del comando (`-e` de `docker compose exec`) y también en el entorno de la llamada
# (ver `run_load`): el primero llega al `psql` del contenedor y el segundo al cliente local. Sin él `psql` usaría la
# página de códigos del sistema y una contraseña con tildes llegaría corrupta. Tupla y no lista: es una constante
# de todo el proceso y un llamador no debe poder alterarla.
DEFAULT_PSQL_COMMAND = ("docker", "compose", "exec", "-T", "-e", "PGCLIENTENCODING=UTF8", "postgres-pgvector",
                        "psql", "-U", "postgres", "-d", "embeddings")
# `ON_ERROR_STOP=1`: sin él `psql` seguiría tras el primer fallo y el rol se crearía con los datos a medias. `-X`: un
# `~/.psqlrc` del usuario no puede alterar la sesión. `-q`: sin ruido de `COMMIT`/`NOTICE` en la salida.
PSQL_FLAGS = ("-v", "ON_ERROR_STOP=1", "-X", "-q")
# Plazo máximo de `psql`, en segundos: evita que una base colgada o un `docker compose` esperando bloqueen la carga.
LOAD_TIMEOUT = 120
# Longitud máxima de la contraseña y del detalle de un error de `psql` que se cita en un mensaje.
PASSWORD_MAX_LENGTH = 200
ERROR_DETAIL_LIMIT = 300
# Con lo que se tapa la contraseña en los mensajes de error.
REDACTION = "***"


class LoadError(ValueError):
    """Fallo de la carga: contraseña no válida o `psql` que no se pudo ejecutar o terminó mal.

    Hereda de ValueError como el resto de errores de la herramienta, pero NO de `AdapterError`, `ManifestError` ni
    `SqlError`: quien capture los errores de datos no debe tragarse un fallo de infraestructura sin querer. Los
    mensajes de contraseña empiezan por `password: ` y los de ejecución por `load: `; ninguno cita la contraseña.
    """


def _check_password(password) -> None:
    # Cada mensaje dice QUÉ regla incumple y nunca el valor: la contraseña es un secreto y un mensaje de error acaba
    # en la terminal, en los registros de CI y en los informes de fallos.
    # `type(...) is str` y no `isinstance`: una subclase de `str` podría redefinir `__repr__` o `__len__` y colar
    # texto distinto del que se escribe en el script.
    if type(password) is not str:
        raise LoadError("password: debe ser una cadena de texto")
    if not password:
        raise LoadError("password: no puede estar vacía")
    # La longitud se mide en caracteres y no en bytes: 200 `ñ` son una contraseña válida.
    if len(password) > PASSWORD_MAX_LENGTH:
        raise LoadError(f"password: no puede tener más de {PASSWORD_MAX_LENGTH} caracteres")
    # Categoría Unicode `Cc` (los `\n`, `\r`, `\t`, NUL, ESC y DEL del contrato): un salto de línea partiría la línea
    # que `psql` repite al fallar y un NUL no cabe en un `text` de PostgreSQL.
    if any(unicodedata.category(char) == "Cc" for char in password):
        raise LoadError("password: no puede contener caracteres de control")
    # `os.environ` en Linux devuelve los bytes inválidos como sustitutos sueltos (`\udcff`), que no se pueden
    # codificar en UTF-8. Se rechaza aquí con un error accionable en lugar de dejar escapar un `UnicodeEncodeError`
    # crudo (una traza) al preparar los bytes de la entrada de `psql`.
    try:
        password.encode("utf-8")
    except UnicodeEncodeError:
        raise LoadError("password: contiene caracteres que no se pueden codificar en UTF-8") from None


def build_role_sql(password) -> str:
    """Genera el script SQL del rol de solo lectura de Grafana, con la contraseña dada.

    Va en un script APARTE del de `build_sql` a propósito: ese es reproducible, se imprime, se guarda con `--output`
    y se comparte, así que no puede contener credenciales ni `GRANT`. Este, en cambio, lleva la contraseña y solo
    existe en memoria y en la entrada estándar de `psql`. Función pura y determinista (la contraseña es el
    argumento: no lee el entorno). Una contraseña no válida lanza `LoadError` con prefijo `password: `.

    Es una transacción propia con nueve sentencias; el orden importa:

    1. `BEGIN`, y `SET LOCAL standard_conforming_strings = on` ANTES de cualquier literal: `sql_literal` escapa
       suponiendo que la barra invertida es un carácter normal, y esa suposición debe cumplirse en esta sesión.
    2. Un bloque `DO` que crea el rol solo si no está en `pg_roles`. `CREATE ROLE` no tiene `IF NOT EXISTS`, así que
       un `CREATE ROLE` a secas haría fallar toda segunda carga (y, con `ON_ERROR_STOP`, la dejaría a medias).
       Alternativa descartada: capturar la excepción `duplicate_object`; mirar el catálogo es más explícito.
    3. `ALTER ROLE ... WITH LOGIN PASSWORD`, SIEMPRE y no solo al crear: así una segunda carga rota la contraseña, y
       un rol preexistente (creado a mano, o sin `LOGIN`) queda adoptado con el estado que declara este script.
    4. Los permisos mínimos para leer el dashboard y nada más: `CONNECT` a la base, `USAGE` del esquema, `SELECT` de
       las tablas y vistas existentes y `ALTER DEFAULT PRIVILEGES` para que las que se creen después (las vistas de
       las tareas siguientes) nazcan ya legibles. Los privilegios por defecto aplican a los objetos que cree el rol
       que ejecuta `load`, que es el mismo que crea el esquema en el script de datos. Sin `INSERT`, `UPDATE`,
       `DELETE`, `TRUNCATE`, `CREATE` ni pertenencia a otros roles: Grafana solo consulta.
    """
    _check_password(password)
    # `sql_literal` es el único camino por el que un valor entra en el SQL: la contraseña no se interpola a mano.
    role = READER_ROLE
    blocks = [
        "BEGIN;",
        SESSION_SQL,
        f"DO $$\nBEGIN\n"
        f"  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = {sql_literal(role)}) THEN\n"
        f"    CREATE ROLE {role} LOGIN;\n"
        f"  END IF;\n"
        f"END\n$$;",
        f"ALTER ROLE {role} WITH LOGIN PASSWORD {sql_literal(password)};",
        f"GRANT CONNECT ON DATABASE embeddings TO {role};",
        f"GRANT USAGE ON SCHEMA {SCHEMA_NAME} TO {role};",
        f"GRANT SELECT ON ALL TABLES IN SCHEMA {SCHEMA_NAME} TO {role};",
        f"ALTER DEFAULT PRIVILEGES IN SCHEMA {SCHEMA_NAME} GRANT SELECT ON TABLES TO {role};",
        "COMMIT;",
    ]
    return "\n\n".join(blocks) + "\n"


def load_command(psql_command=None) -> list[str]:
    """Comando completo de `psql`: el comando dado (o el de por defecto) seguido de `PSQL_FLAGS`.

    Devuelve siempre una lista nueva: ni el resultado comparte estado con las constantes ni la entrada se muta.
    """
    command = list(DEFAULT_PSQL_COMMAND if psql_command is None else psql_command)
    # Un comando vacío ejecutaría las opciones de `psql` como si fueran el programa: se rechaza con un error claro.
    if not command:
        raise LoadError("load: el comando de psql no puede estar vacío")
    return command + list(PSQL_FLAGS)


def _redact(text: str, password: str) -> str:
    # `psql` repite en `stderr` la sentencia que falla, y la del rol lleva la contraseña; por eso se tapa en TODO
    # mensaje de error. Se tapan las dos formas en las que puede salir: la literal y la del literal SQL (comillas
    # dobladas). Una sola pasada con la alternancia más larga primero, y `re.escape` para que `.` o `(` de la
    # contraseña se traten como texto y no como expresión regular.
    forms = sorted({password.replace("'", "''"), password}, key=len, reverse=True)
    return re.sub("|".join(re.escape(form) for form in forms), REDACTION, text)


def _safe_detail(text: str, password: str) -> str:
    # El orden es parte de la seguridad: PRIMERO se tapa la contraseña y DESPUÉS se escapan los caracteres de
    # control y se recorta a 300. Recortar antes dejaría un trozo de la contraseña pegado al corte, y escapar antes
    # podría alterar la contraseña (un carácter de formato no imprimible) e impedir que se reconozca.
    detail = _escape_control(_redact(text, password))
    return detail if len(detail) <= ERROR_DETAIL_LIMIT else detail[:ERROR_DETAIL_LIMIT] + "..."


def _last_line(stderr) -> str:
    # `errors="replace"`: un byte inválido sale como U+FFFD y no como una excepción. Se quitan los `\r` (Windows) y
    # se toma la última línea NO vacía, que es la que dice qué falló (las anteriores son contexto de `psql`).
    text = (stderr or b"").decode("utf-8", errors="replace").replace("\r", "")
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    return lines[-1] if lines else ""


def _loaded_summary(dataset: dict) -> str:
    # Las cuentas salen del conjunto de datos (que `build_sql` ya validó) y no de lo que `psql` diga: con `-q` no
    # dice nada, y así el resumen no depende de la versión del cliente. «ejecuciones» no cambia con una sola:
    # un mensaje fijo es más fácil de comprobar y de analizar en un script.
    runs = dataset["runs"]
    return f"{len(runs)} ejecuciones y {sum(len(entry['results']) for entry in runs)} resultados cargados"


def run_load(dataset, password, psql_command=None, timeout=LOAD_TIMEOUT) -> str:
    """Carga `dataset` y crea o actualiza el rol de Grafana ejecutando `psql`; devuelve el resumen de lo cargado.

    Concatena el script de datos (`build_sql`) y el del rol (`build_role_sql`), en ese orden, y los pasa a `psql`
    por la entrada estándar como bytes UTF-8. Son dos transacciones separadas por una línea en blanco: el rol
    concede permisos sobre un esquema que el script de datos acaba de crear, y el `COMMIT` de los datos queda firme
    aunque el rol falle. Con `ON_ERROR_STOP` el primer fallo detiene la carga y lo anterior queda como estaba.

    Todo se valida ANTES de lanzar `psql`: un conjunto o una contraseña no válidos no envían ni un byte. Los fallos
    de ejecución son siempre `LoadError` con prefijo `load: `, con la contraseña tapada.
    """
    # Se buscan por nombre en cada llamada (no se guardan al importar) para usar siempre las actuales.
    data_sql = build_sql(dataset)
    role_sql = build_role_sql(password)
    command = load_command(psql_command)
    # La contraseña solo viaja por la entrada estándar: ni en los argumentos (se verían en la lista de procesos) ni
    # en el entorno. `main` la lee de `os.environ`, así que se QUITA de la copia que hereda `psql`, sin tocar el
    # entorno del propio proceso (una segunda llamada la necesita).
    env = dict(os.environ)
    env.pop(PASSWORD_ENV, None)
    env["PGCLIENTENCODING"] = "UTF8"
    # Bytes y no modo texto: la codificación es explícita (UTF-8, para que la contraseña llegue intacta) y no hay
    # traducción de saltos de línea. Sin `shell`: la lista de argumentos no pasa por un intérprete que pueda expandir
    # nada. `cwd=ROOT` porque `docker compose` busca ahí el `docker-compose.yml` del proyecto.
    try:
        completed = subprocess.run(
            command, input=(data_sql + "\n" + role_sql).encode("utf-8"), capture_output=True, timeout=timeout,
            cwd=ROOT, env=env,
        )
    except subprocess.TimeoutExpired:
        raise LoadError(f"load: timeout de {timeout} s esperando a psql") from None
    except FileNotFoundError:
        raise LoadError(f"load: no se encuentra el ejecutable {_safe_detail(command[0], password)}") from None
    except OSError as error:
        # `OSError` cubre también `PermissionError` y `BrokenPipeError` (tubería rota al escribir la entrada). Solo
        # se capturan fallos de ejecución: un `RuntimeError` es un error de programación y debe verse tal cual.
        # `from None`: encadenar el error original dejaría su mensaje, que puede llevar la contraseña, en la traza.
        raise LoadError(f"load: no se puede ejecutar {_safe_detail(command[0], password)}: "
                        f"{_safe_detail(str(error), password)}") from None
    if completed.returncode != 0:
        detail = _safe_detail(_last_line(completed.stderr), password)
        raise LoadError(f"load: psql terminó con código {completed.returncode}" + (f": {detail}" if detail else ""))
    return _loaded_summary(dataset)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="evaluation-dashboard.py",
        description="Prepara los resultados de evaluación del asistente para el dashboard de Grafana (JUP-121).",
    )
    # Opciones comunes en parsers padre (`add_help=False` para que cada subcomando conserve su propio `--help`):
    # `rows`, `sql` y `load` leen exactamente los mismos manifiestos, y declararlas tres veces dejaría que
    # divergieran. Alternativa descartada: una función que repita `add_argument` en cada subparser; el padre es el
    # mecanismo de `argparse` para esto.
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--manifest", action="append", default=[], type=Path, metavar="RUTA",
                        help="manifiesto local que se añade después del versionado (repetible)")
    common.add_argument("--no-versioned", action="store_true",
                        help="no lee el manifiesto versionado (docs/validation/evaluation-runs.json)")
    common.add_argument("--root", type=Path, default=ROOT, metavar="DIR",
                        help="raíz que resuelve las rutas relativas de los manifiestos y el report_path "
                             "(por defecto, la raíz del repositorio)")
    # `--output` va en un padre APARTE: solo tiene sentido en `rows` y `sql`, que imprimen un texto. `load` escribe
    # en la base y su única salida es un resumen de una línea, así que aceptar `--output` ahí sería una opción que
    # no hace nada (o que guarda un resumen sin interés). Que sea un error de uso evita el malentendido.
    output = argparse.ArgumentParser(add_help=False)
    output.add_argument("--output", type=Path, metavar="FICHERO",
                        help="escribe el resultado en este fichero en lugar de la salida estándar")
    # `required=True`: sin subcomando argparse termina con el código 2 de error de uso, el mismo que una opción
    # desconocida, y no hay un comportamiento por defecto que adivinar.
    commands = parser.add_subparsers(dest="command", required=True, metavar="comando")
    commands.add_parser(
        "rows", parents=[common, output],
        help="imprime el conjunto de datos normalizado (JSON) de los informes del manifiesto",
        description="Normaliza los informes de los manifiestos al contrato de filas planas y los imprime como JSON.",
    )
    sql = commands.add_parser(
        "sql", parents=[common, output], help="imprime el script SQL transaccional que carga ese conjunto de datos",
        description="Genera el script SQL (esquema, vaciado y carga en una transacción) del conjunto de datos "
                    "normalizado. No se conecta a ninguna base ni contiene credenciales.",
    )
    sql.add_argument("--preserve-existing", action="store_true",
                     help="solo comparación JUP-063: reemplaza su run_id sin DDL, roles ni vaciar otros datos; "
                          "requiere --no-versioned y manifiesto suplementario")
    load = commands.add_parser(
        "load", parents=[common],
        help="carga el conjunto de datos en PostgreSQL y crea o actualiza el rol de solo lectura de Grafana",
        description="Carga el conjunto de datos normalizado en la base con `psql` (el script se pasa por la entrada "
                    "estándar) y crea o actualiza el rol de solo lectura de Grafana. La contraseña del rol se lee "
                    f"de la variable de entorno {PASSWORD_ENV} y nunca se acepta como argumento ni se imprime.",
    )
    load.add_argument("--psql-command", metavar="COMANDO",
                      help="comando que ejecuta `psql`, partido como lo haría un shell POSIX; las opciones de "
                           "`psql` se añaden detrás (por defecto, `docker compose exec` sobre postgres-pgvector)")
    return parser


def _render_rows(dataset: dict) -> str:
    return json.dumps(dataset, indent=2, ensure_ascii=True) + "\n"


def _render_sql(dataset: dict) -> str:
    # `build_sql` se busca por nombre en cada llamada (no se guarda la función en una tabla al importar), como en
    # `_adapt_entry`: así siempre se usa la actual.
    return build_sql(dataset)


def _write_stdout(text: str) -> None:
    # La salida estándar se escribe como bytes UTF-8 por `.buffer`, sin pasar por la capa de texto: en
    # Windows `sys.stdout.write` traduciría `\n` a `\r\n` y la huella de la salida dejaría de coincidir con
    # la del fichero de `--output` (bytes con `\n`) y con la de Linux. Es el mismo contrato de
    # reproducibilidad byte a byte para ambas vías. Alternativa descartada: `reconfigure(newline="\n")`,
    # que muta el flujo global del proceso y no existe en objetos sustituidos como `io.StringIO`.
    buffer = getattr(sys.stdout, "buffer", None)
    if buffer is None:
        # Flujo sin capa binaria (`io.StringIO`, `redirect_stdout` en procesos que embeben `main`):
        # no hay traducción de saltos que evitar, así que se escribe el texto tal cual.
        sys.stdout.write(text)
    else:
        # Se vacía antes la capa de texto para no intercalar escrituras pendientes con los bytes.
        sys.stdout.flush()
        buffer.write(text.encode("utf-8"))
        buffer.flush()


def _split_psql_command(parser: argparse.ArgumentParser, text):
    # `None` es «sin `--psql-command`»: `run_load` usa entonces el comando por defecto. Se parte con `shlex` en modo
    # POSIX para que las comillas agrupen y se quiten (`split()` las dejaría dentro del argumento) y el resultado
    # sea una LISTA: así se ejecuta sin shell y la línea no puede inyectar nada. En Windows hay que escribir las
    # rutas con barras normales: la barra invertida es un escape en modo POSIX.
    if text is None:
        return None
    try:
        command = shlex.split(text)
    except ValueError as error:
        parser.error(f"--psql-command: {error}")
    # Un comando vacío (`--psql-command ""`) es un error de uso y no «usa el de por defecto»: quien lo escribe
    # quería otro comando, y ejecutar el de por defecto contra una base que no eligió sería una sorpresa peligrosa.
    if not command:
        parser.error("--psql-command: el comando no puede estar vacío")
    return command


# Opciones que esperan un valor. Se declaran como constante junto al parser (y no se derivan de `parser._actions`,
# que es API privada de `argparse`): si se añade una opción con valor hay que apuntarla aquí, y el test del `--`
# fija las cuatro actuales.
_VALUE_OPTIONS = ("--manifest", "--root", "--output", "--psql-command")


def _drop_pnpm_double_dash(argv: list) -> list:
    """Quita UN `--` suelto (el primero exacto) que pnpm reenvía al script.

    pnpm 9 pasa el `--` literal al script (`pnpm x -- --opt` ejecuta `x "--" "--opt"`) y `argparse` trataría lo
    siguiente como posicional. La herramienta no tiene argumentos posicionales, así que ignorarlo no pierde nada.
    Se respeta el `--` que sigue a una opción con valor: ahí `argparse` responde «expected one argument» y quitarlo
    convertiría `--manifest -- RUTA` en `--manifest RUTA`, ocultando un error de uso. Solo se quita el primero: un
    segundo `--` sigue siendo un error de uso, y un `--` pegado a otro texto (`--x`, `---`) no es este argumento.
    """
    for index, argument in enumerate(argv):
        if argument == "--":
            if index > 0 and argv[index - 1] in _VALUE_OPTIONS:
                return argv
            return argv[:index] + argv[index + 1:]
    return argv


def main(argv=None) -> int:
    """Línea de comandos. Devuelve 0 si todo fue bien y 1 ante un error de datos o de carga; el 2 lo da `argparse`."""
    parser = _build_parser()
    # Con `argv=None` `argparse` lee `sys.argv[1:]`; se materializa aquí para poder filtrar el `--` de pnpm.
    args = parser.parse_args(_drop_pnpm_double_dash(list(sys.argv[1:] if argv is None else argv)))
    password = command = None
    if args.command == "load":
        # La contraseña se mira ANTES de leer ningún manifiesto o lanzar nada: sin ella no hay nada que hacer, y el
        # error la nombra para que quien lo ve sepa qué variable falta. Una variable vacía cuenta como ausente.
        # Se pasa tal cual, sin recortar: los espacios al borde pueden ser parte de la contraseña.
        password = os.environ.get(PASSWORD_ENV)
        if not password:
            print(f"error: falta la variable de entorno {PASSWORD_ENV}", file=sys.stderr)
            return 1
        # También se VALIDA (longitud, caracteres de control, sustitutos) antes de leer nada: `run_load` solo lo hace
        # al construir el script del rol, es decir después de leer los manifiestos y montar el conjunto de datos, y
        # una contraseña inválida quedaba tapada por un error de manifiesto (o tras un trabajo inútil). Se llama a
        # `_check_password` y no a `build_role_sql` (descartando el resultado) para no generar un script que lleva
        # el secreto solo para tirarlo. `run_load` conserva su orden interno (datos antes que contraseña): sigue
        # siendo la defensa de quien lo use como biblioteca. El mensaje es el de `LoadError` (`password: ...`) y no
        # cita el valor.
        try:
            _check_password(password)
        except LoadError as error:
            print(f"error: {error}", file=sys.stderr)
            return 1
        command = _split_psql_command(parser, args.psql_command)
    manifests = ([] if args.no_versioned else [DEFAULT_MANIFEST]) + args.manifest
    try:
        dataset = build_dataset(manifests, root=args.root)
        if args.command == "load":
            # Solo se escribe el resumen si la carga acaba bien: un fallo sale por `stderr` y no deja salida.
            _write_stdout(run_load(dataset, password, psql_command=command) + "\n")
            return 0
        # Se genera el texto ANTES de tocar `--output`: si algo falla no se crea ni se modifica el fichero.
        if args.command == "sql" and args.preserve_existing:
            text = build_comparison_sql(dataset)
        else:
            text = _render_rows(dataset) if args.command == "rows" else _render_sql(dataset)
        if args.output is None:
            _write_stdout(text)
        else:
            _write_atomically(args.output, text)
    except (AdapterError, ManifestError, SqlError, LoadError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    except OSError as error:
        # `--output` en un directorio inexistente o sin permisos: error del entorno, no una traza.
        print(f"error: no se puede escribir la salida ({error.strerror or type(error).__name__})", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
