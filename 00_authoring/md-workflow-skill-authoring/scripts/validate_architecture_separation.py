#!/usr/bin/env python3
from pathlib import Path
import argparse, re, sys

BANNED = {
    r'\bskill_architect\b': 'removed development role',
    r'\bskill_author\b': 'removed development role',
    r'\bskill_reviewer\b': 'removed development role',
    r'\bskill_tester\b': 'removed development role',
    r'execution_mode\s*:\s*parallel': 'MD parallel execution field',
}

ALLOW = {'validate_architecture_separation.py', 'PHASE1_V2_VALIDATION.json'}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('root', type=Path)
    args = ap.parse_args()
    findings=[]
    for p in args.root.rglob('*'):
        if not p.is_file() or p.name in ALLOW or p.suffix.lower() not in {'.md','.yaml','.yml','.toml','.json'}:
            continue
        text=p.read_text(encoding='utf-8',errors='replace')
        for pat, reason in BANNED.items():
            if re.search(pat,text,re.I):
                findings.append((str(p.relative_to(args.root)),pat,reason))
    for f,pat,reason in findings:
        print(f'ERROR: {f}: {reason}: {pat}')
    print(f'RESULT: {len(findings)} forbidden architecture reference(s)')
    return 1 if findings else 0
if __name__=='__main__':
    raise SystemExit(main())
