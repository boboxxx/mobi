"""Post-measurement strict receipt-time guard; measured source stays frozen."""
from fractions import Fraction
import json,math
import policy_proof as measured


def verify(blob,profiles,scope,contract,policy,speed,yaw,now,min_sequence=0):
    try:
        packet=json.loads(blob);ref=packet['raw']['payload']['reference_us']
        if type(ref) is not int or not math.isfinite(now):return False
        if Fraction.from_float(float(now))*measured.TIME_SCALE<ref:return False
        if type(packet['speed']) not in (float,int) or type(packet['yaw']) not in (float,int):return False
        return measured.verify(blob,profiles,scope,contract,policy,speed,yaw,now,min_sequence)
    except (ValueError,TypeError,KeyError,OverflowError):return False


def conditional_stop_gate(blob,profiles,scope,contract,policy,speed,yaw,now):
    return verify(blob,profiles,scope,contract,policy,speed,yaw,now) and measured.conditional_stop_gate(blob,profiles,scope,contract,policy,speed,yaw,now)
