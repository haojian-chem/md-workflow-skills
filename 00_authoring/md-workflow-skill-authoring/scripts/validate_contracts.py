#!/usr/bin/env python3
from pathlib import Path
import argparse, sys, yaml

REQUIRED={
 'common_types.schema.yaml','confirmation_item.schema.yaml','workflow_decision.schema.yaml',
 'subagent_task.schema.yaml','subagent_result.schema.yaml','project_state.schema.yaml'
}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('root',type=Path); args=ap.parse_args()
    d=args.root/'03_contracts'; errors=[]
    names={p.name for p in d.glob('*.yaml')}
    for n in sorted(REQUIRED-names): errors.append(f'missing {n}')
    for p in d.glob('*.yaml'):
        try:
            data=yaml.safe_load(p.read_text(encoding='utf-8'))
            if not isinstance(data,dict): errors.append(f'{p.name}: root is not mapping')
            if '$schema' not in data: errors.append(f'{p.name}: missing $schema')
        except Exception as e: errors.append(f'{p.name}: {e}')
    for e in errors: print('ERROR:',e)
    print(f'RESULT: {len(errors)} error(s)')
    return 1 if errors else 0
if __name__=='__main__': raise SystemExit(main())
