"""Exact current-ray proposal shortcut and one full receiver verification."""
import hashlib,json,math,sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'body_evidence_20261001'))
import body
from renew import support
from strict import Receiver as ReferenceReceiver,within_deadline
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'policy_runtime_20261001'))
from local_renew import nearest
from proof import QUANTUM


def renew(template,points,origin,observed,reference,profiles,scope,contract,motion,prior,horizon=.4,sequence=0):
    try:
        w=support(template,tuple(profiles.items()),contract)
        o,r,ref=body.encode_source(points,origin,observed,reference)
        origins=o[r[:,0]]*QUANTUM;end=r[:,1:4]*QUANTUM
        valid=(origins[:,2]-contract.origin_error-QUANTUM/2>scope.plane_z+1e-9)&(end[:,2]+contract.point_error+QUANTUM/2<scope.plane_z-1e-9)
        ids=np.flatnonzero(valid);origins=origins[valid];end=end[valid]
        t=(origins[:,2]-scope.plane_z)/(origins[:,2]-end[:,2])
        current=((1-t[:,None])*origins[:,:2]+t[:,None]*end[:,:2]-scope.query)@body.rotation(motion.yaw)
        if not len(current) or not len(w):return None
        j,_=nearest(current,w);chosen=np.unique(ids[j])
        if not len(chosen) or len(chosen)>body.MAX_RAYS:return None
        raw=json.loads(body.serialize(o,r[chosen],ref,profiles,scope,contract,horizon,sequence))
        blob=body.canonical(dict(kind='body-evidence-v1',motion=body.asdict(motion),prior=prior.identity if prior else None,raw=raw))
        return blob if body.verify(blob,profiles,scope,contract,motion,prior,ref/body.TIME_SCALE,0) else None
    except (ValueError,TypeError,KeyError,OverflowError,IndexError):return None


class Receiver(ReferenceReceiver):
    def accept(self,blob,scope,motion,now):
        try:
            if scope.episode!=self.episode or scope.frame_id!=self.frame_id:return False
            packet=json.loads(blob);p=packet['raw']['payload'];prior_id=packet['prior']
            if prior_id is not None and p['reference_us']>=self._deadlines[prior_id]:return False
            reference=p['reference_us']/body.TIME_SCALE
            if reference<=self._last_reference or not within_deadline(blob,now,0):return False
            prior=self._prior(blob)
            if not body.verify(blob,self.profiles,scope,self.contract,motion,prior,now,0,self._last_sequence+1):return False
            end=p['reference_us']+p['horizon_us'];low,high,margin=body.envelope(motion,p['horizon_us']/body.TIME_SCALE,max(x.clock for x in self.profiles.values()))
            identity=hashlib.sha256(blob).hexdigest()
            region=body.Region(tuple(scope.query),motion.yaw,tuple(low),tuple(high),margin,reference,end/body.TIME_SCALE,identity,scope.episode)
            self._history[identity]=region;self._deadlines[identity]=end;self._last_reference=reference;self._last_sequence=p['sequence'];self._last_packet=identity
            return True
        except (ValueError,TypeError,KeyError,OverflowError,IndexError):return False
