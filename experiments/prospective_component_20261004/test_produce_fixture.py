"""End-to-end source/frontend, actual wire, decoder and phase-file test on OLD development."""
import bootstrap
import unittest,tempfile,json,hashlib,shutil,sys,importlib.util
from pathlib import Path
from unittest.mock import patch
from fractions import Fraction as F
import fresh_io
from fresh_io import ROOT,E,read,sha,write
from fresh_inference import PRIMARY,state,infer,threshold
from fresh_transport import RUNTIME_SOURCES
from scores import load_models,current_scores
from fresh_inference import component
spec=importlib.util.spec_from_file_location('new_phase_producer_fixture',E/'produce.py');produce=importlib.util.module_from_spec(spec);spec.loader.exec_module(produce)
spec=importlib.util.spec_from_file_location('preflight_independent',E/'audit.py');ind=importlib.util.module_from_spec(spec);spec.loader.exec_module(ind)
class ActualPhaseFixture(unittest.TestCase):
    def test_old_source_to_actual_packets_and_stage_outputs(self):
        d=read(ROOT/'results/prospective_hypotheses_20261004/qualification_sheng.json');dev=read(ROOT/'results/component_expiry_20261004/development_sheng.json');models=load_models();registry={bp:dict(q,**dev['registry'][bp]) for bp,q in d['registry'].items()};seen=set();chosen=[]
        for r in d['rows']:
            status=r['prediction']['status']
            if status in ('supported','fallback','refused') and status not in seen:chosen.append(r);seen.add(status)
            if len(seen)==3:break
        self.assertEqual(len(chosen),3);dirs=read(ROOT/'experiments/pose_support_20261004/directions.json')['normal_xy']
        rows=[]
        for original in chosen:
            r=dict(original,split='test');bp=r['blueprint'];r['geometries']={m:infer(r['hulls_cm'],d['catalog'][bp],state(r['hulls_cm'],r['layout'],bp,models,m),threshold(registry,bp,m),m) for m in PRIMARY};ss=current_scores(r['hulls_cm'],d['catalog'][bp],r['prediction'],r['ridge_center_um'],r['true_xy']);ss.update(component.conformity(r['hulls_cm'],d['catalog'][bp],r['prediction'],r['true_xy']))
            self.assertEqual(ss,ind.scores(r['groups_cm'],r['hulls_cm'],d['catalog'][bp],r['prediction'],r['ridge_center_um'],r['true_xy'],dirs))
            for m,g in r['geometries'].items():
                expected=ind.geometry(r,m,ind.threshold(registry,bp,m),d['catalog'][bp],dirs);self.assertTrue(all(g[k]==v for k,v in expected.items()))
            rows.append(r)
        with tempfile.TemporaryDirectory(dir=ROOT/'results/prospective_component_20261004',prefix='.fixture-') as name:
            fixture=Path(name);(fixture/'capture/clouds').mkdir(parents=True);events=[];used=set()
            for r in rows:
                source=ROOT/'results/prospective_hypotheses_20261004/capture'/r['cloud_file'];dest=fixture/'capture'/r['cloud_file'];shutil.copyfile(source,dest)
                if r['episode_id'] not in used:events.append(dict(status='captured',episode=dict(id=r['episode_id'],blueprint=r['blueprint'],split='test')));used.add(r['episode_id'])
            for i in range(360-len(events)):events.append(dict(status='spawn_failed',episode=dict(id='fixture_empty_%03d'%i,blueprint=rows[0]['blueprint'],split='test')))
            sources={n:sha(ROOT/n) for n in RUNTIME_SOURCES};inputs={n:sha(ROOT/n) for n in ['results/calibrated_hypotheses_20261004/models_sheng.json','results/state_predictor_20261004/models_sheng.json']};write(fixture/'freeze.json',dict(sources=sources,inputs=inputs));write(fixture/'calibration_frozen.json',dict(registry=registry));q=dict(d,rows=rows,episodes=events,registry=registry,calibration_receipt_sha256=sha(fixture/'calibration_frozen.json'),model_freeze_sha256=sha(fixture/'freeze.json'),measurement_freeze_sha256=sha(fixture/'freeze.json'));write(fixture/'qualification_test_sheng.json',q)
            with patch.multiple(fresh_io,P=fixture,E=fixture),patch.multiple(produce,P=fixture,E=fixture),patch.object(sys,'argv',['produce.py','--split','test']):produce.main()
            paid=read(fixture/'paid_test_sheng.json');self.assertEqual(len(paid['traces']),360*48);self.assertEqual(len(paid['rows']),3)
            for row in paid['rows']:
                for v in row['methods'].values():
                    path=ROOT/v['packet'];self.assertEqual(sha(path),v['wire_sha256']);self.assertEqual(path.stat().st_size,v['wire_bytes']);self.assertLess(path.stat().st_size,10000)
            self.assertFalse((fixture/'paid_certification_sheng.json').exists());self.assertTrue((fixture/'setup_test.bin').exists())
if __name__=='__main__':unittest.main()
