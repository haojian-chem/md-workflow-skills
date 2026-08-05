# Built-in CCD-compatible reference library

This directory is the fixed built-in component-reference root for Skill 1.2.
`index.yaml` is authoritative; callers must not scan the directory or download
missing entries. Each indexed component maps to one `<component_id>.cif` file
and a verified SHA-256 value.

The committed seed files contain only the component and atom-table fields used
by the current heavy-atom comparison. Add or replace a component only through
`scripts/add_ccd_reference.py`, with an explicit target library. That operation
validates the CIF, derives the canonical component ID, verifies conflicts and
updates `index.yaml` atomically. It never edits residue registries.

Additional libraries use the same flat layout and are listed explicitly in
`classification_config.yaml` under `ccd.additional_library_paths`.

The first implementation seeds amino acids, supported protonation variants,
DNA/RNA residues and MSE/SEC/PYL. The larger cofactor/ligand seed set remains an
explicit validation item before this redesigned 1.2 path can return to PASS.
