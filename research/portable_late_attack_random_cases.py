"""Late attack selectors use fresh direct reads; ordinary mapped stats use lazy membership."""
import copy
from portable_ally_random_reference_cases import fixtures as random_fixtures
from world_enemy_attack_cases import field


def fixtures():
    base = copy.deepcopy(random_fixtures()[0])
    base.pop('contract')
    rows = []
    for label, stat, extra in (
        ('caster', 'atk_caster_based_pct', None),
        ('caster-hp-pass', 'atk_caster_based_pct', 'atk_from_hp_pct'),
        ('hp', 'atk_from_hp_pct', None),
        ('mapped-control', 'def_pct', None),
        ('caster-mapped-sibling', 'atk_caster_based_pct', 'def_pct'),
    ):
        case = copy.deepcopy(base)
        case['name'] = 'late-attack-random-' + label
        case['effects'][1].update(stat=stat, duration=-1)
        case['effects'][1]['trigger']['timing'] = ['battle_start']
        # Owner4 casts the buff; the firing owner0 is an eligible recipient.
        case['owners'][1] = 4
        if extra:
            target = 'allies_random:1' if extra == 'def_pct' else 'self'
            case['effects'].append(field(extra, 1, target, 'late-pass-sibling', duration=-1))
            case['owners'].append(4)
        rows.append(case)
    changed=copy.deepcopy(rows[0]);changed['name']='late-attack-random-post-hit-mutation'
    changed['effects'].append(field('atk_pct',0,'self','post-hit-value-update',timing='on_attack',duration=10,max_stack=128))
    changed['owners'].append(0);rows.append(changed)
    snapshot=copy.deepcopy(rows[0]);snapshot['name']='late-attack-random-full-burst-log-off'
    snapshot['duration']=1.25
    snapshot['combat']['weapons'][0].update(gauge=100,interval=.5,min_cycle=.5)
    for i in range(3):snapshot['combat']['weapons'][i]['stage']=i+1
    rows.append(snapshot)
    logged=copy.deepcopy(snapshot);logged['name']='late-attack-random-full-burst-log-on'
    logged['native_snapshot_logging']=True;logged['environment']['native_snapshot_logging']=True
    rows.append(logged)
    healed=copy.deepcopy(rows[0]);healed['name']='late-attack-random-first-capped-heal'
    heal=field('heal_hp_pct',1,'self','post-hit-first-capped-heal',timing='on_attack');heal['type']='instant'
    healed['effects'].append(heal);healed['owners'].append(0);rows.append(healed)
    expired=copy.deepcopy(rows[0]);expired['name']='late-attack-random-expiry-log-on'
    expired['effects'][1]['duration']=.15
    expired['native_snapshot_logging']=True;expired['environment']['native_snapshot_logging']=True
    rows.append(expired)
    rearmed=copy.deepcopy(expired);rearmed['name']='late-attack-random-expiry-log-rearm'
    rearmed['effects'][1]['trigger']['timing'].append('event:state_end:'+rearmed['effects'][1]['name'])
    rows.append(rearmed)
    return rows
