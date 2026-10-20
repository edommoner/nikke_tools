"""Observe actual native firing; literal expectations do not use _burst_gain.

This is CPU characterization, not GPU admission or a CPU trace for GPU input.
The wrappers only record and forward calls to the original native methods.
"""
import copy
import hashlib
import json
from pathlib import Path
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / p) for p in ('app', 'scripts', 'tests')]
import engine_worker
from calculator import buff_manager as native
from portable_weapon_oracle import authored_weapon, authored_weapon_state
from test_target_counter_runtime import NAMES


def buff(timing):
    return dict(name='charge-speed', source='스킬1', type='buff',
                stat='burst_charge_speed_pct', fixed_value=100,
                target='all_allies', duration=-1,
                trigger=dict(timing=[timing], condition=[]))


def run(owner, reference, scenario):
    shooter = (owner + 1) % 5 if scenario == 'other-actor' else owner
    charge = scenario.startswith('charge-')
    timing = {'pellet-callback': 'pellet_hit', 'attack-callback': 'on_attack',
              'charge-attack-callback': 'on_attack'}.get(scenario, 'battle_start')
    effects = [(buff(timing), NAMES[owner])]
    mode = scenario in ('normal-mode', 'skill-mode')
    if mode:
        effects.append((dict(name='changed-weapon', source='스킬1', type='weapon_change',
            weapon_type='AR', damage_coeff={'10': 100}, max_ammo=-1,
            fire_rate=1, charge=False, pellets=1, muzzles=1,
            post_fire_delay=0, burst_energy=5, core_dmg_mult=200,
            skill_damage=scenario == 'skill-mode', target='self', duration=.5,
            trigger=dict(timing=['battle_start'], condition=[])), NAMES[shooter]))
    chars = [dict(name=n, skill_levels={'1': 10, '2': 10, '3': 10},
                  _weapon=copy.deepcopy(engine_worker.META[n])) for n in NAMES]
    w = dict(base_weapon_type='SR' if charge else 'SG' if scenario == 'pellets' else 'AR',
             mode='charge' if charge else 'auto', coefficient=100, capacity=100,
             interval=1, charge=.5, gauge=.5, full_charge_mult=300,
             pellets=10 if scenario in ('pellets', 'pellet-callback') else 1,
             muzzles=2 if scenario == 'dual-muzzle' else 1)
    authored_weapon(chars[shooter], w)

    class BM(native.BuffManager):
        def _register_all(self):
            self._effects = copy.deepcopy(effects)
            self._build_notify_index()

    enemy = dict(core_px=0, code=None, **{'def': 0})
    bm = BM(chars, state=dict(base_stats={n: dict(atk=1000, hp=1000000, **{'def': 0}) for n in NAMES},
        enemy=enemy, full_burst=False, rng_acc={}, rng_expected=True,
        camera={NAMES[shooter]} if scenario == 'charge-camera' else set(),
        burst_gauge=0, burst_gauge_charging=scenario != 'closed-window'))
    st = authored_weapon_state(chars[shooter], w)
    trace = []
    original_mark, original_add, original_notify = bm.mark_normal_attack_landed, bm.add_burst_gauge, bm.notify

    def mark(name):
        original_mark(name)
        trace.append(dict(event='normal-landed', caster=name))

    def add(amount, t, caster='', source=''):
        accepted = original_add(amount, t, caster, source)
        trace.append(dict(event='gauge', amount=amount, accepted=accepted, t=t,
                          caster=caster, source=source,
                          landed=sorted(bm.state.get('normal_attack_landed', ()))))
        return accepted

    def notify(event, t, caster, **ctx):
        result = original_notify(event, t, caster, **ctx)
        if event in ('pellet_hit', 'on_attack', 'full_charge_fire', 'hit_count'):
            trace.append(dict(event=event, caster=caster, t=t))
        return result

    bm.mark_normal_attack_landed, bm.add_burst_gauge, bm.notify = mark, add, notify
    for n in NAMES:
        bm.notify('battle_start', 0, n)
    st.ammo = st._full_ammo(bm, 0)
    raw = reference.get('burst_energy_raw', reference['burst_energy'] / 2)
    initial = bm.get_buffs(NAMES[shooter], '__enemy__', 0).get('burst_charge_speed_flat', 0)
    assert initial == (raw if timing == 'battle_start' else 0), (scenario, initial)
    hits = []
    for frame in range(32 if charge else 1):
        t = frame / 60
        bm.tick(t)
        hits.extend(st.tick(t, bm, enemy, {'rng_mode': 'expected'}))
    count = w['pellets'] * w['muzzles']
    assert len(hits) == count, (scenario, len(hits), count)
    flat = raw if shooter != owner or scenario == 'skill-mode' else reference['burst_energy']
    # Auto on_attack follows gauge lookup; charge on_attack precedes it.
    if scenario == 'attack-callback':
        flat = 0
    expected_gain = (5 if mode else .5) * count * (3 if scenario == 'charge-camera' else 1) + count * flat
    gauge_events = [e for e in trace if e['event'] == 'gauge']
    assert len(gauge_events) == 1, (scenario, gauge_events)
    assert gauge_events[0]['amount'] == expected_gain, (scenario, gauge_events, expected_gain)
    expected_gauge = 0 if scenario == 'closed-window' else min(100, expected_gain)
    assert bm.state['burst_gauge'] == expected_gauge
    expected_landed = [] if scenario == 'skill-mode' else [NAMES[shooter]]
    assert sorted(bm.state.get('normal_attack_landed', ())) == sorted(expected_landed)
    after = bm.get_buffs(NAMES[shooter], '__enemy__', 1).get('burst_charge_speed_flat', 0)
    expected_after = raw if shooter != owner or scenario == 'skill-mode' else reference['burst_energy']
    assert after == expected_after
    bm.state['burst_gauge'] = 0
    bm.state['burst_gauge_charging'] = True
    reset = bm.get_buffs(NAMES[shooter], '__enemy__', 1).get('burst_charge_speed_flat', 0)
    assert reset == expected_after
    return dict(owner=owner, shooter=shooter, reference=reference, scenario=scenario,
                hits=len(hits), initial_flat=initial, expected_generated_gain=expected_gain,
                actual_gauge=expected_gauge, after_flat=after, reset_flat=reset, trace=trace)


def main():
    rows = []
    scenarios = ['auto', 'other-actor', 'pellets', 'dual-muzzle', 'charge-camera',
                 'charge-no-camera', 'closed-window', 'normal-mode', 'skill-mode',
                 'pellet-callback', 'attack-callback', 'charge-attack-callback']
    references = [dict(burst_energy=2, burst_energy_raw=.25),
                  dict(burst_energy=4, burst_energy_raw=1.5), dict(burst_energy=2)]
    output = ROOT / 'research/portable-burst-charge-firing-native.json'
    try:
        for owner in range(5):
            for reference in references:
                replacement = dict(native._NIKKE[NAMES[owner]], **reference)
                if 'burst_energy_raw' not in reference:
                    replacement.pop('burst_energy_raw', None)
                with patch.dict(native._NIKKE, {NAMES[owner]: replacement}):
                    for scenario in scenarios:
                        rows.append(run(owner, reference, scenario))
    except Exception as error:
        output.write_text(json.dumps(dict(passed=False, completed=rows,
            failed=dict(owner=owner, reference=reference, scenario=scenario, error=repr(error))),
            ensure_ascii=False, indent=2) + '\n')
        raise
    paths = ['research/characterize-burst-charge-firing.py', 'scripts/portable_weapon_oracle.py',
             'research/upstream/nikke-calc-master/calculator/timeline.py',
             'research/upstream/nikke-calc-master/calculator/buff_manager.py']
    output.write_text(json.dumps(dict(passed=True, cpu_only=True, cases=rows,
        gpu_execution_performed=False, gpu_admission_enabled=False,
        scope='180 actual native tick/firing cases. Gauge values are read from BuffManager, not reconstructed after mode restoration. Reset checks the reference latch without a second shot. No geometry, missed shots, full battle, skill packet or GPU certification.',
        source_sha256={p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in paths}),
        ensure_ascii=False, indent=2) + '\n')
    print(len(rows), 'actual native firing cases passed; GPU admission unchanged')


if __name__ == '__main__':
    main()
