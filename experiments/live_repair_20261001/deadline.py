"""Strict integer expiry, including conservative reservation of the next tick."""
import math
from fractions import Fraction


def usable(expiry_us, available_s, execution_us=0):
    if type(expiry_us) is not int or type(execution_us) is not int or execution_us < 0:
        raise ValueError('Integer deadline and nonnegative execution bound required')
    if not math.isfinite(available_s):
        raise ValueError('Finite availability time required')
    arrival = math.ceil(Fraction.from_float(float(available_s))*1_000_000)
    return arrival + execution_us < expiry_us


def next_sample_ready(expiry_us, available_s, max_tick_us=50_001):
    # CARLA's observed 50 ms step is slightly longer than .05 as a float.
    # Reservation is prospective only; the actual new reference is still checked.
    return usable(expiry_us, available_s, max_tick_us)
