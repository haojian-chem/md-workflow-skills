#!/usr/bin/env python3
from pathlib import Path
import argparse, re

FM = re.compile(r'\A---\s*\n(.*?)\n---\s*\n', re.S)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('project_root', type=Path)
    ap.add_argument('skill_dir', type=Path)
    a = ap.parse_args()

    p = a.skill_dir / 'SKILL.md'
    errors = []
    warnings = []

    if not p.exists():
        errors.append('missing SKILL.md')
    else:
        text = p.read_text(encoding='utf-8')
        m = FM.search(text)
        if not m:
            errors.append('missing frontmatter')
        else:
            fm = m.group(1)
            if not re.search(r'^name\s*:', fm, re.M):
                errors.append('missing name')
            if not re.search(r'^description\s*:', fm, re.M):
                errors.append('missing description')

        n = len(text.splitlines())
        if n > 500:
            warnings.append(f'SKILL.md has {n} lines; inspect progressive disclosure')

        if re.search(r'00_authoring/md-workflow-skill-authoring/', text):
            errors.append('references superseded authoring package path')

        if re.search(r'\b(SUPERSEDED|LEGACY|HISTORY ONLY)\b', text, re.I):
            warnings.append('current SKILL.md contains historical-status terms; verify they are not acting as current rules')

    for x in errors:
        print('ERROR:', x)
    for x in warnings:
        print('WARNING:', x)
    print(f'RESULT: {len(errors)} error(s), {len(warnings)} warning(s)')
    return 1 if errors else 0


if __name__ == '__main__':
    raise SystemExit(main())
