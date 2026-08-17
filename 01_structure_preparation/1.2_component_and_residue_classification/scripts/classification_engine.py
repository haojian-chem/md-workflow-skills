#!/usr/bin/env python3
"""Side-effect-free facade for the component/residue baseline engine."""
from __future__ import annotations

import copy
from pathlib import Path

import classification_engine_core as _core

for _name in dir(_core):
    if not _name.startswith("__"):
        globals()[_name] = getattr(_core, _name)


def execute_classification(config, script_dir):
    """Run the internal baseline engine with its adapter output schema by default."""
    runtime = copy.deepcopy(config)
    output = runtime.setdefault("output", {})
    output.setdefault(
        "observations_schema",
        str(
            Path(script_dir).resolve().parent
            / "schemas/classification_observations_engine.schema.yaml"
        ),
    )
    return _core.execute_classification(runtime, Path(script_dir).resolve())
