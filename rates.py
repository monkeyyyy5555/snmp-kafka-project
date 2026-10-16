MOD = 2**32

class Rates:
    """Conservative Counter32 rate calculation using monotonic elapsed time."""
    def __init__(self):
        self.previous = {}

    def reset(self, key):
        self.previous.pop(key, None)

    def sample(self, key, counters, now, uptime, discontinuity, speed):
        old = self.previous.get(key)
        self.previous[key] = (counters, now, uptime, discontinuity, speed)
        if old is None:
            return (0.0, 0.0)
        prev, then, old_uptime, old_disc, old_speed = old
        elapsed = now - then
        if elapsed <= 0 or uptime < old_uptime or discontinuity != old_disc or speed != old_speed:
            return (0.0, 0.0)
        # At line rate a full wrap could be invisible: re-baseline long gaps.
        if speed <= 0 or elapsed * speed / 8 >= MOD:
            return (0.0, 0.0)
        deltas = [(cur - before) % MOD for cur, before in zip(counters, prev)]
        # A decrease inconsistent with one plausible wrap is treated as a reset.
        if any(delta > elapsed * speed / 8 * 1.05 for delta in deltas):
            return (0.0, 0.0)
        return tuple(round(delta * 8 / elapsed / 1_000_000, 9) for delta in deltas)
