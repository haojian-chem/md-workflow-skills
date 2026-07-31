#!/usr/bin/env python3
"""Side-effect-free facade for the component/residue classification engine."""
from __future__ import annotations

import classification_engine_core as _core

# Preserve the established module surface, including internal helpers imported
# by executable tests, without assigning into the core module.
for _name in dir(_core):
    if not _name.startswith("__"):
        globals()[_name] = getattr(_core, _name)

execute_classification = _core.execute_classification
