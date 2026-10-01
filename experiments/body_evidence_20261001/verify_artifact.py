#!/usr/bin/env python3
"""Run final saved-artifact checks and record the exact final receiver sources."""
import argparse,hashlib,json,platform,subprocess,sys
from pathlib import Path
import numpy,scipy


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);ap.add_argument('--capture',type=Path,required=True);a=ap.parse_args();src=Path(__file__).resolve().parent
    expected=json.loads((a.results/'analysis.json').read_text())
    commands=[[sys.executable,str(src/'analyze.py'),'--results',str(a.results),'--capture',str(a.capture)],
              [sys.executable,'-m','unittest','discover','-s',str(src)]]
    for command,name in zip(commands,['server_validation.log','final_tests.log']):
        r=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        (a.results/name).write_text(r.stdout+r.stderr);r.check_returncode()
    assert json.loads((a.results/'analysis.json').read_text())==expected
    manifest=dict(validation='passed',matches_uploaded_analysis=True,python=sys.version,numpy=numpy.__version__,scipy=scipy.__version__,platform=platform.platform(),source_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(src.iterdir()) if p.suffix in ['.py','.md'] and not p.name.startswith('._')})
    (a.results/'server_validation.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(manifest),flush=True)


if __name__=='__main__':main()
