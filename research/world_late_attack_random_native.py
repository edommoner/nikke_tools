"""Read-only native query/cache/sample observation; no extra numerical resolutions."""
import hashlib
import json
import random
from contextlib import contextmanager
from unittest.mock import patch
import engine_worker
from calculator.buff_manager import BuffManager
from world_frame_native import roster_names
from world_projectile_native import observe as plain_observe


def state_digest(state):
    return hashlib.sha256(json.dumps(state, separators=(',', ':')).encode()).hexdigest()


@contextmanager
def capture_queries(names):
    queries, samples, stack = [], [], []
    getter, sampler, lazy = BuffManager.get_buffs, random.sample, BuffManager._resolve_lazy
    lazy_depth = 0

    def queried(bm, caster, target, t, exclude_names=frozenset()):
        key = (caster, target, t, bm._cache_version, bm._value_version, exclude_names)
        row = dict(owner=names.index(caster), target=target, time=t,
                   cache_version=bm._cache_version, value_version=bm._value_version,
                   exclude=sorted(exclude_names), hit=key in bm._buffs_cache,
                   sample_indices=[], before_index=random.getstate()[1][-1])
        index = len(queries)
        queries.append(row)
        stack.append(index)
        try:
            result = getter(bm, caster, target, t, exclude_names)
            row['after_index'] = random.getstate()[1][-1]
            row['buffs'] = dict(result)
            return result
        finally:
            stack.pop()

    def sampled(pool, k, **kwargs):
        before = random.getstate()
        result = sampler(pool, k, **kwargs)
        after = random.getstate()
        row = dict(pool=[names.index(n) for n in pool], k=k,
                   picked=[names.index(n) for n in result],
                   query=stack[-1] if stack else None, lazy=lazy_depth != 0,
                   before_index=before[1][-1], after_index=after[1][-1],
                   before_sha256=state_digest(before), after_sha256=state_digest(after))
        if stack:
            queries[stack[-1]]['sample_indices'].append(len(samples))
        samples.append(row)
        return result

    def lazily(bm, ab):
        nonlocal lazy_depth
        lazy_depth += 1
        try:
            return lazy(bm, ab)
        finally:
            lazy_depth -= 1

    with patch.object(BuffManager, 'get_buffs', queried), patch.object(random, 'sample', sampled), patch.object(BuffManager, '_resolve_lazy', lazily):
        yield queries, samples


def observe(case):
    with capture_queries(roster_names(case)) as (queries, samples):
        native, trace = plain_observe(case)
    native['late_attack_random'] = dict(queries=queries, samples=samples)
    return native, trace
