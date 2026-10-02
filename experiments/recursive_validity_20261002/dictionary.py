"""Optional paid inter-message dictionary, common to every baseline."""
import collections,hashlib,json,zlib
import flow
body=flow.body;compact=flow.compact;METHODS=flow.METHODS
MAGIC=b'MOBIFLOW1\0'

def template(raw):
    q=compact.normalize(raw);return hashlib.sha256(body.canonical(q)).hexdigest(),q

class Sender:
    def __init__(self):self.templates=collections.OrderedDict()
    def encode(self,packet,index):
        if len(packet['steps'])!=1:raise ValueError('Single step')
        raw=packet['steps'][0];tid,q=template(raw)
        if tid not in self.templates or index%5==0:
            self.templates[tid]=q
            if len(self.templates)>4:self.templates.popitem(last=False)
            blob=MAGIC+b'F'+compact.encode(packet)
        else:
            p=raw['payload'];header={k:packet[k] for k in ['kind','dynamics','anchor']}
            value=dict(template_sha256=tid,header=header,step=[p['reference_us'],p['horizon_us'],p['sequence'],raw['sha256']])
            blob=MAGIC+b'R'+zlib.compress(body.canonical(value),1)
        if len(blob)>compact.LIMIT:raise ValueError('Wire limit')
        return blob

class Receiver(flow.Receiver):
    def reset(self,root_receipt_us):super().reset(root_receipt_us);self.templates=collections.OrderedDict()
    def advance(self,transport,started_us):
        if not isinstance(transport,bytes) or len(transport)>compact.LIMIT or not transport.startswith(MAGIC) or len(transport)<=len(MAGIC):raise ValueError('Dictionary transport')
        kind=transport[len(MAGIC):len(MAGIC)+1];inner=transport[len(MAGIC)+1:];new=None
        if kind==b'F':
            packet=compact.decode(inner)
            if len(packet['steps'])!=1:raise ValueError('Single step')
            new=template(packet['steps'][0])
        elif kind==b'R':
            z=zlib.decompressobj();data=z.decompress(inner,compact.LIMIT+1)
            if len(data)>compact.LIMIT or not z.eof or z.unused_data or z.unconsumed_tail:raise ValueError('Expansion')
            d=json.loads(data)
            if not isinstance(d,dict) or set(d)!={'template_sha256','header','step'} or not isinstance(d['header'],dict) or set(d['header'])!={'kind','dynamics','anchor'}:raise ValueError('Reference schema')
            row=d['step']
            if not isinstance(row,list) or len(row)!=4 or any(not compact.integer(x) for x in row[:3]) or not isinstance(row[3],str) or len(row[3])!=64:raise ValueError('Reference metadata')
            q=self.templates[d['template_sha256']];ref,h,seq,digest=row
            p=dict(q,reference_us=ref,horizon_us=h,sequence=seq);p['rays']=[r[:4]+[ref-r[4]] for r in q['rays']]
            packet=dict(d['header'],steps=[dict(payload=p,sha256=digest)]);inner=compact.encode(packet)
        else:raise ValueError('Dictionary type')
        result=super().advance(inner,started_us)
        if new:
            tid,q=new;self.templates[tid]=q
            if len(self.templates)>4:self.templates.popitem(last=False)
        return result
