"""Actual native geometry activation;called only after GPU readback."""
import copy
import struct
import engine_worker
from calculator.buff_manager import BuffManager
from timer_registry_cases import NAMES


def observe(case):
    if case.get('geometry_physical_reference'):
        from portable_weapon_oracle import observe as physical
        queries, weapon = physical(case)
        return dict(queries=queries, weapons=[weapon])
    raw = [(copy.deepcopy(e), NAMES[o]) for e, o in zip(case['effects'], case.get('owners', [0]*len(case['effects'])))]
    chars = [dict(name=n, skill_levels={'1':10, '2':10, '3':10}, _weapon=copy.deepcopy(engine_worker.META[n])) for n in NAMES]
    geometry = case['environment']['geometry']
    enemy = dict(core_px=geometry.get('core_px', 0), optimal_range_weapons=geometry.get('optimal_weapons', []))
    if geometry.get('distance') is not None:
        enemy['distance'] = geometry['distance']
    class BM(BuffManager):
        def _register_all(self):
            self._effects = raw
            self._build_notify_index()
    state = dict(base_stats={n:dict(atk=1000, hp=1000000, **{'def':0}) for n in NAMES},
                 enemy=enemy, full_burst=False, rng_expected=True, rng_acc={})
    bm = BM(chars, state=state)
    queries = []
    events = {0:'battle_start', 7:'on_attack'}
    for t, op, event, owner, arg, index, extra, extra2 in case['script']:
        bm.tick(t)
        if op == 0:
            bm.notify(events[event], t, NAMES[owner])
        elif op == 2:
            queries.append(dict(attack_buffs=[bm.get_buffs(n, '__enemy__', t)['atk_pct'] for n in NAMES]))
        else:
            raise ValueError('Unsupported geometry oracle stimulus')
    probability = []
    for index, (effect, _) in enumerate(raw):
        if not any(c.startswith('prob:') for c in effect.get('trigger', {}).get('condition', [])):
            continue
        for owner, name in enumerate(NAMES):
            value = state['rng_acc'].get(('prob', id(effect), name), 0.)
            probability.append(dict(definition=index, owner=owner, value=value,
                                    bits=f'{struct.unpack("<Q", struct.pack("<d", value))[0]:016x}'))
    return dict(queries=queries, **(dict(probability=probability) if probability else {}))


def compare(case, gpu, contains):
    native = observe(case)
    contains(gpu, native, case['name']+'.native_geometry')
    if 'expected_marker' in case:
        owner = case.get('owners', [0])[-1]
        assert native['queries'][-1]['attack_buffs'][owner] == case['expected_marker'], case['name']
    return native
