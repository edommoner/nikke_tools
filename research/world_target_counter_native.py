"""Actual native counter oracle for shared literal stimuli; no GPU inputs here."""
import dataclasses
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / p) for p in ('app', 'scripts', 'tests')]
from effect_runtime import pool, publish_impact, state
from impact_specs import ActorHandle, Impact
from target_counter_runtime import target_death
from test_target_counter_runtime import NAMES, manager


def observe_case(case):
    bm = manager(case['effects']); steps = []; uids = {}; latch_checks = []
    original = bm.notify
    def notify(event, t, caster, **ctx):
        if event.startswith('event:target_counter_complete:'):
            ready = [r for r in pool(bm, 'target_hit_counter').values() if r.credit >= r.spec.threshold]
            assert all(r.done for r in ready)
            latch_checks.append(dict(event=event, time=t, ready_count=len(ready), all_ready_latched=True))
        return original(event, t, caster, **ctx)
    bm.notify = notify
    def uid(raw):
        if raw not in uids: uids[raw] = len(uids) + 1
        return uids[raw]
    for t, action in case['actions']:
        bm.tick(t); kind, *args = action
        if kind in ('activate', 'refresh'):
            bm.notify('battle_start' if kind == 'activate' else 'on_attack', t, NAMES[0])
        elif kind == 'hit':
            f, o, k, identity, generation, credit, damage, *who = args
            publish_impact(bm, Impact(NAMES[who[0] if who else 2], ActorHandle(k, identity, generation), f, o, damage, credit), t)
        elif kind == 'death': target_death(bm, ActorHandle(*args), t)
        else: raise ValueError('Unknown native counter stimulus')
        records = [r for r in pool(bm, 'target_hit_counter').values() if any(ab is r.carrier for ab in bm._active)]
        # UID is process-global on CPU. Preserve equivalence/ordering with a
        # per-case ordinal; epochs and all other quantities remain unmodified.
        for r in records: uid(r.carrier.uid)
        trace = []
        for when, c in state(bm).counter_trace:
            row = dataclasses.asdict(c); row['uid_ordinal'] = uid(row.pop('uid')); row['time'] = when; trace.append(row)
        summary = [len(records), sum(r.credit for r in records), len(trace), state(bm).counter_epoch]
        expected = list(case['expected'][len(steps)])
        assert summary == expected, (case['name'], len(steps), summary, expected)
        assert state(bm).event_stack == [] and state(bm).impact_stack == []
        steps.append(dict(time=t, summary=summary, resources=[dict(uid_ordinal=uid(r.carrier.uid), epoch=r.epoch,
            name=r.carrier.effect['name'], owner=NAMES.index(r.caster), actor=dataclasses.asdict(r.spec.actor),
            credit=r.credit, expires=r.expires, done=r.done) for r in records], completions=trace,
            dead_actors=[dataclasses.asdict(a) for a in sorted(state(bm).dead_actors, key=lambda a: (int(a.kind), a.identity, a.generation))]))
    return dict(name=case['name'], steps=steps, latch_checks=latch_checks)


def activation_child_witness():
    from target_counter_cases import marker
    bm = manager([marker(threshold=1)]); events = []; original = bm.notify
    def notify(event, t, caster, **ctx):
        if event == 'event:marker' and caster == NAMES[0]:
            rows = list(pool(bm, 'target_hit_counter').values())
            events.append(dict(event=event, before_impact=[dict(epoch=r.epoch, credit=r.credit, done=r.done) for r in rows]))
            publish_impact(bm, Impact(NAMES[2], ActorHandle(0, 0, 1), 0, 2, 0, 1), t)
        return original(event, t, caster, **ctx)
    bm.notify = notify; bm.notify('battle_start', 0, NAMES[0])
    assert events == [dict(event='event:marker', before_impact=[dict(epoch=1, credit=0, done=False)])]
    assert not bm._active and len(state(bm).counter_trace) == 1 and state(bm).counter_epoch == 1
    return dict(passed=True, events=events, final_live_carriers=0, completions=1, epoch=1,
                preparation_precedes_named_activation_children=True, zero_damage_positive_credit=True)
