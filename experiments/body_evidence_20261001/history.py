"""Receiver-owned history; packets cannot install a free-region assertion."""
import hashlib,json
from body import verify,established_region,TIME_SCALE
from stopping import admit


class Receiver:
    def __init__(self,profiles,contract,episode,frame_id):
        self.profiles=dict(profiles);self.contract=contract
        self.episode=episode;self.frame_id=frame_id
        self._history={};self._last_reference=float('-inf');self._last_sequence=-1;self._last_packet=None

    def _prior(self,blob):
        identity=json.loads(blob)['prior']
        return None if identity is None else self._history[identity]

    def accept(self,blob,scope,motion,now):
        try:
            if scope.episode!=self.episode or scope.frame_id!=self.frame_id:return False
            p=json.loads(blob)['raw']['payload'];reference=p['reference_us']/TIME_SCALE
            if reference<=self._last_reference:return False
            prior=self._prior(blob)
            if not verify(blob,self.profiles,scope,self.contract,motion,prior,now,0,self._last_sequence+1):return False
            region=established_region(blob,self.profiles,scope,self.contract,motion,prior,now)
            self._history[region.identity]=region;self._last_reference=reference;self._last_sequence=p['sequence'];self._last_packet=region.identity
            return True
        except (ValueError,TypeError,KeyError,IndexError,OverflowError):return False

    def allows_action(self,blob,scope,motion,now,stopping):
        try:
            if scope.episode!=self.episode or scope.frame_id!=self.frame_id or hashlib.sha256(blob).hexdigest()!=self._last_packet:return False
            return admit(blob,self.profiles,scope,self.contract,motion,self._prior(blob),now,stopping)
        except (ValueError,TypeError,KeyError,IndexError,OverflowError):return False

    def latest_region(self):
        return self._history.get(self._last_packet)
