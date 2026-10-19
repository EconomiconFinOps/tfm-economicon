"""Negative controls: changed references must never pass offline verification."""
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from preparar import prepare

from verificar import check


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]


class IntegrityControls(unittest.TestCase):
    def test_rejects_changed_cost_or_leaked_answer(self):
        for name in ("costes-esperados.json", "prompts.json"):
            with self.subTest(file=name), tempfile.TemporaryDirectory() as tmp:
                package = Path(tmp)
                shutil.copytree(ROOT / "generado", package / "generado")
                target = package / "generado" / name
                data = json.loads(target.read_text(encoding="utf-8"))
                if name == "costes-esperados.json":
                    data["totals"][0]["cost"] = "1000.00"
                else:
                    data["cases"][0]["expected"] = "1000 EUR"
                target.write_text(json.dumps(data), encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "Archivo no reproducible"):
                    check(REPO, package)

    def test_rejects_matching_but_invalid_regeneration(self):
        # Both copies agree: only the independent reference invariant catches this.
        with tempfile.TemporaryDirectory() as tmp:
            package = Path(tmp)

            def extra_group(repo, output):
                expected = prepare(repo, output)
                expected["groups"].append({"value": "unexpected", "record_count": 0})
                (output / "costes-esperados.json").write_text(
                    json.dumps(expected), encoding="utf-8"
                )
                shutil.copytree(output, package / "generado")
                return expected

            with patch("verificar.prepare", side_effect=extra_group):
                with self.assertRaisesRegex(ValueError, "Referencia o separación"):
                    check(REPO, package)

    def test_rejects_missing_or_extra_file(self):
        for action in ("missing", "extra"):
            with self.subTest(action=action), tempfile.TemporaryDirectory() as tmp:
                package = Path(tmp)
                shutil.copytree(ROOT / "generado", package / "generado")
                if action == "missing":
                    (package / "generado/prompts.json").unlink()
                else:
                    (package / "generado/unexpected.txt").write_text("extra", encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "Inventario generado"):
                    check(REPO, package)


if __name__ == "__main__":
    unittest.main()
