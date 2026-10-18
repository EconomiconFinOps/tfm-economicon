"""Pinned build artifact integrity; synthetic bytes, no network inference."""
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("build_tokenizer", ROOT / "apps/processor/build_tokenizer.py")
tokenizer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tokenizer)


class TokenizerBuildTests(unittest.TestCase):
    def test_pins_match_current_chat_and_summary_manifests(self):
        for bundle in ("chat/v3", "summary/v3"):
            manifest = json.loads((ROOT / "apps/processor/app/agents/prompt_resources/jup035" / bundle / "manifest.json").read_text())
            self.assertEqual(manifest["tokenizer"]["revision"], tokenizer.REVISION)
            self.assertEqual(manifest["tokenizer"]["sha256"], tokenizer.SHA256)
            self.assertEqual(manifest["tokenizer"]["bytes"], tokenizer.SIZE)
        self.assertEqual(tokenizer.URL, "https://huggingface.co/zai-org/GLM-5.2/resolve/" + tokenizer.REVISION + "/tokenizer.json")

    def test_verified_download_replaces_only_after_integrity_check(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "tokenizer.json"
            target.write_bytes(b"existing")
            def download(request, **kwargs):
                self.assertEqual(request.full_url, tokenizer.URL)
                self.assertEqual(target.read_bytes(), b"existing")
                return io.BytesIO(b"right")
            result = tokenizer.fetch(target, opener=download, digest=hashlib.sha256(b"right").hexdigest(), size=5)
            self.assertEqual(result, target)
            self.assertEqual(target.read_bytes(), b"right")
            self.assertEqual(list(target.parent.iterdir()), [target])

    def test_wrong_artifact_is_rejected_without_replacing_existing_file(self):
        for payload in (b"wrong", b"shorter-than-expected", b"four"):
            with self.subTest(payload=payload), tempfile.TemporaryDirectory() as directory:
                target = Path(directory) / "tokenizer.json"
                target.write_bytes(b"existing")
                with self.assertRaises(ValueError):
                    tokenizer.fetch(target, opener=lambda *a, **kw: io.BytesIO(payload),
                                    digest=hashlib.sha256(b"right").hexdigest(), size=5)
                self.assertEqual(target.read_bytes(), b"existing")
                self.assertEqual(list(target.parent.iterdir()), [target])

    def test_verified_cache_needs_no_network(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "tokenizer.json"
            target.write_bytes(b"right")
            def forbidden(*args, **kwargs):
                self.fail("Verified cache should work offline")
            tokenizer.fetch(target, opener=forbidden, digest=hashlib.sha256(b"right").hexdigest(), size=5)

    def test_same_verified_fetcher_supports_the_explicit_embedding_resource_url(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "cl100k_base.tiktoken"
            def download(request, **kwargs):
                self.assertEqual(request.full_url, "https://openaipublic.blob.core.windows.net/encodings/cl100k_base.tiktoken")
                return io.BytesIO(b"fixture")
            tokenizer.fetch(target, opener=download, digest=hashlib.sha256(b"fixture").hexdigest(), size=7,
                            url="https://openaipublic.blob.core.windows.net/encodings/cl100k_base.tiktoken")
            self.assertEqual(target.read_bytes(), b"fixture")


if __name__ == "__main__":
    unittest.main()
