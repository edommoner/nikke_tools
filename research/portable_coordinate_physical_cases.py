"""Literal worlds for the next shared physical-coordinate port, not support.

The radii/shape positions are authored; no landing probabilities are packed.
"""
import copy
from portable_coordinate_skill_cases import fixtures as skill_cases


def fixtures():
    base = copy.deepcopy(skill_cases()[2])
    base.pop('contract')
    base['effects'] = base['effects'][:2]
    base['owners'] = base['owners'][:2]
    base['duration'] = .05
    base['patterns'] = [dict(id='parts', kind='parts', targets=[
        dict(name='front', hp=1e8, x=0, y=0, r=2, z=2),
        dict(name='behind', hp=1e8, x=0, y=0, r=2, z=1)])]
    base['combat']['weapons'][0] = dict(enabled=True, stage=0, gauge=0,
        capacity=30, interval=.1, reload=.4, pellets=1, muzzles=1, mode='auto')
    rows = []
    def add(name):
        c = copy.deepcopy(base)
        c['name'] = 'coordinate-physical-reference/' + name
        rows.append(c)
        return c
    add('occlusion-and-body')
    c = add('full-front');c['patterns'][0]['targets'][0]['r'] = 100
    c = add('interrupt-front');c['patterns'].insert(0, dict(id='interrupt', kind='interrupt',
        targets=[dict(name='stop', hp=1e8, x=0, y=0, r=100, z=3)]))
    c = add('two-muzzles-three-pellets');c['combat']['weapons'][0].update(pellets=3, muzzles=2)
    c = add('retirement');c['patterns'][0]['targets'][0]['hp'] = 1
    c['duration'] = .25
    c = add('body-without-targets');c['patterns'] = [dict(id='idle', kind='idle')]
    from world_enemy_attack_cases import field
    c = add('pierce-reach');c['effects'].append(field('pierce_enabled', 1, 'self', 'physical-pierce'));c['owners'].append(0)
    c = add('charge-pierce');c['effects'].append(field('pierce_enabled', 1, 'self', 'physical-pierce'));c['owners'].append(0)
    c['combat']['weapons'][0].update(mode='charge', charge=.05, interval=.1,
        min_cycle=.1, full_charge_mult=100)
    c['duration'] = .1
    return rows
