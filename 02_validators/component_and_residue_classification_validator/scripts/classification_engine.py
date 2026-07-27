#!/usr/bin/env python3
"""Runtime facade for the component/residue classification v1.2 engine.

The implementation remains in ``classification_engine_core.py``.  This facade
keeps structural entity/polymer facts authoritative for chain grouping even
when residue topology classification is unresolved or conflicting.
"""
from __future__ import annotations

import classification_engine_core as _core


_original_build_chain_groups = getattr(
    _core,
    "_classification_engine_original_build_chain_groups",
    _core._build_chain_groups,
)
_core._classification_engine_original_build_chain_groups = _original_build_chain_groups


def _build_chain_groups(analyses):
    """Group structural chains without erasing unresolved classification state.

    ``classification.polymer_class`` is a scientific classification result and
    may be null or conflicting.  ``ResidueRecord`` entity/polymer metadata is a
    separate structural fact.  During grouping only, temporarily project an
    available structural class onto the analysis, then restore the original
    classification objects before downstream output is built.
    """

    replaced = []
    try:
        for analysis in analyses:
            structural_class = _core._entity_polymer_class(analysis.residue)
            value = analysis.classification
            if structural_class is None or structural_class == value.polymer_class:
                continue
            replaced.append((analysis, value))
            analysis.classification = _core.ClassificationValue(
                polymer_class=structural_class,
                topology_class=value.topology_class,
                resolution_status=value.resolution_status,
                primary_source=value.primary_source,
                evidence=value.evidence,
                ccd_id=value.ccd_id,
                rtp_template_name=value.rtp_template_name,
            )
        return _original_build_chain_groups(analyses)
    finally:
        for analysis, value in replaced:
            analysis.classification = value


_core._build_chain_groups = _build_chain_groups

# Preserve the previous module surface, including internal helpers used by the
# executable tests, while ensuring execute_classification resolves the patched
# grouping function through the core module globals.
for _name in dir(_core):
    if _name.startswith("__") or _name == "_build_chain_groups":
        continue
    globals()[_name] = getattr(_core, _name)
