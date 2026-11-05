"""Mechanical authored stimuli; never serializes CPU state as GPU input."""
import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def effect(conditions, **extra):
    return dict(name='chance', source='스킬1', type='buff', stat='atk_pct', fixed_value=1,
                target='self', duration=-1, max_stack=10000,
                trigger=dict(timing=['on_attack'], condition=conditions), **extra)


def script(owner=0, count=31):
    rows = []
    for i in range(count):
        rows += [[i / 10, 0, 7, owner, 0, -1, 0, 0], [i / 10, 2, 0, owner, 0, i, 0, 0]]
    return rows


def main():
    cases = []
    def add(name, effects, owners=None, commands=None, **extra):
        cases.append(dict(name='probability-' + name, effects=effects,
                          owners=owners or [0] * len(effects), script=commands if commands is not None else script(),
                          probability_reference=True, **extra))
    fires = {'0': [], '5': [20], '10': [11, 21, 31], '20': list(range(5, 32, 5)),
             '50': list(range(2, 32, 2)), '100': list(range(1, 32))}
    for rate in ['0', '5', '10', '20', '30', '33.3333', '50', '100']:
        for owner in range(5):
            add('rate-' + rate + '-owner-' + str(owner), [effect(['prob:' + rate])], [owner], script(owner),
                **(dict(expected_success_events=fires[rate]) if rate in fires else {}))
    for condition in ['self_state:absent', 'self_stat_above:atk_pct:1']:
        for rate in ['0', '20', '100']:
            for before in [True, False]:
                conditions = [condition, 'prob:' + rate] if before else ['prob:' + rate, condition]
                add('order-' + condition.replace(':', '-') + '-' + rate + '-' + str(before), [effect(conditions)])
    for rates in [['50', '50'], ['10', '100'], ['100', '10'], ['100', '100'], ['20', '50'], ['0', '100']]:
        add('multiple-' + '-'.join(rates), [effect(['prob:' + rate for rate in rates])])
    for values in [{}, {'10': 20}, {'1': 50, '10': 100}, {'1': 50, '10': 0}]:
        add('skill-values-' + str(len(cases)), [effect(['prob:{0}'], trigger_values=values)])
    for same_name in [True, False]:
        for same_owner in [True, False]:
            effects = [effect(['prob:20']), effect(['prob:50'])]
            effects[1]['fixed_value'] = 3
            effects[1]['name'] = 'chance' if same_name else 'separate'
            commands = script()
            if not same_owner:
                commands = []
                for i in range(20):
                    commands += [[i / 10, 0, 7, i % 2, 0, -1, 0, 0], [i / 10, 2, 0, 0, 0, i, 0, 0]]
            add('instance-' + str(same_name) + '-' + str(same_owner), effects, [0, 0 if same_owner else 1], commands)
    for duration in [0, .05, .15]:
        e = effect(['prob:20']);e['duration'] = duration
        add('expire-reapply-' + str(duration), [e])
    for rate in ['0', '20', '100']:
        e = effect(['prob:' + rate]);e['trigger']['timing'] = ['passive']
        add('permanent-passive-' + rate, [e], commands=[[0, 0, 0, 0, 0, -1, 0, 0]] + [[i / 10, 2, 0, 0, 0, i, 0, 0] for i in range(20)])
    for rate in ['10', '20', '100']:
        e = effect(['prob:' + rate]);e['trigger']['timing'] = ['every:0.1s']
        add('periodic-' + rate, [e], commands=[[i / 10, 2, 0, 0, 0, i, 0, 0] for i in range(32)])
    for maximum in [0, 1, 2]:
        add('budget-' + str(maximum), [effect(['prob:50'], max_trigger=maximum)])
    e = effect(['prob:50']);e['trigger']['timing'] = ['on_attack_count:2', 'on_attack_count:3']
    add('descriptor-multiplicity', [e])
    for target in ['all_allies', 'all_allies_excl_self', 'allies_top_atk:1', 'allies_top_atk:2']:
        e = effect(['prob:20']);e['target'] = target
        add('recipient-' + target, [e])
    for before in [True, False]:
        for rate in ['0', '100']:
            lazy = effect([]);lazy.update(name='ranked', fixed_value=10, target='allies_top_atk:1')
            lazy['trigger']['timing'] = ['battle_start']
            conditions = ['prob:' + rate, 'self_stat_above:atk_pct:1'] if before else ['self_stat_above:atk_pct:1', 'prob:' + rate]
            add('lazy-query-order-' + str(before) + '-' + rate, [lazy, effect(conditions)],
                commands=[[0, 0, 0, 0, 0, -1, 0, 0], [.1, 0, 7, 0, 0, -1, 0, 0]],
                probability_lazy_reference=True)
    for rates in [['10'], ['20'], ['33.3333'], ['50', '50'], ['10', '100']]:
        no_critical = effect([]);no_critical.update(name='no-critical', stat='crit_rate', fixed_value=-15)
        no_critical['trigger']['timing'] = ['battle_start']
        chance = effect(['prob:' + rate for rate in rates]);chance['fixed_value'] = 0
        end = 4095 / 60
        add('physical4096-' + '-'.join(rates), [no_critical, chance],
            commands=[[end, 24, 0, 0, 0, -1, 0, 0], [end, 2, 0, 0, -1, 0, 0, 0]],
            combat=dict(weapons=[dict(enabled=True, capacity=10000, interval=1/120, coefficient=100)] + [dict(enabled=False) for _ in range(4)], targets=[dict(hp=1e15)], trace='summary'),
            probability_physical_reference=True, expected_attempts=4096,
            expected_frames=4096)
    for case in cases:
        case['expected_queries'] = [{} for command in case['script'] if command[1] == 2]
    (ROOT / 'tests/fixtures/portable-probability.json').write_text(json.dumps(dict(cases=cases), ensure_ascii=False, indent=2) + '\n')
    print(len(cases), 'authored probability cases')


if __name__ == '__main__':
    main()
