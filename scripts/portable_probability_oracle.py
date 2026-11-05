"""Actual native activation probability, observed only after GPU readback."""
import copy
import struct
from unittest.mock import patch
import engine_worker
from calculator.buff_manager import BuffManager
from timer_registry_cases import NAMES


def observe(case):
    if case.get('probability_physical_reference'):
        return observe_physical(case)
    raw = [(copy.deepcopy(e), NAMES[o]) for e, o in zip(case['effects'], case.get('owners', [0] * len(case['effects'])))]
    chars = [dict(name=n, skill_levels={'1': 10, '2': 10, '3': 10}, _weapon=dict(engine_worker.META[n])) for n in NAMES]
    attempts = []

    class BM(BuffManager):
        def _register_all(self):
            self._effects = raw
            self._build_notify_index()

        def _condition_ok(self, conditions, caster, t, eff=None):
            passed = super()._condition_ok(conditions, caster, t, eff)
            if eff is not None and any(c.startswith('prob:') for c in conditions):
                attempts.append(dict(time=t, definition=next(i for i, (e, _) in enumerate(raw) if e is eff),
                                     owner=NAMES.index(caster), passed=passed))
            return passed

    state = dict(base_stats={n: dict(atk=1000, hp=1000000, **{'def': 0}) for n in NAMES},
                 enemy={'def': 0}, full_burst=False, rng_expected=True, rng_acc={})
    bm = BM(chars, state=state)
    events = {0: 'battle_start', 7: 'on_attack', 8: 'hit_count', 19: 'event:full_reload'}
    queries = []
    for t, op, event, owner, arg, index, extra, extra2 in case['script']:
        bm.tick(t)
        if op == 0:
            bm.notify(events[event], t, NAMES[owner])
        elif op == 2:
            before = dict(state['rng_acc'])
            queries.append(dict(attack_buffs=[bm.get_buffs(n, '__enemy__', t)['atk_pct'] for n in NAMES]))
            assert before == state['rng_acc'], 'Runtime queries must not advance probability'
        else:
            raise ValueError('Unsupported probability oracle stimulus')
    probability = []
    for definition, (effect, _) in enumerate(raw):
        if not any(c.startswith('prob:') for c in effect.get('trigger', {}).get('condition', [])):
            continue
        for owner, name in enumerate(NAMES):
            value = state['rng_acc'].get(('prob', id(effect), name), 0.0)
            probability.append(dict(definition=definition, owner=owner, value=value,
                                    bits=f'{struct.unpack("<Q", struct.pack("<d", value))[0]:016x}'))
    result = dict(queries=queries, probability=probability, attempts=attempts)
    if case.get('probability_lazy_reference'):
        result['carriers'] = [dict(definition=next(i for i, (e, _) in enumerate(raw) if e is ab.effect),
                                   recipients=sum(1 << NAMES.index(n) for n in set(ab.target_chars or [])),
                                   stacks=ab.stack, lazy_pending=ab.target_chars is None) for ab in bm._active]
    return result


def observe_physical(case):
    from portable_weapon_oracle import observe as observe_weapon
    original = BuffManager._condition_ok
    attempts = []
    managers = []
    def condition(manager, conditions, caster, t, eff=None):
        passed = original(manager, conditions, caster, t, eff)
        if any(c.startswith('prob:') for c in conditions):
            if not managers:
                managers.append(manager)
            assert managers[0] is manager
            attempts.append(dict(time=t, owner=NAMES.index(caster), passed=passed))
        return passed
    with patch.object(BuffManager, '_condition_ok', condition):
        queries, weapon = observe_weapon(case)
    assert len(attempts) == case['expected_attempts'], (case['name'], len(attempts))
    bm = managers[0]
    probability = []
    for definition, (effect, _) in enumerate(bm._effects):
        if not any(c.startswith('prob:') for c in effect.get('trigger', {}).get('condition', [])):
            continue
        for owner, name in enumerate(NAMES):
            value = bm.state['rng_acc'].get(('prob', id(effect), name), 0.0)
            probability.append(dict(definition=definition, owner=owner, value=value,
                                    bits=f'{struct.unpack("<Q", struct.pack("<d", value))[0]:016x}'))
    return dict(queries=queries, probability=probability, attempts=attempts, weapon=weapon)


def compare(case, gpu, contains):
    native = observe(case)
    contains(gpu['queries'], native['queries'], case['name'] + '.native-queries')
    assert gpu['probability'] == native['probability'], (case['name'], gpu['probability'], native['probability'])
    if case.get('probability_lazy_reference'):
        active = [carrier for carrier in gpu['carriers'] if carrier['active']]
        assert len(active) == len(native['carriers']), case['name']
        contains(active, native['carriers'], case['name'] + '.native-lazy-resolution')
    if case.get('probability_physical_reference'):
        contains(gpu['weapons'][0], native['weapon'], case['name'] + '.native-weapon-clock')
        assert gpu['frames'] == case['expected_frames']
    if 'expected_success_events' in case:
        assert [i + 1 for i, row in enumerate(native['attempts']) if row['passed']] == case['expected_success_events']
    return native
