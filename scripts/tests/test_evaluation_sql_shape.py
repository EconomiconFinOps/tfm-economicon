"""Prefijos exactos de los errores de forma de `build_sql` (JUP-121, tarea 3.1, remediación de mutación).

Las pruebas de `test_evaluation_sql.py` solo exigen que el error de forma EMPIECE por `runs[i]`. Eso deja vivos los
mutantes que alteran la ruta del campo (`runs[i].resultsXX`, `runs[i].runXX`...) o que sustituyen un `raise` por
`pass`. Aquí se fija el prefijo exacto `<ruta>: ` de cada error de forma del conjunto de datos, de la entrada y de la
ejecución, y el contenido relevante del mensaje (`clave desconocida`, `falta`, el índice del propietario del
`run_id`). Todas las pruebas usan `AdapterError` y `startswith` con el prefijo completo, incluidos los dos puntos y
el espacio, para que un sufijo añadido a la ruta (`resultsXX: `) no pase por casualidad.

La ruta de la herramienta se puede sustituir con `EVALUATION_DASHBOARD_TOOL` para apuntar a una copia mutada.
"""
from __future__ import annotations

import copy
import importlib.util
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL_PATH = Path(os.environ.get("EVALUATION_DASHBOARD_TOOL") or ROOT / "tools" / "evaluation-dashboard.py")
SPEC = importlib.util.spec_from_file_location("economicon_evaluation_dashboard_sql_shape", TOOL_PATH)
assert SPEC is not None and SPEC.loader is not None
tool = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = tool
SPEC.loader.exec_module(tool)


# --- Conjunto de datos mínimo válido, escrito a mano (sin Node ni manifiestos) ---------------------------------


def make_run(run_id: str = "run-1", **fields) -> dict:
    run = {
        "run_id": run_id, "source": "SRC-1", "run_at": "2026-10-14T10:00:00Z", "commit": "abc1234",
        "suite": "JUP-069", "suite_version": "1.0.0", "suite_sha256": "ab" * 32, "corpus_sha256": "cd" * 32,
        "embedding_provider": "mock", "embedding_alias": "mock-alias",
        "retrieval": {"top_k": 4, "max_distance": 0.6, "chunk_size": 500, "chunk_overlap": 50},
        "generation_model": "modelo-1", "prompt_sha256": None, "synthetic": False,
        "is_real": True, "non_real_reasons": [], "comparability_key": "ef" * 32, "format": "rows-v1",
        "milestone": False, "report_path": "docs/evidence/informe.json", "report_sha256": "01" * 32,
    }
    run.update(fields)
    return run


def make_row(index: int = 0) -> dict:
    return {
        "measure_type": "A", "grp": "g", "metric_id": "M-1", "behavior": f"b{index}", "status": "measured",
        "count": None, "value": 0.5, "unit": "ms", "numerator": None, "denominator": None,
        "ci_low": None, "ci_high": None, "judgment": "automatic", "selected": False,
    }


def make_entry(run_id: str) -> dict:
    return {"run": make_run(run_id), "results": [make_row()]}


def make_dataset(count: int = 4) -> dict:
    return {"dataset_version": 1, "runs": [make_entry(f"run-{n}") for n in range(count)]}


def error_of(dataset) -> str:
    """Mensaje del `AdapterError` que lanza `build_sql`; falla si no lanza o lanza otro tipo."""
    with unittest.TestCase().assertRaises(tool.AdapterError) as caught:
        tool.build_sql(dataset)
    return str(caught.exception)


class SqlShapeBaseTest(unittest.TestCase):
    def test_el_conjunto_de_partida_es_valido(self) -> None:
        # Línea base: sin ella, un error de forma de las demás pruebas podría venir del propio conjunto de partida
        # y no de la deformación que se aplica.
        self.assertIn("BEGIN;", tool.build_sql(make_dataset()))


class DatasetRootShapeTest(unittest.TestCase):
    def test_clave_desconocida_en_la_raiz(self) -> None:
        # El `raise` de esta rama convertido en `pass` aceptaría una clave ajena y seguiría hasta el final.
        message = error_of({"dataset_version": 1, "runs": [], "extra": 1})
        self.assertTrue(message.startswith("dataset: "), message)
        self.assertIn("clave desconocida", message)

    def test_runs_ausente(self) -> None:
        # Sin `runs` la lista no existe: error de la raíz, no de ninguna ejecución.
        message = error_of({"dataset_version": 1})
        self.assertTrue(message.startswith("dataset: "), message)

    def test_dataset_version_ausente(self) -> None:
        message = error_of({"runs": []})
        self.assertTrue(message.startswith("dataset: "), message)


class EntryRunAndResultsShapeTest(unittest.TestCase):
    def deformed(self, key: str, value) -> str:
        dataset = make_dataset()
        # Posición 2: un índice distinto de 0 y de 1 fija que la ruta usa el índice real de la ejecución.
        dataset["runs"][2][key] = value
        return error_of(dataset)

    def test_run_que_no_es_objeto(self) -> None:
        for value in ([], None, 5, "x", ()):
            with self.subTest(run=value):
                message = self.deformed("run", value)
                self.assertTrue(message.startswith("runs[2].run: "), message)

    def test_results_que_no_es_lista(self) -> None:
        # Cubre el `raise` de la rama (`pass` dejaría pasar un objeto o una tupla) y la ruta exacta del campo.
        for value in ({}, "x", None, (), 5):
            with self.subTest(results=value):
                message = self.deformed("results", value)
                self.assertTrue(message.startswith("runs[2].results: "), message)

    def test_results_tupla_con_filas_validas_tampoco_es_lista(self) -> None:
        # Una tupla con contenido válido solo se rechaza si la rama comprueba el tipo y no el contenido.
        message = self.deformed("results", (make_row(),))
        self.assertTrue(message.startswith("runs[2].results: "), message)


class ShapeBeforeSemanticsTest(unittest.TestCase):
    def test_results_que_no_es_lista_se_informa_antes_que_un_campo_de_run_invalido(self) -> None:
        # La forma se comprueba ANTES de delegar la semántica en `validate_rows`. Con una ejecución válida, esa
        # función también diría `runs[2].results: debe ser una lista` (mismo texto), así que el `raise` de forma
        # no se distinguiría. Con un `commit` inválido en la misma ejecución, sin la comprobación de forma el primer
        # error sería el de `run.commit` (validate_rows revisa `run` antes que `results`).
        dataset = make_dataset()
        dataset["runs"][2]["run"]["commit"] = "no es un commit!"
        # Línea base: con `results` válido, el fallo es el del campo de la ejecución.
        self.assertTrue(error_of(copy.deepcopy(dataset)).startswith("runs[2].run.commit: "))
        dataset["runs"][2]["results"] = {}
        message = error_of(dataset)
        self.assertTrue(message.startswith("runs[2].results: "), message)
        self.assertIn("debe ser una lista", message)


class EntryObjectShapeTest(unittest.TestCase):
    def test_entrada_que_no_es_objeto_en_la_posicion_tres(self) -> None:
        for value in ([], None, 5, "x"):
            with self.subTest(entry=value):
                dataset = make_dataset()
                dataset["runs"][3] = value
                message = error_of(dataset)
                self.assertTrue(message.startswith("runs[3]: "), message)

    def test_entrada_con_clave_de_mas_en_la_posicion_tres(self) -> None:
        dataset = make_dataset()
        dataset["runs"][3]["extra"] = 1
        message = error_of(dataset)
        self.assertTrue(message.startswith("runs[3]: "), message)
        self.assertIn("clave desconocida", message)

    def test_entrada_sin_run_o_sin_results_en_la_posicion_tres(self) -> None:
        for missing in ("run", "results"):
            with self.subTest(falta=missing):
                dataset = make_dataset()
                del dataset["runs"][3][missing]
                message = error_of(dataset)
                self.assertTrue(message.startswith("runs[3]: "), message)
                self.assertIn(missing, message)


class RunKeysShapeTest(unittest.TestCase):
    def test_clave_desconocida_en_run(self) -> None:
        # `run` completo (todas las claves de salida) más una ajena: solo la rama de clave desconocida puede fallar.
        dataset = make_dataset()
        dataset["runs"][1]["run"]["extra"] = 1
        message = error_of(dataset)
        self.assertTrue(message.startswith("runs[1].run: "), message)
        self.assertIn("clave desconocida", message)

    def test_clave_de_run_ausente(self) -> None:
        dataset = make_dataset()
        del dataset["runs"][1]["run"]["report_sha256"]
        message = error_of(dataset)
        self.assertTrue(message.startswith("runs[1].run: "), message)
        self.assertIn("falta", message)
        self.assertIn("report_sha256", message)


class DuplicateRunIdShapeTest(unittest.TestCase):
    def test_run_id_repetido_entre_la_ejecucion_cero_y_la_uno(self) -> None:
        dataset = make_dataset()
        dataset["runs"][1] = make_entry("run-0")
        message = error_of(dataset)
        # Ruta exacta del campo repetido (la segunda aparición) e índice de la primera como propietaria.
        self.assertTrue(message.startswith("runs[1].run.run_id: "), message)
        self.assertIn("runs[0]", message)

    def test_el_propietario_es_la_primera_aparicion(self) -> None:
        # Con el duplicado en la posición 3 y el original en la 2, el índice citado debe ser el 2 y no 0, 1 ni 3.
        dataset = make_dataset()
        dataset["runs"][3] = make_entry("run-2")
        message = error_of(dataset)
        self.assertTrue(message.startswith("runs[3].run.run_id: "), message)
        self.assertIn("ya lo usa runs[2]", message)


if __name__ == "__main__":
    unittest.main()
