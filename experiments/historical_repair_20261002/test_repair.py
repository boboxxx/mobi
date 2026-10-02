import copy,json,unittest
import numpy as np
import context,repair,backward
G=repair.G;body=repair.body
class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.ctx=context.load('c0_view0_reference_rate20')
    def failed(self,mode='scalar',feedback='backward'):
        c=self.ctx;rx=context.receiver(c,mode,repair.ref(c['root'])+1000,feedback);source=repair.Source(c['profiles'],c['contract'],rx.core.anchor);source.add(c['root'],c['capture']/'clouds'/(c['root_identity']+'.npz'),c['root_decision']['stamp']);sender=G.dictionary.Sender()
        for i in range(20,23):
            raw=c['original'][i];source.add(raw,c['capture']/'clouds'/('drive_%03d.npz'%i),c['decisions']['drive_%03d'%i]['stamp']);wire=sender.encode(dict(kind='position-flow-v1' if mode=='fine' else 'class-guard-flow-v1',dynamics='observation-speed-age-v1',anchor=rx.core.anchor.identity,steps=[raw]),i);d,_=rx.normal(wire,raw,repair.ref(raw)+1000);rx.normal_finish(repair.ref(raw)+2000,d)
        self.assertEqual(d['horizon_us'],0);q=rx.request(raw);return rx,source,q,repair.ref(raw)+10000
    def test_real_historical_repair_and_expired_action(self):
        for mode in ('scalar','fine'):
            rx,s,q,start=self.failed(mode);reply,stats=s.reply(q);d,_=rx.reply(reply,start);self.assertGreaterEqual(d['horizon_us'],475000);self.assertFalse(rx.core.can_act(start,1000));rx.reply_finish(start+600000);self.assertFalse(rx.core.can_act(start+600000,1000));self.assertEqual(rx.core.seen_ref,repair.ref(self.ctx['original'][22]));self.assertEqual(stats['transitions'][0]['selection']['rays'],129)
            with self.assertRaises(ValueError):rx.reply(reply,start+700000)
    def test_backfill_cannot_invent_untransmitted_rays(self):
        rx,s,q,start=self.failed(feedback='backfill');reply,_=s.reply(q);d,_=rx.reply(reply,start);self.assertEqual(d['horizon_us'],0);self.assertEqual(d['reason'],'replay_unproved')
    def test_reply_request_binding(self):
        rx,s,q,start=self.failed();reply,_=s.reply(q);v=repair.unpack(reply);v['request']='0'*64
        with self.assertRaises(ValueError):rx.reply(repair.pack(v),start)
        self.assertIsNotNone(rx.inflight)
    def test_changed_fragment_rejected(self):
        rx,s,q,start=self.failed();reply,_=s.reply(q);v=repair.unpack(reply);v['patches'][0]['fragment']['payload']['rays'][0][1]+=1
        before=rx.core.ref
        with self.assertRaises(ValueError):rx.reply(repair.pack(v),start)
        self.assertEqual(rx.core.ref,before)
    def test_valid_checksum_but_insufficient_fragment_rejected(self):
        rx,s,q,start=self.failed();reply,_=s.reply(q);v=repair.unpack(reply);raw=v['patches'][0]['fragment'];p,o,r=body.decode(body.canonical(raw),rx.core.profiles,rx.core.anchor.scope,rx.core.contract);v['patches'][0]['fragment']=json.loads(body.serialize(o,r[:1],p['reference_us'],rx.core.profiles,rx.core.anchor.scope,rx.core.contract,.475,p['sequence']))
        with self.assertRaises(ValueError):rx.reply(repair.pack(v),start)
    def test_cache_eviction_fails_closed(self):
        rx,s,q,start=self.failed()
        for i in range(23,32):s.add(self.ctx['original'][i],None,0)
        self.assertEqual(len(s.cache),8);reply,_=s.reply(q);d,_=rx.reply(reply,start);self.assertEqual(d['reason'],'cache_miss');self.assertEqual(d['horizon_us'],0)
    def test_stale_parent_is_not_rolled_back(self):
        rx,s,q,start=self.failed();reply,_=s.reply(q);rx.parent=self.ctx['original'][22];before=rx.core.ref;d,_=rx.reply(reply,start);self.assertEqual(d['reason'],'stale_parent');self.assertEqual(rx.core.ref,before)
    def test_unknown_exterior_and_exact_preimage_against_boxes(self):
        g=body.Profile(domain=1.,step=.1,r_min=.1,r_max=.2,query_radius=0);cells=np.array([[.05,.05],[-.25,.15]]);d=.213
        pred=backward.predecessors(cells,g,d);grid=body.grid(g.domain,g.step)[0];dist=np.linalg.norm(np.maximum(np.abs(grid[:,None,:]-cells[None,:,:])-g.step,0),axis=2).min(axis=1);np.testing.assert_array_equal(pred.ravel(),dist<=d+1e-9);self.assertIsNone(backward.predecessors(np.array([[.95,.05]]),g,.1))
    def test_bounded_decompression_and_trailing_data(self):
        wire=repair.pack(dict(a=1))
        with self.assertRaises(ValueError):repair.unpack(wire+b'extra')
    def test_one_request_and_unchanged_geometry_suppression(self):
        rx,s,q,start=self.failed(feedback='backfill');self.assertIsNone(rx.request(self.ctx['original'][22]));reply,_=s.reply(q);rx.reply(reply,start);self.assertIsNone(rx.request(self.ctx['original'][22]))
if __name__=='__main__':unittest.main()
