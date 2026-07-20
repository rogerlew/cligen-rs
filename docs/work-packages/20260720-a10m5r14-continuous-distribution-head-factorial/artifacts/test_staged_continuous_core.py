#!/usr/bin/env python3
"""Stage the exact transitive science modules and run the full CPU self-test."""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import torch

package = Path(__file__).resolve().parents[1]
repo = package.parents[2]
sources = {
    "legacy_core.py": repo / "docs/work-packages/20260717-a10m5-bounded-gpu-screen/artifacts/jobs/screen.py",
    "screen_core_v2.py": repo / "docs/work-packages/20260718-a10m5r3-candidate-family-capacity-knee/artifacts/jobs/screen_core_v2.py",
    "inherited_climate_core.py": repo / "docs/work-packages/20260719-a10m5r8-climate-statistics-objective/artifacts/jobs/climate_core.py",
    "climate_core.py": package / "artifacts/jobs/climate_core.py",
    "residual_core.py": repo / "docs/work-packages/20260719-a10m5r9-climate-normal-residual-architecture/artifacts/jobs/residual_core.py",
    "portfolio_core.py": repo / "docs/work-packages/20260719-a10m5r10-parallel-architecture-portfolio/artifacts/jobs/portfolio_core.py",
    "inherited_continuous_core.py": repo / "docs/work-packages/20260719-a10m5r12r1-admission-materialization-remedy/artifacts/jobs/continuous_core.py",
    "aligned_objective.py": package / "artifacts/jobs/aligned_objective.py",
    "continuous_core.py": package / "artifacts/jobs/continuous_core.py",
}
with tempfile.TemporaryDirectory() as scratch:
    root = Path(scratch)
    for name, source in sources.items():
        payload = source.read_bytes()
        if package not in source.parents:
            committed = subprocess.run(
                ("git", "show", f"HEAD:{source.relative_to(repo).as_posix()}"),
                cwd=repo, check=True, capture_output=True,
            ).stdout
            if committed != payload:
                raise RuntimeError(f"inherited staged source drift: {source}")
        (root / name).write_bytes(payload)
    sys.path.insert(0, str(root))
    import continuous_core  # noqa: E402

    continuous_core.self_test(torch.device("cpu"))
print("A10M5R14-STAGED-CONTINUOUS-CORE-TEST-PASS")
