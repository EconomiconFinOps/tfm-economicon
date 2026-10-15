"""Fetch the immutable, verified tokenizer at build time; never at runtime."""
import argparse
import hashlib
import os
from pathlib import Path
import tempfile
import time
import urllib.request

REVISION = "a66456a59f21345d1e5e586345c448a9106d29d7"
SHA256 = "19e773648cb4e65de8660ea6365e10acca112d42a854923df93db4a6f333a82d"
SIZE = 20217442
URL = f"https://huggingface.co/zai-org/GLM-5.2/resolve/{REVISION}/tokenizer.json"
DEFAULT = Path(__file__).parent / "app/agents/prompt_resources/jup035/chat/v2/tokenizer.json"


def verified(path, digest=SHA256, size=SIZE):
    if not path.is_file() or path.stat().st_size != size:
        return False
    with path.open("rb") as source:
        checksum = hashlib.sha256()
        for chunk in iter(lambda: source.read(65536), b""):
            checksum.update(chunk)
        return checksum.hexdigest() == digest


def fetch(path=DEFAULT, *, opener=urllib.request.urlopen, digest=SHA256, size=SIZE):
    path = Path(path)
    if verified(path, digest, size):
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        deadline = time.monotonic() + 300
        request = urllib.request.Request(URL, headers={"User-Agent": "economicon-tokenizer-build"})
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
    fetch(parser.parse_args().output)
    print("Pinned tokenizer verified")
