import argparse
import copy
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'experiments/action_window_reference_20261011'))
import kernel as k

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);args=ap.parse_args()
    base=ROOT/'results/transactions_diagnostic_20261011'
    manifest=json.loads((base/'package_manifest.json').read_text())
    for name,v in manifest['files'].items():
        p=ROOT/name;assert p.is_file(),name
        raw=p.read_bytes();assert len(raw)==v['bytes'] and hashlib.sha256(raw).hexdigest()==v['sha256'],name
    for unit in ('action_window_reference_20261011','temporal_action_window_20261011'):
        r=ROOT/'results'/unit
        assert (r/'local/scientific.json').read_bytes()==(r/'sheng/scientific.json').read_bytes()
    a=json.loads((base/'audit_local.json').read_text());b=json.loads((base/'audit_sheng.json').read_text())
    for d in (a,b):
        assert d['status']=='PASS'
        for receipt in d['input_receipts']:
            path=ROOT/receipt.pop('path');assert hashlib.sha256(path.read_bytes()).hexdigest()==receipt['sha256']
    assert a==b
    first=json.loads((ROOT/'results/action_window_reference_20261011/local/scientific.json').read_text())
    for p in first['profiles']:
        allowed=[False]*17
        for lo,hi in p['valid_start_age_segments']:allowed[lo:hi+1]=[True]*(hi-lo+1)
        for host in ('local','sheng'):
            for packet_name in p['packets']:
                raw=(ROOT/'results/action_window_reference_20261011'/host/packet_name).read_bytes()
                decoded=k.decode(raw)
                assert decoded['allowed']==allowed and decoded['source']==1_000_000 and decoded['tick']==50_000
                assert decoded['length']==p['length'] and decoded['alpha']==F(p['alpha'])
                assert decoded['digest']==k.context_digest(p['observation'])
                expected=p['bitmap_bytes'] if '_bitmap' in packet_name else p['interval_bytes']
                assert len(raw)==expected
    assert (ROOT/'results/action_window_reference_20261011/tests_local.txt').read_text().strip().endswith('OK')
    assert (ROOT/'results/action_window_reference_20261011/tests_sheng.txt').read_text().strip().endswith('OK')
    for host in ('local','sheng'):
        assert (base/('codec_'+host+'.txt')).read_text().strip()=='SUPPLEMENTAL_CODEC_CONTRACT_CHECKS_PASS 13'
    for unit,expected in [('action_window_reference_20261011','FINITE_ACTION_WINDOW_REFERENCE_COMPLETE'),('temporal_action_window_20261011','FINITE_TEMPORAL_ACTION_WINDOW_COMPLETE')]:
        assert (ROOT/'results'/unit/'terminal_sheng.txt').read_text().strip()==expected
    result=dict(status='PASS',files_verified=len(manifest['files']),bytes_verified=sum(v['bytes'] for v in manifest['files'].values()),
                scientific_outputs='both batches byte-identical across hosts',
                independent_audit='identical after validating and removing only host-relative input paths',
                synthetic_only=True)
    raw=json.dumps(result,sort_keys=True,indent=2)+'\n'
    path=Path(args.out)
    if path.exists():assert path.read_text()==raw
    else:path.write_text(raw)
    print(json.dumps(result,sort_keys=True))

if __name__=='__main__':main()
