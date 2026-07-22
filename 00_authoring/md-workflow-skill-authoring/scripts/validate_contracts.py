#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import yaml

REQUIRED = {
    'common_types.schema.yaml',
    'confirmation_item.schema.yaml',
    'workflow_route_fragment.schema.yaml',
    'workflow_decision.schema.yaml',
    'subagent_task.schema.yaml',
    'subagent_result.schema.yaml',
    'project_state.schema.yaml',
    'workstream_state.schema.yaml',
    'project_event.schema.yaml',
    'manager_session.schema.yaml',
    'route_record.schema.yaml',
    'decision_record.schema.yaml',
    'submission_record.schema.yaml',
    'artifact_set.schema.yaml',
    'state_snapshot.schema.yaml',
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('root', type=Path)
    args = ap.parse_args()

    contract_dir = args.root / '03_contracts'
    errors: list[str] = []
    names = {p.name for p in contract_dir.glob('*.yaml')}

    for name in sorted(REQUIRED - names):
        errors.append(f'missing {name}')

    try:
        from jsonschema.validators import validator_for
        from jsonschema.exceptions import SchemaError
    except Exception as exc:
        validator_for = None
        SchemaError = Exception
        errors.append(f'jsonschema unavailable: {exc}')

    for path in sorted(contract_dir.glob('*.yaml')):
        try:
            data = yaml.safe_load(path.read_text(encoding='utf-8'))
            if not isinstance(data, dict):
                errors.append(f'{path.name}: root is not mapping')
                continue
            if '$schema' not in data:
                errors.append(f'{path.name}: missing $schema')
            if data.get('$id') != path.name:
                errors.append(f'{path.name}: $id must equal filename')
            if validator_for is not None:
                validator_for(data).check_schema(data)
        except SchemaError as exc:
            errors.append(f'{path.name}: invalid JSON Schema: {exc.message}')
        except Exception as exc:
            errors.append(f'{path.name}: {exc}')

    for error in errors:
        print('ERROR:', error)
    print(f'RESULT: {len(errors)} error(s)')
    return 1 if errors else 0


if __name__ == '__main__':
    raise SystemExit(main())
