import copy,hashlib,unittest,zlib
import dictionary as wire
import test_flow

class DictionaryTests(unittest.TestCase):
    def fixture(self):
        f,old,packet=test_flow.FlowTests().fixture();rx=wire.Receiver('fine_terminal',f.profiles,f.contract,{n:2.5 for n in f.profiles});rx.register(f.legacy,f.initial,f.scope,f.motion);rx.reset(10000)
        return f,rx,packet,wire.Sender()
    def test_received_full_reference_restore_exact_facts_and_pay_rebuild(self):
        f,rx,packet,tx=self.fixture();first=tx.encode(packet(.15,1),20);rx.advance(first,200000);rx.finish(210000)
        ref=tx.encode(packet(.3,2),21);self.assertLess(len(ref),len(first));d,s=rx.advance(ref,400000);rx.finish(410000)
        self.assertTrue(d['fact_accepted']);self.assertEqual(s.reference_us,300000)
        full=tx.encode(packet(.45,3),25);self.assertEqual(full[len(wire.MAGIC):len(wire.MAGIC)+1],b'F')
    def test_lost_initial_full_reference_refused_without_fact_or_authority_change(self):
        f,rx,packet,tx=self.fixture();tx.encode(packet(.15,1),20);ref=tx.encode(packet(.3,2),21);before=rx.authority
        with self.assertRaises(KeyError):rx.advance(ref,400000)
        self.assertEqual(rx.ref,rx.anchor.reference_us);self.assertEqual(rx.authority,before);self.assertFalse(rx.templates)
        full=tx.encode(packet(.45,3),25);d,s=rx.advance(full,500000);rx.finish(510000);self.assertTrue(d['fact_accepted'])
    def test_changed_geometry_requires_full_and_corrupt_full_cannot_poison_dictionary(self):
        f,rx,packet,tx=self.fixture();b=packet(.15,1);b['steps'][0]['payload']['rays'][0][1]+=1
        broken=tx.encode(b,21)
        with self.assertRaises(ValueError):rx.advance(broken,200000)
        self.assertFalse(rx.templates)
        raw=b['steps'][0];raw['sha256']=hashlib.sha256(wire.body.canonical(raw['payload'])).hexdigest();tx=wire.Sender();good=tx.encode(b,21);rx.advance(good,200000);rx.finish(210000)
        changed=tx.encode(packet(.3,2),22);self.assertEqual(changed[len(wire.MAGIC):len(wire.MAGIC)+1],b'F');rx.advance(changed,400000);rx.finish(410000);self.assertEqual(len(rx.templates),2)
    def test_reference_checksum_replay_future_and_expansion_refused(self):
        f,rx,packet,tx=self.fixture();rx.advance(tx.encode(packet(.15,1),20),200000);rx.finish(210000);ref=tx.encode(packet(.3,2),21)
        with self.assertRaises(ValueError):rx.advance(ref,250000)
        data=ref[len(wire.MAGIC)+1:];d=wire.compact.json.loads(zlib.decompress(data));d['step'][3]='0'*64
        with self.assertRaises(ValueError):rx.advance(wire.MAGIC+b'R'+zlib.compress(wire.body.canonical(d)),400000)
        for bad in [ref+b'x',ref[:-1],wire.MAGIC+b'R'+zlib.compress(b' '*(wire.compact.LIMIT+1))]:
            with self.assertRaises(ValueError):rx.advance(bad,400000)
        rx.advance(ref,400000);rx.finish(410000)
        with self.assertRaises(ValueError):rx.advance(ref,420000)
        rx.reset(10000);self.assertFalse(rx.templates)
if __name__=='__main__':unittest.main()
