"""Verify explicit publication files, immutable inputs, and all archived raw bytes."""
import argparse,hashlib,json,tarfile
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--manifest',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();assert not a.out.exists()
sha=lambda b:hashlib.sha256(b).hexdigest()
m=json.loads(a.manifest.read_bytes())
for name,item in m['files'].items():
 q=Path(name);assert not q.is_absolute() and '..' not in q.parts
 b=q.read_bytes();assert len(b)==item['bytes'] and sha(b)==item['sha256'],name
counts={}
for unit in m['units']:
 e=Path('experiments')/unit;v=Path('results')/unit;f=json.loads((e/'freeze.json').read_bytes())
 for section in ('sources','inputs'):
  for name,digest in f[section].items():assert sha(Path(name).read_bytes())==digest,name
 raw=json.loads((v/'raw_archives/raw_manifest.json').read_bytes());seen=set();cleanup=None
 for name,item in raw['archives'].items():
  archive=v/'raw_archives'/name;b=archive.read_bytes();assert len(b)==item['bytes'] and sha(b)==item['sha256'],name
  with tarfile.open(archive,'r:xz') as t:
   for member in t:
    q=Path(member.name);assert member.isfile() and not q.is_absolute() and '..' not in q.parts and member.name not in seen
    b=t.extractfile(member).read();i=raw['files'][member.name];assert i['archive']==name and len(b)==i['bytes'] and sha(b)==i['sha256'],member.name
    if member.name=='capture/cleanup.json':cleanup=json.loads(b)
    seen.add(member.name)
 assert seen==set(raw['files'])
 assert cleanup==dict(sensors=0,synchronous=False,vehicles=0,walkers=0)
 c=json.loads((v/'cross_host.json').read_bytes());assert c['status']=='PASS' and c['all_discrete_values_identical']
 owner=json.loads((v/'server_ownership.json').read_bytes());stop=json.loads((v/'stopped_ownership.json').read_bytes());assert stop['stopped'] and stop['experiment']==unit
 for key in ('pid','executable','start_time_utc'):assert owner[key]==stop[key]
 counts[unit]=len(seen)
r=dict(status='PASS',manifest_sha256=sha(a.manifest.read_bytes()),files=len(m['files']),published_bytes=sum(i['bytes'] for i in m['files'].values()),all_original_freezes_verified=True,raw_files_verified=counts,owned_servers_stopped=True)
a.out.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n');print(json.dumps(r,sort_keys=True))
