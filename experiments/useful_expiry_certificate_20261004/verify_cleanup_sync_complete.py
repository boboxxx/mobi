#!/usr/bin/env python3
import argparse,ast,hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[2];P=R/'results/receiver_source_sync_20261005'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();assert not a.out.exists()
 original=(P/'original_recover_cleanup_sheng.py').read_bytes();canonical=(P/'canonical_recover_cleanup.py').read_bytes();assert original==canonical+b'\n' and ast.dump(ast.parse(original))==ast.dump(ast.parse(canonical));assert (R/'experiments/receiver_budget_live_20261004/recover_cleanup.py').read_bytes()==canonical
 d=json.loads((P/'source_sync.json').read_text());assert d['executed_original_sha256']==sha(P/'original_recover_cleanup_sheng.py') and d['canonical_sha256']==sha(P/'canonical_recover_cleanup.py') and d['ast_equal'] and not d['scientific_core_or_result_or_policy_changed']
 m=json.loads((P/'manifest.json').read_text())
 for name,h in m['files'].items():assert sha(R/name)==h,name
 result=dict(manifest_sha256=sha(P/'manifest.json'),canonical_sha256=sha(P/'canonical_recover_cleanup.py'),executed_original_sha256=sha(P/'original_recover_cleanup_sheng.py'),exactly_one_trailing_LF_difference=True,ast_equal=True,original_executed_source_preserved=True,canonical_publication_bytes_verified=True)
 a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print('CLEANUP_SOURCE_FORMAT_PRESERVATION_OK')
if __name__=='__main__':main()
