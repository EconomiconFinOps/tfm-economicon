"""Prepare the private channel key without rotating existing credentials."""
import argparse
import os
from pathlib import Path
import secrets


def ensure_hmac(path):
    path = Path(path).resolve()
    if not path.exists():
        path.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "wb") as output:
            output.write(secrets.token_hex(32).encode("ascii"))
        # The private host directory protects the file; the non-root containers
        # must be able to read a Compose file-secret mounted without uid remapping.
        os.chmod(path, 0o444)
    if not path.is_file() or not 32 <= path.stat().st_size <= 4096:
        raise ValueError("Private chat key is invalid; existing file retained")
    return str(path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    ensure_hmac(parser.parse_args().path)
