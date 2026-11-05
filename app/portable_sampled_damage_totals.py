"""Decode exact main-damage credits without discarding the binary64 diagnostic.

The dedicated sampled-parent profile counts BODY/PART at actorPoolLand, before
lifesteal receipts. ADD's capped score and INTERRUPT do not enter this bank.
"""
import math
from portable_coordinate_sampling_bank import LAYOUT as BANK
from portable_coordinate_physical_specs import LAYOUT as CF
BASE=919704
WORDS=29
MAGIC=0x43504431

def verify_layout():
    assert BASE==BANK['RNG']+BANK['RNG_WORDS']
    assert BASE+WORDS<=CF['END']
    return True

def exact_damage(block, legacy_damage, packets, target_kinds,*,sampled_burst=False,sampled_manual=False):
    verify_layout()
    assert list(block[BASE:BASE+4])==[MAGIC,1,5,0], 'Exact damage header'
    if type(sampled_burst) is not bool or type(sampled_manual) is not bool or sampled_manual and not sampled_burst:raise ValueError('Explicit sampled totals profile required')
    if sampled_burst:
        from portable_coordinate_sampled_burst_wire import HEAD,HEAD_WORDS,ENTRIES,HITS
        tail=HEAD+HEAD_WORDS
        if sampled_manual:
            from portable_manual_control_specs import BASE as MBASE,WORDS as MWORDS
            assert tail==MBASE
            tail+=MWORDS
        assert not any(block[BASE+WORDS:HEAD]) and not any(block[tail:CF['END']]), 'Exact damage unused tail'
        assert block[HEAD]<=ENTRIES and block[HEAD+3]<=ENTRIES*HITS and not any(block[HEAD+4:HEAD+HEAD_WORDS]), 'Pending numeric header'
    else:
        assert not any(block[BASE+WORDS:CF['END']]), 'Exact damage unused tail'
    totals=[0]*5;counts=[0]*5;rounded=[0.0]*5
    for p in packets:
        kind=target_kinds.get(p['target'],0)
        if kind not in (0,1):continue
        who=p['owner'];amount=p['damage']
        assert isinstance(who,int) and 0<=who<5 and isinstance(amount,int) and 0<=amount<2**63, 'Exact credited integer packet'
        totals[who]+=amount;counts[who]+=1;rounded[who]+=float(amount)
    assert all(math.isfinite(v) for v in rounded)
    assert list(legacy_damage)==rounded, 'Preserved ordered binary64 aggregate'
    actual=[]
    for who in range(5):
        at=BASE+4+who*5
        value=sum(int(block[at+i])<<(32*i) for i in range(4))
        assert value==totals[who] and block[at+4]==counts[who], 'Exact damage amount/count'
        actual.append(value)
    return actual
