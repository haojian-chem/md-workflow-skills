# Chain and component selection rules

## 1. Scope

This substep selects one model and a set of complete classified components for one Workstream. It does not perform residue-range extraction, atom filtering, chemical bond breaking, altLoc resolution or identifier normalization.

## 2. Authoritative inputs

Selection is derived only from:

```text
classification_result.yaml
selection_spec.yaml
resolved decision records referenced by the spec
```

Natural-language context, common MD conventions, file names and directory names are not selection evidence.

## 3. Explicit component IDs

Every selected object must be named by a `component_id` present in the classification result.

A component contains the complete `residue_ids` recorded by 1.2. Selecting a component selects all of its residues and every atom/altLoc in those residues.

The following implicit selectors are prohibited in v1:

- all protein chains;
- all ligands;
- chain-name wildcard;
- residue-name wildcard;
- all objects within a distance;
- all cofactors or metals;
- remove all water/ions;
- retain biological assembly automatically.

## 4. Model selection

Exactly one `selected_model_id` is required. The Operation never defaults to the first model.

Every selected component must belong to the selected model. A component from another model makes the spec invalid.

## 5. Confirmed covalent closure

Confirmed covalent relations are:

```text
COVALENT
DISULFIDE
GLYCOSIDIC
```

For every confirmed relation, either both endpoints are selected or both are excluded. A selection that retains only one endpoint is blocked.

The Operation must not:

- auto-add the missing endpoint;
- remove the connection record and continue;
- treat the relation as an optional warning;
- use geometry to override explicit connectivity.

The user must provide a revised complete selection or move intentional bond breaking to a dedicated chemical-editing workflow.

## 6. Non-covalent boundary relations

The following may cross the selection boundary without forcing inclusion:

- explicit or geometric metal coordination;
- hydrogen bonds;
- salt bridges;
- close contacts;
- geometry-only covalent candidates.

All such cross-boundary relations must be recorded in the manifest/report because they can affect scientific interpretation, but they do not change the selected set.

## 7. Component integrity

A selected component is indivisible in v1. The output must preserve:

- every classified residue in the component;
- every atom of each selected residue;
- every altLoc;
- source ordering;
- model/chain/residue/atom identity fields;
- coordinates, occupancy, B factor, element and formal charge when represented.

Partial chains, domains, residue ranges and atom subsets require a later contract revision or another Skill.

## 8. Output format

The spec explicitly chooses `PDB` or `MMCIF`.

### PDB

PDB is allowed only when selected identifiers and atoms can be represented without implicit renaming, truncation or collision. Otherwise block and request MMCIF or an explicit later mapping/reorder decision.

### MMCIF

MMCIF may normalize category ordering, quoting and formatting. The output must preserve selected coordinate objects and the atom mapping.

For AF3 CIF input, the selected output is a normalized coordinate MMCIF. AF3-specific non-coordinate categories are not guaranteed to survive and must be reported. The original AF3 CIF remains the provenance source.

## 9. Mapping identity

Stable source atom identity uses:

```text
model_id
chain_id
residue_name
residue_number
insertion_code
atom_name
altloc
element
```

Serial numbers are recorded but are not the sole identity key.

The mapping must be one-to-one and complete for all selected atoms.

## 10. Idempotency and conflicts

Same task, same source/spec/classification hashes and identical outputs may be reused after hash verification.

Block when:

- an output path belongs to another task;
- an existing output has a different hash;
- source/classification/spec changed after task creation;
- output path equals an input path;
- output is under a forbidden management path.

## 11. Artifact semantics

The Operation creates an UNVALIDATED STRUCTURE candidate. Its dedicated Validator may confirm selection fidelity, but that does not imply altLoc, completeness, protonation or final structure-preparation validity.
