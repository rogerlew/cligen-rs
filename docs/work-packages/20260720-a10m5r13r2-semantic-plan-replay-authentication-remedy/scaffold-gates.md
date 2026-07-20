# Scaffold gates

```sh
python3 docs/work-packages/20260720-a10m5r13r2-semantic-plan-replay-authentication-remedy/artifacts/test_replay_authentication.py
python3 - <<'PY'
import ast
from pathlib import Path
root = Path("docs/work-packages/20260720-a10m5r13r2-semantic-plan-replay-authentication-remedy/artifacts")
for path in (root / "run_temporal_replay.py", root / "test_replay_authentication.py"):
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
PY
```

The tests exercise byte parity between the replay-local and toolkit canonical
implementations, Unicode key ordering, strict duplicate/float/constant/safe-
integer/surrogate rejection, exact semantic reconstruction, optional
`created_at` removal, tampered allowlist rejection,
both unsigned and resigned receipt tampering, all four committed input-file
pins, semantic asset-manifest binding, input-commit ancestry, working-byte
publication drift, local/upstream head drift, and the complete collection
present/absent/identity partition. A focused file-reader regression admits the
authenticated `1289.0` science value while proving the record reader still
rejects the same float. The tests create no authority, remote state, scheduler
query, or allocation.
