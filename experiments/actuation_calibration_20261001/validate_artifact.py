"""Verify archived capture identities, frozen sources and reported counts."""
import argparse,csv,hashlib,io,json,platform,socket,sys,tarfile
from pathlib import Path
import numpy,scipy


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);a=ap.parse_args()
    p=a.results;src=Path(__file__).resolve().parent;root=src.parents[1]
    m=json.loads((p/'analysis/manifest.json').read_text())
    for name,digest in m['source_sha256'].items():assert sha(src/name)==digest,name
    assert sha(src/'PROTOCOL.md')==m['protocol_sha256']
    assert sha(p/'capture/manifest.json')==m['capture_manifest_sha256']
    assert sha(p/'capture/summary.csv')==m['capture_summary_sha256']
    packet=root/'results/policy_runtime_20261001/binary/packets/dense_0_free_03_v0.5_h0.4.pvx'
    assert sha(packet)==m['packet_sha256']
    final=list(csv.DictReader((p/'capture/summary.csv').open()));assert len(final)==799
    for r in final:assert sha(p/'capture/episodes'/(r['id']+'.json.gz'))==r['sha256']
    with tarfile.open(p/'preliminary_yaw_only.tgz') as t:
        prefix='preliminary_yaw_only/'
        early=list(csv.DictReader(io.StringIO(t.extractfile(prefix+'summary.csv').read().decode())))
        assert len(early)==799
        for r in early:assert hashlib.sha256(t.extractfile(prefix+'episodes/'+r['id']+'.json.gz').read()).hexdigest()==r['sha256']
        assert json.loads(t.extractfile(prefix+'plan.json').read())==json.loads((p/'capture/plan.json').read_text())
    report=json.loads((p/'analysis/report.json').read_text());pred=list(csv.DictReader((p/'analysis/test_predictions.csv').open()))
    ticks=json.loads((p/'tick_realization.json').read_text());tr=list(csv.DictReader((p/'tick_realization.csv').open()))
    for kind in ['constant','state']:
        r=[x for x in pred if x['kind']==kind];assert len(r)==400
        assert sum(x['joint_exceedance']=='True' for x in r)==report['methods'][kind]['joint_exceedances']
        assert sum(x['counterfactual_admit']=='True' for x in r)==report['methods'][kind]['counterfactual_admissions']
        q=[x for x in tr if x['kind']==kind];assert len(q)==400
        assert sum(x['joint_exceedance']=='True' for x in q)==ticks['methods'][kind]['joint_exceedances']
    assert report['methods']['constant']['joint_exceedances']==0 and report['methods']['state']['joint_exceedances']==7
    assert json.loads((p/'server_cleanup.json').read_text())['own_server_remaining'] is False
    assert 'Ran 8 tests' in (p/'tests_final.log').read_text() and 'OK' in (p/'tests_final.log').read_text()
    sys.path.insert(0,str(src.parents[0]/'lease_handoff_20261001'))
    import lease
    deps={}
    for mod in list(sys.modules.values()):
        f=getattr(mod,'__file__',None)
        if f:
            q=Path(f).resolve()
            if q.is_file() and root in q.parents and q.suffix=='.py':deps[str(q.relative_to(root))]=sha(q)
    for q in src.glob('*'):
        if q.is_file():deps[str(q.relative_to(root))]=sha(q)
    deps[str(packet.relative_to(root))]=sha(packet)
    (p/'dependencies.json').write_text(json.dumps(deps,indent=2,sort_keys=True)+'\n')
    result=dict(host=socket.gethostname(),python=platform.python_version(),numpy=numpy.__version__,scipy=scipy.__version__,final_raw_episode_hashes=799,excluded_preliminary_raw_episode_hashes=799,identical_request_plans=True,frozen_analysis_sources_verified=True,primary_state_failures_retained=7,tests=8,owned_server_stopped=True,physical_movement_authorized=False,validation='passed')
    (p/'validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
