#!/usr/bin/env python3
import argparse,hashlib,json,platform,socket,subprocess,sys
from pathlib import Path
import numpy,scipy


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);ap.add_argument('--capture',type=Path,required=True);ap.add_argument('--previous',type=Path,required=True);a=ap.parse_args();repo=Path(__file__).resolve().parents[2];src=Path(__file__).parent
    d=json.loads((a.results/'dependencies.json').read_text())
    for name,digest in d['source_sha256'].items():assert hashlib.sha256((repo/name).read_bytes()).hexdigest()==digest,name
    for name,digest in d['input_sha256'].items():assert hashlib.sha256((a.capture/name).read_bytes()).hexdigest()==digest,name
    for name,digest in d['previous_sha256'].items():assert hashlib.sha256((a.previous/name).read_bytes()).hexdigest()==digest,name
    commands=[['-m','unittest','discover','-s',str(src)], [str(src/'analyze_execution.py'),'--results',str(a.results)], [str(src/'validate.py'),'--results',str(a.results),'--capture',str(a.capture),'--previous',str(a.previous)]];runs=[]
    for args in commands:
        p=subprocess.run([sys.executable]+args,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,cwd=str(repo),timeout=300);runs.append(dict(command=args,exit_code=p.returncode,output=p.stdout));print(p.stdout,flush=True)
        if p.returncode:raise RuntimeError('Validation failed')
    data=dict(host=socket.gethostname(),platform=platform.platform(),python=sys.version,numpy=numpy.__version__,scipy=scipy.__version__,validation='passed',dependencies_verified=True,runs=runs)
    (a.results/'sheng_validation.json').write_text(json.dumps(data,indent=2)+'\n')


if __name__=='__main__':main()
