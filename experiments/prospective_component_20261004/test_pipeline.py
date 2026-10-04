import bootstrap
import unittest,hashlib,importlib.util
from fractions import Fraction as F
from fresh_io import ROOT,E,read,canon,sha
from fresh_inference import PRIMARY,state,infer,threshold
from fresh_transport import registration,compress,decode_setup,encode,decode,RUNTIME_SOURCES
from scores import load_models
from make_plan import plan
spec=importlib.util.spec_from_file_location('conditional_tests',ROOT/'experiments/balanced_expiry_20261004/conditional.py');stats=importlib.util.module_from_spec(spec);spec.loader.exec_module(stats)
class Pipeline(unittest.TestCase):
    def test_independent_plan_and_selector(self):
        pp=plan();self.assertEqual(pp,read(E/'plan.json'));self.assertEqual(len(pp),2520);cert=[e for e in pp if e['split']=='certification'];self.assertEqual(len(cert),600)
        self.assertTrue(all(0<=e['selected_query_index']<32 for e in cert));self.assertEqual(len({e['selected_query_index'] for e in cert}),32)
        for bp in read(E/'catalog.json'):
            self.assertEqual(sum(e['split']=='calibration' and e['blueprint']==bp for e in pp),260)
            self.assertEqual(sum(e['split']=='test' and e['blueprint']==bp for e in pp),60)
    def test_union_confidence_with_all_controls(self):
        self.assertLessEqual(18*F(39,40)**260+24*F(19,20)**260,F(1,40))
        self.assertGreater(18*F(39,40)**259+24*F(19,20)**259,F(1,40))
    def test_selected_query_zero_failure_sample_requirement(self):
        self.assertEqual(stats.zero_failure_required(F(1,20),F(1,40),96),161)
        self.assertFalse(stats.certificate([True]*160,[False]*160,delta=F(1,40),policies=96)['accepted'])
        self.assertTrue(stats.certificate([True]*161,[False]*161,delta=F(1,40),policies=96)['accepted'])
    def test_same_inference_function_deadline_and_source_epoch(self):
        d=read(ROOT/'results/prospective_hypotheses_20261004/qualification_sheng.json');dev=read(ROOT/'results/component_expiry_20261004/development_sheng.json');registry={bp:dict(q,**dev['registry'][bp]) for bp,q in d['registry'].items()};fake=dict(d,registry=registry);models=load_models();freeze=dict(sources={n:sha(ROOT/n) for n in RUNTIME_SOURCES},inputs={})
        ctx=registration(fake,'a'*64,freeze);contract=hashlib.sha256(canon(ctx)).hexdigest();self.assertEqual(decode_setup(compress(ctx),contract),ctx)
        wanted={bp:{'supported','fallback','refused'} for bp in d['catalog']};chosen=[]
        for r in d['rows']:
            status=r['prediction']['status']
            if status in wanted[r['blueprint']]:wanted[r['blueprint']].remove(status);chosen.append(r)
        self.assertTrue(any(r['prediction']['status']=='fallback' for r in chosen))
        self.assertTrue(any(not r['hulls_cm'] for r in chosen))
        for r in chosen:
            for family in PRIMARY:
                hyp=state(r['hulls_cm'],r['layout'],r['blueprint'],models,family);g=infer(r['hulls_cm'],d['catalog'][r['blueprint']],hyp,threshold(registry,r['blueprint'],family),family)
                outputs=[decode(encode(r,family,k,r['hulls_cm'],hyp,ctx,contract),family,k,ctx,contract) for k in ('function','deadline')]
                self.assertEqual(outputs[0],outputs[1]);self.assertEqual(outputs[0]['lower_us'],g['lower_us']);self.assertEqual(outputs[0]['source_us'],r['source_us'])
        with self.assertRaises(Exception):decode_setup(b'corrupt',contract)
if __name__=='__main__':unittest.main()
