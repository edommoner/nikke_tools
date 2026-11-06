"""External CPU bucket observation and S17 experiment. No reference source edits.

Each evaluation is a fresh subprocess. Scalar wrappers observe the ORIGINAL
function's return-frame locals (including RNG decisions), never recompute factors.
Only landed SimResult.hits are aggregated; speculative scalar calls are counted.
"""
from __future__ import annotations
import argparse, collections, contextlib, copy, functools, hashlib, json, math
import os, pathlib, shutil, socket, subprocess, sys, time
from unittest.mock import patch
sys.dont_write_bytecode = True
ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'app'))
KNOBS = {'atk': (2, [100, 1000]), 'crit_dmg': (3, [1, 5]),
         'charge_dmg_pct': (4, [1, 5]), 'element_bonus': (7, [1, 5])}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                    separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def clean(value):
    # Full CPU payload is deterministic in this experiment. Exclude nothing.
    return value


class BucketLog:
    """Scoped wrappers, preserving object identity and restoring every binding.

    damage.calc_damage itself stays original: destructible_damage_policy clones
    its globals to replace factor5. Wrapping that binding would break the clone.
    Instead its calculate entry and the local-import resolve entry are observed.
    """
    def __init__(self):
        self.scalars = []
        self.events = {}
        self.hits = []
        self.sites = collections.Counter()
        self.pending = []

    def wrapper(self, original):
        @functools.wraps(original)
        def call(*args, **kwargs):
            previous = sys.getprofile()
            def observe(frame, event, result):
                if event == 'return' and frame.f_code.co_name in ('calc_damage', 'calc_damage_avg'):
                    loc = frame.f_locals
                    if all('f'+str(i) in loc for i in range(1, 8)):
                        self.scalar(frame, result)
            # Nested observed entries share the outer observer; avoid duplicates.
            if getattr(previous, '_bucket_observer', False):
                return original(*args, **kwargs)
            observe._bucket_observer = True
            sys.setprofile(observe)
            try:
                return original(*args, **kwargs)
            finally:
                sys.setprofile(previous)
        return call

    def scalar(self, frame, result):
        loc = frame.f_locals
        ht = dict(loc['hit_type']); buffs = loc['buffs']
        attacker = None; when = None; scaling = []
        caller = frame.f_back
        for _ in range(24):
            if caller is None: break
            v = caller.f_locals
            if when is None: when = v.get('t', v.get('when'))
            if attacker is None:
                attacker = v.get('caster')
                if not isinstance(attacker, str):
                    cs = v.get('cs', v.get('self'))
                    attacker = getattr(cs, 'name', None)
                if not attacker and isinstance(v.get('character'), dict): attacker = v['character'].get('name')
                if not attacker and isinstance(v.get('name'), str): attacker = v['name']
            if '_scalings' in v: scaling = v['_scalings']
            if caller.f_code.co_filename.endswith('timeline.py'):
                site = f"{caller.f_code.co_name}:{caller.f_lineno}"
                self.sites[site] += 1
                # Keep walking for enclosing caster/time when nested helper lacks it.
            caller = caller.f_back
        factors = [loc['f'+str(i)] for i in range(1, 8)]
        damage = result['damage'] if isinstance(result, dict) else result
        record = dict(attacker=attacker, time=when, factors=factors, damage=damage,
                      full_burst=bool(ht.get('is_full_burst')), flags=ht,
                      crit_frac=loc.get('crit_frac'), is_crit=loc.get('is_crit'),
                      expected=bool(loc.get('expected', True)),
                      slopes={'atk': 0. if 'max_hp_replacement' in scaling else 1+buffs.get('atk_pct', 0)/100,
                              'crit_dmg': (loc.get('crit_frac', 0) or 0)/100,
                              'charge_dmg_pct': .01 if ht.get('is_full_charge') else 0.,
                              'element_bonus': .01 if buffs.get('is_element_match') else 0.})
        self.scalars.append(record); self.pending.append(record)

    def __enter__(self):
        import engine_worker
        from calculator import timeline
        import destructible_damage_policy, destructible_skill_runtime
        self.stack = contextlib.ExitStack()
        for obj, name in ((timeline, 'calc_damage'),
                          (destructible_damage_policy, 'calculate'),
                          (destructible_skill_runtime, 'resolve')):
            self.stack.enter_context(patch.object(obj, name, self.wrapper(getattr(obj, name))))
        original_init = timeline.HitEvent.__init__
        def initialize(event, *args, **kwargs):
            original_init(event, *args, **kwargs)
            record = None
            if event.hit_tag not in ('accum_split_damage', 'dealt_fixed_damage'):
                for i in range(len(self.pending)-1, -1, -1):
                    p = self.pending[i]
                    if p['attacker'] == event.caster and p['time'] == event.t and p['damage'] == event.damage:
                        record = self.pending.pop(i)
                        record['kind'] = event.hit_tag
                        break
            self.events[id(event)] = (event, record)
        self.stack.enter_context(patch.object(timeline.HitEvent, '__init__', initialize))
        original_execute = engine_worker.sim.execute
        def execute(*args, **kwargs):
            result = original_execute(*args, **kwargs)
            self.hits = list(result.hits)
            return result
        self.stack.enter_context(patch.object(engine_worker.sim, 'execute', execute))
        return self

    def __exit__(self, *args):
        return self.stack.__exit__(*args)

    def aggregate(self, payload):
        groups = {}; member = collections.Counter(); uncovered = collections.Counter()
        prediction = {k: {str(m): {'first': 0., 'exact': 0.} for m in v[1]} for k,v in KNOBS.items()}
        # Window boundaries come from actual full-burst starts in the CPU payload.
        starts = [e['time'] for e in payload['burst_timeline'] if e['event'] == 'full_burst 시작']
        for hit in self.hits:
            member[hit.caster] += hit.damage
            pair = self.events.get(id(hit)); record = pair[1] if pair and pair[0] is hit else None
            if record is None:
                uncovered[hit.hit_tag] += hit.damage
                continue
            window = sum(t <= hit.t+1e-3 for t in starts) if record['full_burst'] else 0
            key = (hit.caster, hit.hit_tag, record['full_burst'], window)
            if key not in groups:
                groups[key] = dict(attacker=hit.caster, kind=hit.hit_tag, full_burst=record['full_burst'],
                                   window=window, hits=0, damage=0, damage_over_bucket=[0.]*7,
                                   zero_buckets=[0]*7, first_time=hit.t, last_time=hit.t,
                                   crit_fraction_sum=0., core_fraction_sum=0.)
            g = groups[key]; g['hits'] += 1; g['damage'] += hit.damage; g['last_time'] = hit.t
            g['crit_fraction_sum'] += record['crit_frac'] or 0.
            core_prob = record['flags'].get('core_prob')
            g['core_fraction_sum'] += (core_prob if record['expected'] and core_prob is not None
                                       else float(record['flags'].get('is_core', False)))
            for i, b in enumerate(record['factors']):
                if b: g['damage_over_bucket'][i] += hit.damage/b
                else: g['zero_buckets'][i] += 1
            for knob, (group, magnitudes) in KNOBS.items():
                b = record['factors'][group-1]
                if not b: continue
                slope = record['slopes'][knob]
                # One group is changed: these are algebraically identical.
                for magnitude in magnitudes:
                    x = slope*magnitude
                    prediction[knob][str(magnitude)]['first'] += hit.damage*x/b
                    prediction[knob][str(magnitude)]['exact'] += hit.damage*((b+x)/b-1)
        expected = {m['name']: m['damage'] for m in payload['members']}
        if dict(member) != {k:v for k,v in expected.items() if v}:
            raise AssertionError(('Hit reconciliation', dict(member), expected))
        if sum(member.values()) != payload['total_damage']: raise AssertionError('Total reconciliation')
        return dict(groups=list(groups.values()), landed_hits=len(self.hits), scalar_calls=len(self.scalars),
                    call_sites=dict(self.sites), member_hit_damage=dict(member), reconciliation=True,
                    uncovered_by_kind=dict(uncovered), uncovered_damage=sum(uncovered.values()),
                    uncovered_share=sum(uncovered.values())/max(payload['total_damage'], 1), unit_predictions=prediction)


def perturb(body, knob, magnitude):
    body = copy.deepcopy(body)
    if knob == 'atk':
        body['stat_deltas'] = {n: {'atk': magnitude} for n in body['squad']}
    else:
        for n in body['squad']:
            current = body.get('patches', {}).get(n, {}).get('equip_skills', {}).get(knob,
                          body['profile']['chars'][n]['equip_skills'].get(knob, 0))
            value = sum(current) if isinstance(current, list) else current
            body.setdefault('patches', {}).setdefault(n, {}).setdefault('equip_skills', {})[knob] = value+magnitude
    return body


def worker(request):
    import engine_worker
    body = request['body']; started = time.perf_counter()
    if request.get('logged'):
        with BucketLog() as log: payload = engine_worker.evaluate(body)
        result = dict(payload=payload, buckets=log.aggregate(payload))
    else:
        original_execute = engine_worker.sim.execute
        diagnostic = {}
        def execute(*args, **kwargs):
            executed = original_execute(*args, **kwargs)
            counts = collections.Counter((h.caster, h.hit_tag) for h in executed.hits)
            damages = collections.Counter()
            for h in executed.hits: damages[(h.caster, h.hit_tag)] += h.damage
            diagnostic.update(hit_counts={' / '.join(k):v for k,v in counts.items()},
                              hit_damage={' / '.join(k):v for k,v in damages.items()})
            return executed
        with patch.object(engine_worker.sim, 'execute', execute):
            result = dict(payload=engine_worker.evaluate(body), diagnostic=diagnostic)
    result.update(seconds=time.perf_counter()-started, host=socket.gethostname(), payload_digest=digest(clean(result['payload'])))
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--worker', action='store_true')
    p.add_argument('--body', type=pathlib.Path)
    p.add_argument('--out', type=pathlib.Path)
    args = p.parse_args()
    if args.worker:
        print(json.dumps(worker(json.load(sys.stdin)), ensure_ascii=False, allow_nan=False))
    elif args.body and args.out:
        body = json.loads(args.body.read_text())
        body['compute_backend'] = 'cpu'
        results = []
        for logged in (False, True):
            r = subprocess.run([sys.executable, __file__, '--worker'], input=json.dumps(dict(body=body, logged=logged)), text=True, capture_output=True, check=True)
            results.append(json.loads(r.stdout))
        if clean(results[0]['payload']) != clean(results[1]['payload']): raise AssertionError('Non-interference')
        args.out.write_text(json.dumps(dict(non_interference=True, baseline=results[0], logged=results[1]), ensure_ascii=False)+'\n')
    else: p.error('Use --worker, or --body BODY --out RESULT')

if __name__ == '__main__': main()
