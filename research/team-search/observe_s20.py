"""External S20 profile/action observer; preserves original return objects.

Extends S18 attribution only in this fresh process. It does not edit the
reference or call getters speculatively. Logged/plain payloads are compared by
the coordinator before an observation is accepted.
"""
import collections
import functools
import json
import sys
import time
from unittest.mock import patch
import profile_s18 as old

ACTION_KEYS = ['max_ammo_pct', 'max_ammo_flat', 'reload_speed_pct',
               'attack_speed_pct', 'charge_speed_pct', 'charge_time_flat',
               'reload_ratio_pct', 'burst_cooldown']


class Observer(old.ProfileLog):
    def __init__(self, target, duration):
        super().__init__(target, duration)
        self.actions = collections.Counter()
        self.method_stats = {}
        self.instant_events = []
        self.weapon_cycle = {}

    def __enter__(self):
        old.KEYS.extend(k for k in ACTION_KEYS if k not in old.KEYS)
        super().__enter__()
        from calculator.timeline import CharState, BurstController
        from calculator.buff_manager import BuffManager
        initialize = CharState.__init__
        def initialized(cs, *args, **kw):
            initialize(cs, *args, **kw)
            if cs.name == self.target:
                self.weapon_cycle = {k: getattr(cs, k, None) for k in
                    ('fire_mode', 'fire_rate', 'fire_rate_max', 'warmup_bullets',
                     'charge_time_base', 'post_fire_delay', 'post_reload_delay',
                     'clip_count', 'pre_fire_delay')}
        self.stack.enter_context(patch.object(CharState, '__init__', initialized))
        register = BuffManager.register_instant_handler
        def registered(manager, stat, handler):
            @functools.wraps(handler)
            def observed(effect, caster, t, val):
                value = handler(effect, caster, t, val)
                if caster == self.target and stat in ('burst_cooldown_reduce', 'ammo_charge_pct', 'ammo_charge_flat', 'burst_reentry'):
                    self.instant_events.append(dict(stat=stat, time=t, value=val, effect=effect.get('name')))
                return value
            return register(manager, stat, observed)
        self.stack.enter_context(patch.object(BuffManager, 'register_instant_handler', registered))
        for name in ('_charge_fire', '_start_reload', '_finish_reload',
                     '_current_fire_rate', '_effective_charge_time',
                     '_reload_duration', '_full_ammo'):
            original = getattr(CharState, name)

            def wrap(original=original, name=name):
                @functools.wraps(original)
                def observed(cs, *args, **kw):
                    value = original(cs, *args, **kw)
                    if cs.name == self.target:
                        self.actions[name] += 1
                        if isinstance(value, (int, float)):
                            row = self.method_stats.setdefault(name, dict(n=0, sum=0., min=value, max=value))
                            row['n'] += 1
                            row['sum'] += value
                            row['min'] = min(row['min'], value)
                            row['max'] = max(row['max'], value)
                    return value
                return observed
            self.stack.enter_context(patch.object(CharState, name, wrap()))
        return self

    def scalar(self, frame, result):
        super().scalar(frame, result)
        self.scalars[-1]['action_received'] = {k: frame.f_locals['buffs'].get(k, 0.) for k in ACTION_KEYS}

    def compact(self, payload):
        result = super().compact(payload)
        samples = collections.defaultdict(list)
        for h in self.hits:
            if h.caster != self.target:
                continue
            pair = self.events.get(id(h))
            if pair and pair[0] is h and pair[1] is not None:
                r = pair[1]
                samples[(h.hit_tag, r['full_burst'])].append(r['action_received'])
        for g in result['groups']:
            rows = samples[(g['kind'], g['phase'])]
            g['action_received'] = {k: sum(r[k] for r in rows)/len(rows) for k in ACTION_KEYS}
        result['actions'] = dict(self.actions)
        result['method_stats'] = self.method_stats
        result['instant_events'] = self.instant_events
        result['weapon_cycle'] = self.weapon_cycle
        return result


def worker(request):
    import engine_worker
    body = request['body']
    started = time.perf_counter()
    if request.get('logged'):
        with Observer(request['target'], body['duration']) as observer:
            payload = engine_worker.evaluate(body)
        profile = observer.compact(payload)
    else:
        payload = engine_worker.evaluate(body)
        profile = None
    return dict(payload=payload, profile=profile, seconds=time.perf_counter()-started,
                payload_digest=old.b.digest(payload))


if __name__ == '__main__':
    print(json.dumps(worker(json.load(sys.stdin)), ensure_ascii=False, allow_nan=False))
