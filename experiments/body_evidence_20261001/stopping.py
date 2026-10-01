"""Joint consistency of body-motion and stopping contracts."""
from dataclasses import dataclass,asdict
import json,math
from body import verify,action_duration,TIME_SCALE


@dataclass(frozen=True)
class Stopping:
    traction_upper: float=3.
    braking_lower: float=4.
    braking_upper: float=8.
    control: float=.05
    reaction: float=.02

    def __post_init__(self):
        if not all(math.isfinite(x) and x>=0 for x in asdict(self).values()) or self.braking_lower<=0 or self.braking_lower>self.braking_upper:raise ValueError('Invalid stopping contract')


def admit(blob,profiles,scope,contract,motion,prior,now,stopping=Stopping()):
    if motion.acceleration<max(stopping.traction_upper,stopping.braking_upper):return False
    try:
        reference=json.loads(blob)['raw']['payload']['reference_us']/TIME_SCALE
        age=now-reference
        execution=action_duration(math.hypot(motion.vx,motion.vy),age,stopping.traction_upper,stopping.braking_lower,stopping.control,stopping.reaction)
        return verify(blob,profiles,scope,contract,motion,prior,now,execution)
    except (ValueError,TypeError,KeyError,OverflowError):return False
