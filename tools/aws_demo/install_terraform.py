"""Install pinned Linux Terraform using a committed official-release checksum.

Neither cached local tools nor an unversioned 'latest' binary are accepted.
The SHA256 was checked against HashiCorp's 1.13.3 SHA256SUMS. Never runs apply.
"""
import hashlib
import os
from pathlib import Path
import urllib.request
import zipfile

VERSION = "1.13.3"
LINUX_SHA256 = "71fc43d92ea09907be5d416d2405a6a9c2d1ceaed633f5e175c0af26e8c4b365"


def install():
    name = f"terraform_{VERSION}_linux_amd64.zip"
    base = f"https://releases.hashicorp.com/terraform/{VERSION}/"
    tools = Path(__file__).resolve().parents[2] / ".work/bin"
    tools.mkdir(parents=True, exist_ok=True)
    archive = tools / name
    data = urllib.request.urlopen(base + name, timeout=120).read()
    if hashlib.sha256(data).hexdigest() != LINUX_SHA256:
        raise ValueError("Terraform download checksum mismatch")
    archive.write_bytes(data)
    with zipfile.ZipFile(archive) as bundle:
        binary = bundle.read("terraform")
    destination = tools / "terraform"
    destination.write_bytes(binary)
    os.chmod(destination, 0o755)


if __name__ == "__main__":
    install()
