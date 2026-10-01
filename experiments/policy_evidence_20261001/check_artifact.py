#!/usr/bin/env python3
"""Bounded server-side validation; no simulator or background jobs started."""
import argparse,hashlib,json,platform,socket,subprocess,sys
from pathlib import Path
import numpy,scipy


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);ap.add_argument('--capture',type=Path,required=True);a=ap.parse_args()
    repo=Path(__file__).resolve().parents[2];src=Path(__file__).parent
    deps=json.loads((a.results/'dependencies.json').read_text())
    for relative,digest in deps['source_sha256'].items():assert hashlib.sha256((repo/relative).read_bytes()).hexdigest()==digest,relative
    for name,digest in deps['input_sha256'].items():assert hashlib.sha256((a.capture/name).read_bytes()).hexdigest()==digest,name
    commands=[['-m','unittest','discover','-s',str(src)], [str(src/'analyze_actuation.py'),'--results',str(a.results)], [str(src/'validate.py'),'--results',str(a.results),'--capture',str(a.capture)]]
    runs=[]
    for command in commands:
        process=subprocess.run([sys.executable]+command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,cwd=str(repo),timeout=180)
        runs.append(dict(command=command,exit_code=process.returncode,output=process.stdout))
        print(process.stdout,flush=True)
        if process.returncode:raise RuntimeError('Artifact validation failed')
    report=dict(host=socket.gethostname(),platform=platform.platform(),python=sys.version,numpy=numpy.__version__,scipy=scipy.__version__,dependencies_verified=True,runs=runs,validation='passed')
    (a.results/'sheng_validation.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
