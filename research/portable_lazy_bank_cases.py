"""Native-checked bounded lazy-cache workloads, without alternate game math."""
import copy
from portable_stun_cases import fixtures as status_fixtures
from world_enemy_attack_cases import field


def fixtures():
    base=copy.deepcopy(status_fixtures()[0]);base.update(effects=[],owners=[],patterns=[dict(id='idle',kind='idle')])
    base['combat']['trace']='summary'
    rows=[]
    def buff(name,target='allies_top_atk:1',timing='battle_start',stat='atk_pct',duration=-1):
        return field(stat,0,target,name,timing=timing,duration=duration)
    def add(name,effects,owners=None):
        c=copy.deepcopy(base);c.update(name='lazy-bank-'+name,effects=effects,owners=owners if owners is not None else [0]*len(effects))
        rows.append(c);return c
    c=add('no-lazy',[buff('self',target='self')]);c['expected_cache_groups']=0
    c=add('shared-siblings',[buff('first'),buff('second',stat='crit_rate')]);c['expected_cache_groups']=1
    c=add('separate-owners',[buff('first'),buff('second')],[0,1]);c['expected_cache_groups']=2
    c=add('separate-raw-selectors',[buff('first'),buff('second',target='allies_lowest_hp:1')]);c['expected_cache_groups']=2
    timing='every:0.016666666666666666s'
    selectors=[f'allies_top_atk:{n}' for n in range(1,6)]+[f'allies_lowest_hp:{n}' for n in range(1,5)]
    for name,effects in [
        ('reuse-nine-groups',[buff('rank-'+str(i),target=target,timing=timing,duration=.001) for i,target in enumerate(selectors)]),
        ('repeated-composite-selector',[buff('composite',target=['allies_top_atk:1','allies_lowest_hp:1'],timing=timing,duration=.001)]),
        ('reuse-linked-siblings',[buff('rank-'+str(i)+'-'+stat,target=target,timing=timing,duration=.001,stat=stat) for i,target in enumerate(selectors) for stat in ('atk_pct','crit_rate')])]:
        c=add(name,effects);c.update(duration=2.2,expect_cache_saturation=name!='repeated-composite-selector')
        if name=='repeated-composite-selector':c['expected_cache_groups']=0
        else:
            # A literal zero-valued self-set enables the existing full ordered
            # recipient readback, rather than comparing ranks as a bit mask.
            c['effects'].append(buff('ordered-observation',target=['self']));c['owners'].append(0)
        c['combat']['weapons'][0].update(interval=1/60,capacity=10000)
        for weapon in c['combat']['weapons'][1:]:weapon['interval']=100
    return rows


def negative_inputs(compile_case):
    from portable_specs import LIMITS as L
    c=fixtures()[4];raw=compile_case(c)[0];count=raw[2]
    at=L['COMMAND_BASE']+(count-1)*8
    if raw[at]!=40:raise ValueError('Expected final actor-field snapshot')
    # Preserve all command-count sidecars. actorFieldCommand checks this owner
    # during execution, after the preceding complete world/frame commands.
    raw[at+3]=5
    return [('reject/lazy-bank-error-after-warm',raw,None)]
