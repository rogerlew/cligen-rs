import argparse
import hashlib
import json
from pathlib import Path

MIB = 1024 * 1024


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while block := handle.read(MIB):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("wheelhouse", type=Path)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    expected = {entry["filename"]: entry for entry in manifest["wheels"]}
    observed = {path.name: path for path in args.wheelhouse.glob("*.whl")}
    if set(expected) != set(observed):
        raise RuntimeError("wheelhouse filename set differs from manifest")
    for filename, path in observed.items():
        entry = expected[filename]
        if path.stat().st_size != entry["bytes"] or sha256(path) != entry["sha256"]:
            raise RuntimeError(f"wheel verification failed: {filename}")
    print(f"wheelhouse_verified={len(observed)}")


if __name__ == "__main__":
    main()
