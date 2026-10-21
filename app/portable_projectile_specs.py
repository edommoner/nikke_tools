"""Physical pellet split and non-coordinate part reach; no CPU battle state."""
from effect_spec import EXTRA_STAT
STATS = {name: EXTRA_STAT[name] for name in ('pellet_count','pellet_count_fixed','pierce_range','explosion_range')}
ABI = 0x5045568d
MODE = 24
MAX_PELLETS = 4096
HEAD = 720912
TRACE = HEAD+16
TRACE_COUNT = 2048
assert STATS == dict(pellet_count=47,pellet_count_fixed=48,pierce_range=63,explosion_range=64)
assert TRACE+TRACE_COUNT*16 <= 786432
