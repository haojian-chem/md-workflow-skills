#!/usr/bin/env python3
from pathlib import Path
import argparse, re, hashlib

def blocks(text):
    text=re.sub(r'```.*?```','',text,flags=re.S)
    return [re.sub(r'\s+',' ',x).strip() for x in re.split(r'\n\s*\n',text) if len(re.sub(r'\s+',' ',x).strip())>=120]

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('root',type=Path); a=ap.parse_args(); seen={}; findings=[]
    for p in a.root.rglob('*'):
        if p.is_file() and p.suffix.lower() in {'.md','.yaml','.yml'}:
            for b in blocks(p.read_text(encoding='utf-8',errors='replace')):
                h=hashlib.sha256(b.encode()).hexdigest()
                if h in seen and seen[h]!=p: findings.append((seen[h],p,b[:100]))
                else: seen[h]=p
    for a1,a2,s in findings: print(f'WARNING: duplicate block: {a1} <-> {a2}: {s}')
    print(f'RESULT: {len(findings)} duplicate block(s)')
    return 0
if __name__=='__main__': raise SystemExit(main())
