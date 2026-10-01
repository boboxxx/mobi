"""Conservative 1D boundary reachability under explicit supplied bounds.

Not a CARLA safety certificate: valid coverage and free-space detection must be
established externally. Endpoint ground hits alone cannot prove continuous space.
"""
import math


def lifetime(empty_length, position_error, speed_bound, acceleration_bound,
             clock_error=0., covered=True, observed_free=True):
    if min(position_error, speed_bound, acceleration_bound, clock_error) < 0:
        raise ValueError('Bounds must be nonnegative')
    if not covered or not observed_free:
        return 0.
    distance = empty_length-position_error
    if distance <= 0:
        return 0.
    if acceleration_bound > 0:
        # Stable positive root of v*t + a*t^2/2 = distance.
        crossing = 2*distance/(speed_bound+math.sqrt(speed_bound**2+2*acceleration_bound*distance))
    elif speed_bound > 0:
        crossing = distance/speed_bound
    else:
        crossing = math.inf
    return max(0., crossing-clock_error)


def supports(produced_at, received_at, commit_at, duration, validity):
    if not produced_at <= received_at <= commit_at or duration < 0:
        return False
    return commit_at+duration < produced_at+validity
