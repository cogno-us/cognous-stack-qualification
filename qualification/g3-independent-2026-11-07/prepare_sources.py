#!/usr/bin/env python3
"""Fetch and verify the frozen qualification sources into a disposable root."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import tarfile
import tempfile
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    manifest = json.loads((HERE / "source-environment.json").read_text())
    destination = args.destination.resolve()
    archives, sources = destination / "archives", destination / "src"
    archives.mkdir(parents=True, exist_ok=True)
    sources.mkdir(parents=True, exist_ok=True)

    for key, source in manifest["sources"].items():
        archive = archives / f"{key}-{source['commit']}.tar.gz"
        url = (
            f"https://github.com/{source['repository']}/archive/"
            f"{source['commit']}.tar.gz"
        )
        if not archive.exists():
            with tempfile.NamedTemporaryFile(dir=archives, delete=False) as tmp:
                with urllib.request.urlopen(url) as response:
                    shutil.copyfileobj(response, tmp)
                temporary = Path(tmp.name)
            temporary.replace(archive)
        digest = hashlib.sha256(archive.read_bytes()).hexdigest()
        if digest != source["archive_sha256"]:
            raise SystemExit(f"{key}: archive digest mismatch")

        target = sources / key
        if target.exists():
            continue
        temporary_target = sources / f".{key}.tmp"
        shutil.rmtree(temporary_target, ignore_errors=True)
        temporary_target.mkdir()
        with tarfile.open(archive, "r:gz") as bundle:
            members = bundle.getmembers()
            prefix = Path(members[0].name).parts[0]
            for member in members:
                relative = Path(*Path(member.name).parts[1:])
                if not relative.parts:
                    continue
                member.name = str(relative)
                resolved = (temporary_target / relative).resolve()
                if not resolved.is_relative_to(temporary_target.resolve()):
                    raise SystemExit(f"{key}: unsafe archive member")
                if member.issym() or member.islnk():
                    raise SystemExit(f"{key}: links are not accepted")
                bundle.extract(member, temporary_target, filter="data")
            if not prefix:
                raise SystemExit(f"{key}: archive prefix missing")
        temporary_target.replace(target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
