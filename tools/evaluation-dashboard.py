"""Carga de los resultados de evaluación del asistente en la base del dashboard de Grafana (JUP-121).

Por ahora este módulo contiene la capa de manifiestos: lee y valida los manifiestos que dicen qué
informes alimentan el dashboard (`docs/validation/evaluation-runs.json` y los locales). Usa solo la
biblioteca estándar, no tiene efectos al importarse y nunca abre una conexión de red ni a la base de
datos. Los adaptadores de informes y la carga a la base los añaden las tareas siguientes del change.
"""

from __future__ import annotations

import json
import re
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
