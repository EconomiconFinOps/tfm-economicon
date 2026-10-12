import hashlib
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location(
    "build_tokenizer", Path(__file__).resolve().parents[1] / "apps/processor/build_tokenizer.py")
tokenizer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tokenizer)


class TokenizerBuildTests(unittest.TestCase):
    def test_wrong_artifact_is_rejected_without_replacing_existing_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "tokenizer.json"
            path.write_bytes(b"existing")
            with self.assertRaises(ValueError):
                tokenizer.fetch(path, opener=lambda *a, **kw: io.BytesIO(b"wrong"),
                                digest=hashlib.sha256(b"right").hexdigest(), size=5)
            self.assertEqual(path.read_bytes(), b"existing")
            self.assertEqual(list(path.parent.iterdir()), [path])

    def test_verified_cache_needs_no_network(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "tokenizer.json"
            path.write_bytes(b"right")
            def forbidden(*args, **kwargs):
                self.fail("Verified cache should work offline")
            tokenizer.fetch(path, opener=forbidden, digest=hashlib.sha256(b"right").hexdigest(), size=5)


if __name__ == "__main__":
    unittest.main()
