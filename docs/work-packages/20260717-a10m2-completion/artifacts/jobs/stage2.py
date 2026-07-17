from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import time
from pathlib import Path

MIB = 1024 * 1024
CHECKPOINT_BYTES = 64 * MIB


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while block := handle.read(MIB):
            digest.update(block)
    return digest.hexdigest()


def timed(callable_: object) -> float:
    start = time.monotonic()
    callable_()
    return time.monotonic() - start


def verify_objects(root: Path, objects: list[dict[str, object]]) -> None:
    for entry in objects:
        path = root / str(entry["path"])
        if path.stat().st_size != int(entry["bytes"]):
            raise RuntimeError(f"size mismatch for {entry['path']}")
        if sha256(path) != entry["sha256"]:
            raise RuntimeError(f"hash mismatch for {entry['path']}")


def copy_objects(
    source: Path, destination: Path, objects: list[dict[str, object]]
) -> None:
    for entry in objects:
        relative = Path(str(entry["path"]))
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source / relative, target)


def write_checkpoint(path: Path) -> None:
    block = bytes(MIB)
    with path.open("wb") as handle:
        for _ in range(CHECKPOINT_BYTES // MIB):
            handle.write(block)
        handle.flush()
        os.fsync(handle.fileno())


def atomic_json(path: Path, payload: dict[str, object]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def rate(byte_count: int, seconds: float) -> float:
    return byte_count / MIB / max(seconds, 1e-9)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--durable-root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--archive-sha256", required=True)
    parser.add_argument("--local-dir", type=Path, required=True)
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    objects = manifest["objects"]
    total_bytes = sum(int(entry["bytes"]) for entry in objects)
    if len(objects) != 98 or total_bytes != 223_799_545:
        raise RuntimeError("A10M1 transfer identity differs from frozen aggregate")

    durable_verify_seconds = timed(lambda: verify_objects(args.durable_root, objects))

    local_objects = args.local_dir / "objects"
    many_copy_seconds = timed(
        lambda: copy_objects(args.durable_root, local_objects, objects)
    )
    many_verify_seconds = timed(lambda: verify_objects(local_objects, objects))

    local_archive = args.local_dir / "a10m1-corpus.tar"
    archive_copy_seconds = timed(lambda: shutil.copyfile(args.archive, local_archive))
    if sha256(local_archive) != args.archive_sha256:
        raise RuntimeError("job-local archive hash mismatch")

    warm_read_seconds = timed(lambda: verify_objects(local_objects, objects))

    local_checkpoint = args.local_dir / "checkpoint-64m.bin"
    write_checkpoint_seconds = timed(lambda: write_checkpoint(local_checkpoint))
    checkpoint_sha = sha256(local_checkpoint)
    args.checkpoint.parent.mkdir(parents=True, exist_ok=True)
    checkpoint_part = args.checkpoint.with_suffix(args.checkpoint.suffix + ".part")
    copyback_seconds = timed(lambda: shutil.copyfile(local_checkpoint, checkpoint_part))
    os.replace(checkpoint_part, args.checkpoint)
    if sha256(args.checkpoint) != checkpoint_sha:
        raise RuntimeError("durable checkpoint copy-back hash mismatch")

    shutil.rmtree(local_objects)
    if local_objects.exists():
        raise RuntimeError("local cache removal failed")
    fallback_path = args.durable_root / str(objects[0]["path"])
    if sha256(fallback_path) != objects[0]["sha256"]:
        raise RuntimeError("durable fallback verification failed")

    payload = {
        "archive_bytes": args.archive.stat().st_size,
        "archive_copy_mib_s": rate(args.archive.stat().st_size, archive_copy_seconds),
        "archive_copy_seconds": archive_copy_seconds,
        "archive_sha256": args.archive_sha256,
        "cache_fallback": "verified_durable",
        "checkpoint_bytes": CHECKPOINT_BYTES,
        "checkpoint_copyback_mib_s": rate(CHECKPOINT_BYTES, copyback_seconds),
        "checkpoint_copyback_seconds": copyback_seconds,
        "checkpoint_sha256": checkpoint_sha,
        "checkpoint_write_seconds": write_checkpoint_seconds,
        "durable_verify_seconds": durable_verify_seconds,
        "logical_bytes": total_bytes,
        "many_copy_mib_s": rate(total_bytes, many_copy_seconds),
        "many_copy_seconds": many_copy_seconds,
        "many_verify_seconds": many_verify_seconds,
        "object_count": len(objects),
        "stage2": "pass",
        "warm_read_mib_s": rate(total_bytes, warm_read_seconds),
        "warm_read_seconds": warm_read_seconds,
        "warm_read_warning": "cache-warm diagnostic; not training throughput",
    }
    atomic_json(args.result, payload)
    print(json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    main()
