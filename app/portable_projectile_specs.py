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


def finalize_program(words):
    """Keep canonical rows intact; normalize native squad indexing without changing effect definitions.

    Native registers the counted spelling in the squad index. The bare spelling
    is indexed locally and never visited by global squad-ammo notification.
    Existing wire stage2 for a non-burst event is the shared never-match form.
    """
    from portable_specs import LIMITS as L,FIELDS as F
    if words[0]==ABI and words[L['TARGET_COUNTER_INPUT_BASE']+6]==MODE:return
    for row in range(words[1]):
        count=words[L['DEFINITION_BASE']+row*L['DEFINITION_WORDS']+F['TRIGGER_COUNT']]
        slots=[L['EVENT_BASE']+row*L['EVENT_WORDS']+slot*8 for slot in range(count)]
        bare=[at for at in slots if words[at]==26 and words[at+3]==0]
        counted=[at for at in slots if words[at]==26 and words[at+3]!=0]
        if not bare:continue
        for at in bare:words[at+7]=2
        # A counted spelling puts this entire effect into the native squad
        # index. Its bare spelling then matches every notification, once per
        # counted index entry. Preserve the remaining non-ammo timings.
        for at in counted:words[at+3]=0
    words[0]=ABI
    words[L['TARGET_COUNTER_INPUT_BASE']+6]=MODE
