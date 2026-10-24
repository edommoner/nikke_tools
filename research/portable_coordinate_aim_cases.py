"""Authored hand/camera controls across lifetimes, arbitration and native clocks."""
import copy
from portable_coordinate_core_cases import fixtures as cores
from world_enemy_attack_cases import field
from timer_registry_cases import NAMES


def fixtures():
    base = cores()[-1]
    rows = []

    def add(label):
        case = copy.deepcopy(base)
        case.update(name='coordinate-aim/'+label, duration=.35,
                    controls=[{} for _ in range(5)], camera=[NAMES[0]], control_mode='solo')
        for target in case['patterns'][0]['targets']:
            target['hp'] = 1e30
        rows.append(case)
        return case

    def hand(case, who=0, target='front', **when):
        case['controls'][who] = dict(aim=[dict(at=target, **when)])

    def burst(case):
        case['duration'] = 1.
        for who, stage in enumerate((3, 1, 2, 0, 0)):
            case['combat']['weapons'][who]['stage'] = stage
        case['effects'].append(dict(field('burst_charge_pct', 100, 'all_allies', 'start-gauge'), type='instant'))
        case['owners'].append(0)

    c = add('manual-owner-only'); hand(c)
    c = add('first-live-entry'); hand(c)
    a, b = c['patterns'][0]['targets']
    c['patterns'] = [dict(id='late-front', kind='parts', targets=[a], delay=.15),
                     dict(id='behind', kind='parts', targets=[b]), c['patterns'][-1]]
    c['controls'][0]['aim'].append(dict(at='behind'))
    c = add('target-expires'); hand(c)
    a, b = c['patterns'][0]['targets']
    c['patterns'] = [dict(id='front', kind='parts', targets=[a], until=dict(time=.15)),
                     dict(id='behind', kind='parts', targets=[b]), c['patterns'][-1]]
    c = add('core-expires-fallback'); hand(c, target='core')
    c['patterns'][-1]['until'] = dict(time=.15)
    c['patterns'][0]['targets'][1]['x'] = 20.
    c['controls'][0]['aim'].append(dict(at='behind'))
    c = add('core-changes-manual-stays'); hand(c)
    c['patterns'].append(dict(id='moved-core', kind='core', core_px=8, x=-10., y=3., delay=.15))
    c = add('priority-preemption'); hand(c, 0, priority=10); hand(c, 1, 'behind', priority=20)
    c = add('equal-priority-new-edge'); hand(c, 0, priority=20)
    hand(c, 1, 'behind', priority=20, anchor='combat_start', offset=.1, len=.1)
    c = add('warn-all-own'); c['control_mode'] = 'warn'; hand(c, 0); hand(c, 1, 'behind')
    c = add('layer2-interrupt'); c['focus_aim_layer2'] = True
    c['patterns'].insert(0, dict(id='interrupt', kind='interrupt', targets=[dict(name='stop', hp=1e30, x=10, y=7, r=2)]))
    c = add('layer1-ignores-interrupt')
    c['patterns'].insert(0, dict(id='interrupt', kind='interrupt', targets=[dict(name='stop', hp=1e30, x=10, y=7, r=2)]))
    c = add('shared-camera-layer2'); c.update(focus_aim_layer2=True, camera_mode='shared', camera=[NAMES[0], NAMES[1]])
    c['patterns'].insert(0, dict(id='interrupt', kind='interrupt', targets=[dict(name='stop', hp=1e30, x=10, y=7, r=2)]))
    c = add('focus-zero-marker-expires'); hand(c)
    c['effects'].append(field('focus_fire', 0, 'all_allies', 'focus-marker', duration=.1)); c['owners'].append(0)
    c = add('full-burst-follow'); hand(c); burst(c)
    for name in ('always', 'burst_charge', 'burst_chain', 'own_full_burst'):
        c = add('window-'+name); hand(c, window=name); burst(c)
        if name == 'burst_charge':
            c['effects'][-1]['trigger']['timing'] = ['every:0.2s']
            c['effects'][-1]['max_trigger'] = 1
    c = add('combat-start-anchor'); hand(c, anchor='combat_start', offset=.1, len=.1)
    for name in ('fb_end', 'own_fb_end'):
        c = add('anchor-'+name); hand(c, anchor=name, offset=-10., len=.1); burst(c)
    c = add('anchor-own-buff-end'); hand(c, anchor='own_buff_end', buff='aim-clock', offset=-.1, len=.1)
    c['effects'].append(field('atk_pct', 0, 'self', 'aim-clock', duration=.2)); c['owners'].append(0)
    c = add('anchor-reload-minus'); hand(c, anchor='combat_start', offset=.5, len=.1, minus='reload_total')
    c = add('anchor-next-fb-prediction'); hand(c, anchor='next_fb_start', offset=-40., len=100.); burst(c)
    c['duration'] = 11.
    for weapon in c['combat']['weapons']:
        weapon.update(mode='charge', charge=180., interval=180., min_cycle=180.)
    for matched in (True, False):
        c = add('gate-'+str(matched)); burst(c)
        hand(c, gate=dict(burst_stage='1', burst_user=NAMES[1] if matched else NAMES[4]))
    c = add('same-frame-target-break'); hand(c)
    c['patterns'][0]['targets'][0]['hp'] = 1
    c['combat']['weapons'][3] = copy.deepcopy(c['combat']['weapons'][0])
    c['effects'].append(field('focus_fire', 0, 'all_allies', 'break-follow')); c['owners'].append(0)
    c = add('default-interrupt-priority'); hand(c, 0); hand(c, 1, 'stop')
    c['patterns'].insert(0, dict(id='interrupt', kind='interrupt', until=dict(time=.15),
        targets=[dict(name='stop', hp=1e30, x=10, y=7, r=2)]))
    c = add('shared-camera-manual'); c.update(control_mode='warn', camera_mode='shared', camera=[NAMES[0], NAMES[1]])
    hand(c, 0); hand(c, 1, 'behind')
    c['effects'].append(field('focus_fire', 0, 'all_allies', 'shared-follow')); c['owners'].append(0)
    c = add('forced-camera-sequence'); hand(c, 0, priority=30); hand(c, 1, 'behind', priority=10)
    c['sequence'] = [dict(t=0., action='focus', target=NAMES[1])]
    c = add('dynamic-reload-minus'); c['duration'] = .55
    hand(c, anchor='combat_start', offset=.5, len=.1, minus='reload_total')
    c['effects'].append(field('reload_time_fixed', .1, 'self', 'changed-reload', 'every:0.15s', max_trigger=1)); c['owners'].append(0)
    return rows
