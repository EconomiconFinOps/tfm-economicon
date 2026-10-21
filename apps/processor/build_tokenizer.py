"""Fetch the immutable, verified tokenizer at build time; never at runtime."""
import argparse
import hashlib
import os
from pathlib import Path
import tempfile
import time
import urllib.request

REVISION = "314113f8a7dadb388215396ba5fbee2c610a04d6"
SHA256 = "c90dfa01249db1be4245780a052ede752e1361c612ac6d08e2bdada7d599476b"
SIZE = 6367257
URL = f"https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash/resolve/{REVISION}/tokenizer.json"
DEFAULT = Path(__file__).parent / "app/agents/prompt_resources/jup035/chat/v4/tokenizer.json"
LEGACY_REVISION = "a66456a59f21345d1e5e586345c448a9106d29d7"
LEGACY_SHA256 = "19e773648cb4e65de8660ea6365e10acca112d42a854923df93db4a6f333a82d"
LEGACY_SIZE = 20217442
LEGACY_URL = f"https://huggingface.co/zai-org/GLM-5.2/resolve/{LEGACY_REVISION}/tokenizer.json"
LEGACY_DEFAULT = DEFAULT.parent.parent / "v2/tokenizer.json"


def verified(path, digest=SHA256, size=SIZE):
    if not path.is_file() or path.stat().st_size != size:
        return False
    with path.open("rb") as source:
        checksum = hashlib.sha256()
        for chunk in iter(lambda: source.read(65536), b""):
            checksum.update(chunk)
        return checksum.hexdigest() == digest


def fetch(path=DEFAULT, *, opener=urllib.request.urlopen, digest=SHA256, size=SIZE, url=None):
    path = Path(path)
    if verified(path, digest, size):
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        deadline = time.monotonic() + 300
        request = urllib.request.Request(url or URL, headers={"User-Agent": "economicon-tokenizer-build"})
        with opener(request, timeout=30) as response:
            with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as output:
                temporary = Path(output.name)
                count = 0
                while chunk := response.read(65536):
                    count += len(chunk)
                    if count > size or time.monotonic() >= deadline:
                        raise ValueError("Tokenizer download limit exceeded")
                    output.write(chunk)
        if not verified(temporary, digest, size):
            raise ValueError("Tokenizer SHA256 or size mismatch")
        os.chmod(temporary, 0o644)
        temporary.replace(path)
        return path
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT)
    parser.add_argument("--legacy-output", type=Path, default=LEGACY_DEFAULT,
                        help="Historical summary reader asset; never the active Flash counter")
    parser.add_argument("--embedding-output", type=Path, help="Generated cl100k_base asset, outside the repository")
    parser.add_argument("--embedding-only", action="store_true", help="Prepare embeddings without changing the GLM artifact")
    args = parser.parse_args()
    if not args.embedding_only:
        fetch(args.output)
        fetch(args.legacy_output, digest=LEGACY_SHA256, size=LEGACY_SIZE, url=LEGACY_URL)
    if args.embedding_output is not None or args.embedding_only:
        from app.embeddings.tokenizer_resource import (
            RESOURCE_URL, RESOURCE_SHA256, RESOURCE_BYTES, resource_path, assert_external_resource_path,
        )
        target = args.embedding_output if args.embedding_output is not None else resource_path()
        assert_external_resource_path(target)
        if target.is_symlink():
            raise ValueError('Embedding tokenizer destination must not be a symlink')
        fetch(target, url=RESOURCE_URL, digest=RESOURCE_SHA256, size=RESOURCE_BYTES)
    print("Pinned tokenizer verified")
