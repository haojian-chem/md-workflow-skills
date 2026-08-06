# Built-in CCD-compatible reference library

This is the fixed built-in component-reference root for Skill 1.2.
`index.yaml` is authoritative; runtime callers must not scan this directory or
download missing entries. Each component maps to one `<component_id>.cif` and
one verified SHA-256 value.

Seed files retain only the component and atom-table fields required by the
heavy-atom comparison. The approved cofactor/ligand set is defined once in
`../approved_ccd_seed_manifest.yaml`. Use `scripts/add_ccd_reference.py` for one
explicit component, or `scripts/sync_approved_ccd_seeds.py` for that approved
set. Both validate IDs, CIF parsing, conflicts and hashes without editing
residue registries.

The webpage entry point is the manually dispatched
`component-classification-v1-2-ccd-seeds` workflow. It is blocked on `main` and
commits generated seeds only to the selected feature branch.

Additional libraries use the same indexed flat layout and are declared in
`classification_config.yaml` under `ccd.additional_library_paths`.
