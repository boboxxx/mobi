"""Integer-microsecond deadline guard for the production receiver entry point.

Keep original measured implementations frozen. Round both receipt time and
execution duration upward, using exact arithmetic on the supplied float values.
"""
from fractions import Fraction
from dataclasses import replace
import json,math
import body
from history import Receiver as OriginalReceiver
from stopping import Stopping


def within_deadline(blob,now,execution):
    try:
        if not math.isfinite(now) or not math.isfinite(execution) or execution<0:return False
        p=json.loads(blob)['raw']['payload'];ref=p['reference_us'];h=p['horizon_us']
        if type(ref) is not int or type(h) is not int:return False
        received=math.ceil(Fraction.from_float(float(now))*body.TIME_SCALE)
        action=math.ceil(Fraction.from_float(float(execution))*body.TIME_SCALE)
        return received+action<ref+h
    except (ValueError,TypeError,KeyError,OverflowError):return False


def verify(blob,profiles,scope,contract,motion,prior,now,execution,min_sequence=0):
    return within_deadline(blob,now,execution) and body.verify(blob,profiles,scope,contract,motion,prior,now,execution,min_sequence)


def admit(blob,profiles,scope,contract,motion,prior,now,stopping=Stopping()):
    if motion.acceleration<max(stopping.traction_upper,stopping.braking_upper):return False
    try:
        reference=json.loads(blob)['raw']['payload']['reference_us']/body.TIME_SCALE
        execution=body.action_duration(math.hypot(motion.vx,motion.vy),now-reference,stopping.traction_upper,stopping.braking_lower,stopping.control,stopping.reaction)
        return verify(blob,profiles,scope,contract,motion,prior,now,execution)
    except (ValueError,TypeError,KeyError,OverflowError):return False


class Receiver(OriginalReceiver):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs);self._deadlines={}

    def accept(self,blob,scope,motion,now):
        try:
            packet=json.loads(blob);p=packet['raw']['payload'];prior_id=packet['prior']
            if prior_id is not None and p['reference_us']>=self._deadlines[prior_id]:return False
            if not (within_deadline(blob,now,0) and super().accept(blob,scope,motion,now)):return False
            end=p['reference_us']+p['horizon_us'];self._deadlines[self._last_packet]=end
            old=self._history[self._last_packet]
            self._history[self._last_packet]=replace(old,expires=end/body.TIME_SCALE)
            return True
        except (ValueError,TypeError,KeyError,OverflowError):return False

    def allows_action(self,blob,scope,motion,now,stopping=Stopping()):
        try:
            return super().allows_action(blob,scope,motion,now,stopping) and admit(blob,self.profiles,scope,self.contract,motion,self._prior(blob),now,stopping)
        except (ValueError,TypeError,KeyError,OverflowError):return False
