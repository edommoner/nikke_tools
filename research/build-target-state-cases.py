"""Authored stimuli and expected markers, never CPU-generated GPU inputs."""
import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def effect(name, target='boss', conditions=None, duration=.5, timing='on_attack', stat=None):
    return dict(name=name, source='스킬1', type='buff', stat=stat, fixed_value=1,
                duration=duration, target=target, max_stack=10,
                trigger=dict(timing=[timing], condition=conditions or []))


def notify(t, event, owner):
    return [t, 0, event, owner, 0, -1, 0, 0]


def query(t, index=0):
    return [t, 2, 0, 0, 0, index, 0, 0]


def case(name, effects, owners, script, values, owner=0, targets=None):
    expected = []
    for value in values:
        row = [0]*5;row[owner] = value
        expected.append(dict(attack_buffs=row))
    assert len(expected) == sum(c[1] == 2 for c in script)
    return dict(name='target-state-' + name, target_state_reference=True,
        effects=effects, owners=owners, script=script,
        combat=dict(weapons=[dict(enabled=False) for _ in range(5)],
                    targets=targets or [dict(hp=1000000)]), expected_queries=expected)


def main():
    rows = []
    for owner in range(5):
        source = (owner+1)%5
        for index, name in enumerate(['A', '사슬 감기', 'A:B:C', ' A ', '', 'A\nB', 'X.*', '🙂']):
            for prefix, expected in [('target_state:', 1), ('not_target_state:', 0), ('target_stack_above:', 1)]:
                condition = prefix + name + (':2' if prefix == 'target_stack_above:' else '')
                marker = effect('marker', 'self', [condition], duration=2, timing='event:full_reload', stat='atk_pct')
                rows.append(case(f'exact-{owner}-{index}-{prefix}', [effect(name), marker], [source, owner],
                    [notify(0, 7, source), notify(.01, 7, source), notify(.1, 19, owner), query(.1)], [expected], owner))
        for prefix, expected in [('target_state:', 0), ('not_target_state:', 1), ('target_stack_above:', 0)]:
            condition = prefix + 'missing' + (':1' if prefix == 'target_stack_above:' else '')
            rows.append(case(f'absent-{owner}-{prefix}',
                [effect('marker', 'self', [condition], duration=2, timing='event:full_reload', stat='atk_pct')],
                [owner], [notify(.1, 19, owner), query(.1)], [expected], owner))
        for duration in (-1, 2):
            for prefix in ('target_state:', 'not_target_state:', 'target_stack_above:'):
                condition = prefix + 'state' + (':1' if prefix == 'target_stack_above:' else '')
                marker = effect('marker', 'self', [condition], duration=duration, timing='event:full_reload', stat='atk_pct')
                if prefix == 'not_target_state:':
                    script = [notify(0, 19, owner), query(0), notify(.1, 7, source), query(.1, 1), notify(.6, 8, owner), query(.6, 2)]
                    values = [1, 0 if duration == -1 else 1, 1]
                else:
                    script = [notify(0, 7, source), notify(.1, 19, owner), query(.1), notify(.5, 8, owner), query(.5, 1)]
                    # target_stack_above is activation-only even for infinite buffs.
                    values = [1, 0 if duration == -1 and prefix == 'target_state:' else 1]
                rows.append(case(f'lifetime-{owner}-{duration}-{prefix}', [effect('state'), marker], [source, owner], script, values, owner))
        # A same-named allied state must never satisfy an enemy condition.
        marker = effect('marker', 'self', ['target_state:state'], duration=2, timing='event:full_reload', stat='atk_pct')
        rows.append(case(f'ally-only-{owner}', [effect('state', 'all_allies'), marker], [source, owner],
                         [notify(0, 7, source), notify(.1, 19, owner), query(.1)], [0], owner))
        # Multiple instances use max stack, not their sum; independent of owner.
        for threshold, expected in [(2, 1), (3, 1), (4, 0), (5, 0)]:
            a, b = effect('same'), effect('same')
            marker = effect('marker', 'self', [f'target_stack_above:same:{threshold}'], duration=2, timing='event:full_reload', stat='atk_pct')
            script = [notify(0, 7, 0), notify(.01, 7, 0), notify(.02, 7, 1), notify(.03, 7, 1), notify(.04, 7, 1), notify(.1, 19, owner), query(.1)]
            rows.append(case(f'max-{owner}-{threshold}', [a, b, marker], [0, 1, owner], script, [expected], owner))
    for prefix in ('target_state:', 'not_target_state:', 'target_stack_above:'):
        condition = prefix + 'state' + (':1' if prefix == 'target_stack_above:' else '')
        marker = effect('marker', 'self', [condition], duration=-1, timing='event:full_reload', stat='atk_pct')
        marker['max_stack'] = 1
        script = [[0,20,0,0,1,0,0,0], notify(0, 7, 0), notify(.1, 19, 0), query(.1),
                  [.2,22,0,0,1,0,0,0], query(.2, 1), [.3,21,0,0,1,0,1000000,0], query(.3, 2),
                  notify(.4, 7, 0), notify(.4, 19, 0), query(.4, 3)]
        expected = [0,0,0,0] if prefix == 'not_target_state:' else [1,0,0,1] if prefix == 'target_state:' else [1,1,1,1]
        rows.append(case('retire-reuse-' + prefix, [effect('state', 'enemies_nearest:1', duration=2), marker], [0,0], script, expected,
                         targets=[dict(hp=1000000),dict(hp=1000000,kind=5)]))
    for actual, wanted in [('A:B', 'A'), (' A', 'A'), ('A ', 'A'), ('A', 'a')]:
        marker = effect('marker', 'self', ['target_state:' + wanted], duration=2, timing='event:full_reload', stat='atk_pct')
        rows.append(case(f'distinct-{actual!r}-{wanted!r}', [effect(actual), marker], [0,0],
                         [notify(0,7,0), notify(.1,19,0), query(.1)], [0]))
    for prefix in ('target_state:', 'target_stack_above:'):
        condition = prefix + 'dot' + (':2' if prefix == 'target_stack_above:' else '')
        dot = effect('dot', 'all_enemies', duration=1, stat='dot_damage')
        dot.update(type='damage', tick_interval=.2, tick_start=.2, fixed_value=0)
        marker = effect('marker', 'self', [condition], duration=-1, timing='event:full_reload', stat='atk_pct')
        rows.append(case('dot-' + prefix, [dot, marker], [0,0],
            [notify(0,7,0), notify(.01,7,0), notify(.1,19,0), query(.1), notify(1.01,8,0), query(1.01,1)],
            [1,0] if prefix == 'target_state:' else [1,1]))
    marker = effect('marker', 'self', ['target_state:state'], duration=-1, timing='event:full_reload', stat='atk_pct')
    clear = effect('clear', 'self', timing='hit_count', stat='remove_named_buff')
    clear.update(type='instant', target_effect='state')
    rows.append(case('explicit-remove', [effect('state'), marker, clear], [0,0,0],
        [notify(0,7,0), notify(.1,19,0), query(.1), notify(.2,8,0), query(.2,1)], [1,0]))
    targets = [dict(hp=10),dict(hp=1000000,kind=5),dict(hp=2000000,kind=5)]
    marker = effect('marker', 'self', ['target_state:state'], duration=-1, timing='event:full_reload', stat='atk_pct')
    rows.append(case('any-live-enemy', [effect('state', 'enemies_lowest_hp:2', duration=2), marker], [0,0],
        [notify(0,7,0), notify(.1,19,0), query(.1), [.2,22,0,0,2,0,0,0], query(.2,1),
         [.3,21,0,0,2,0,2000000,0], query(.3,2), [.4,22,0,0,1,0,0,0], query(.4,3)], [1,1,1,0], targets=targets))
    for threshold, expected in [(0,1),(2147483647,0)]:
        marker = effect('marker', 'self', [f'target_stack_above:absent:{threshold}'], duration=2, timing='event:full_reload', stat='atk_pct')
        rows.append(case('integer-bound-' + str(threshold), [marker], [0], [notify(0,19,0),query(0)], [expected]))
    # Activation-only conditions must preserve the native same-name merge.
    # Runtime-condition placeholders would retain two separate10/20 entries.
    for owner in range(5):
        for target in ('self','all_allies','allies_top_atk:1'):
            for duration in (-1,1):
                aliases=[]
                for value in (10,20):
                    alias=effect('alias',target,['target_stack_above:absent:0'],duration=duration,stat='atk_pct')
                    alias.update(fixed_value=value,max_stack=2);aliases.append(alias)
                script=[notify(0,7,owner),query(0),notify(1,8,owner),query(1,1)]
                row=case(f'alias-{owner}-{target}-{duration}',aliases,[owner,owner],script,[20,20 if duration==-1 else 0],owner)
                members=range(5) if target=='all_allies' else [0] if target=='allies_top_atk:1' else [owner]
                values=[20 if i in members else 0 for i in range(5)]
                row['expected_queries']=[dict(attack_buffs=values),dict(attack_buffs=values if duration==-1 else [0]*5)]
                rows.append(row)
    for row in rows:
        row['effects'] = copy.deepcopy(row['effects'])
    path = ROOT / 'tests/fixtures/portable-target-states.json'
    path.write_text(json.dumps(dict(cases=rows), ensure_ascii=False, indent=2) + '\n')
    print('Authored target-state cases', len(rows))


if __name__ == '__main__':
    main()
