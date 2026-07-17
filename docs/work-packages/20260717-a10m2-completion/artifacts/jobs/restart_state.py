from __future__ import annotations

import argparse
import hashlib
import json
import os
import signal
import sys
import time
from pathlib import Path

SEED = 0xA10C0DE
MODULUS = 2**64
interrupted = False


def advance(state: int) -> int:
    return (6364136223846793005 * state + 1442695040888963407) % MODULUS


def trace_update(digest: str, step: int, state: int) -> str:
    return hashlib.sha256(f"{digest}:{step}:{state}".encode()).hexdigest()


def atomic_json(path: Path, payload: dict[str, object]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def on_usr1(_signum: int, _frame: object) -> None:
    global interrupted
    interrupted = True


def run_interrupt(checkpoint: Path) -> int:
    signal.signal(signal.SIGUSR1, on_usr1)
    state = SEED
    digest = "0" * 64
    step = 0
    while step < 180:
        step += 1
        state = advance(state)
        digest = trace_update(digest, step, state)
        if interrupted:
            payload = {"digest": digest, "seed": SEED, "state": state, "step": step}
            atomic_json(checkpoint, payload)
            print(
                json.dumps(
                    {"checkpoint": "pass", "c3a": "interrupted", **payload},
                    sort_keys=True,
                )
            )
            return 75
        time.sleep(1.0)
    raise RuntimeError("registered Slurm signal was not delivered before completion")


def run_resume(checkpoint: Path) -> int:
    payload = json.loads(checkpoint.read_text(encoding="utf-8"))
    step = int(payload["step"])
    state = int(payload["state"])
    digest = str(payload["digest"])
    if int(payload["seed"]) != SEED or not 1 <= step < 180:
        raise RuntimeError("invalid checkpoint identity or step")
    while step < 180:
        step += 1
        state = advance(state)
        digest = trace_update(digest, step, state)

    control_state = SEED
    control_digest = "0" * 64
    for control_step in range(1, 181):
        control_state = advance(control_state)
        control_digest = trace_update(control_digest, control_step, control_state)
    if state != control_state or digest != control_digest:
        raise RuntimeError("resumed state or trace differs from uninterrupted control")
    print(
        json.dumps(
            {
                "checkpoint_step": int(payload["step"]),
                "c3b": "pass",
                "final_digest": digest,
                "final_state": state,
                "target_step": step,
            },
            sort_keys=True,
        )
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("interrupt", "resume"))
    parser.add_argument("checkpoint", type=Path)
    args = parser.parse_args()
    args.checkpoint.parent.mkdir(parents=True, exist_ok=True)
    if args.mode == "interrupt":
        return run_interrupt(args.checkpoint)
    return run_resume(args.checkpoint)


if __name__ == "__main__":
    sys.exit(main())
