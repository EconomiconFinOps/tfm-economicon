"""Carga de los resultados de evaluación del asistente en la base del dashboard de Grafana (JUP-121).

Por ahora este módulo contiene tres capas. La primera es la de manifiestos: lee y valida los manifiestos
que dicen qué informes alimentan el dashboard (`docs/validation/evaluation-runs.json` y los locales). La
segunda es el adaptador del informe JSON de JUP-070 (`adapt_jup070`), que normaliza ese informe al
contrato de filas planas `rows-v1` de `docs/validation/evaluation-dashboard.md`. La tercera es el
adaptador del benchmark de modelos de JUP-078 (`adapt_jup078`), que produce el mismo contrato a partir
del informe de `tools/llm-benchmark.py`. Usa solo la biblioteca estándar, no tiene efectos al importarse
y nunca abre una conexión de red ni a la base de datos. Los demás adaptadores y la carga a la base los
añaden las tareas siguientes del change.
"""

from __future__ import annotations

import copy
import json
import math
import re
from datetime import datetime
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
)
# Regla 3 del contrato: los identificadores no pueden ser texto libre (un enunciado de pregunta, por
# ejemplo). Se admite solo un alfabeto cerrado de hasta 80 caracteres. El patrón conserva `$` porque es
# el literal del contrato, pero `$` también casa antes de un salto de línea final; por eso SIEMPRE se
# valida con `fullmatch` (ver `_is_identifier`) y así "abc\n" se rechaza sin tocar el patrón.
IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:=,/+@-]{0,79}$")

ROOT_KEYS = {"manifest_version", "runs"}
ENTRY_KEYS = {"path", "format", "milestone", "run_id"}


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
    return {"path": raw_path, "format": fmt, "milestone": milestone, "run_id": run_id, "manifest": manifest}


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
RUN_KEYS = (
    "run_id", "source", "run_at", "commit", "suite", "suite_version", "suite_sha256", "corpus_sha256",
    "embedding_provider", "embedding_alias", "retrieval", "generation_model", "prompt_sha256", "synthetic",
)
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
            raise _bad(f"metrics.{metric_id}", "métrica desconocida (no está en el catálogo de JUP-067)")
        _check_object(data, f"metrics.{metric_id}")
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
    return type(value) in (int, float) and math.isfinite(value)


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
