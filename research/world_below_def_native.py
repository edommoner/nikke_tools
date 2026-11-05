"""Observe actual target and effective-defense reads; never add a query."""
import engine_worker
from contextlib import contextmanager
from unittest.mock import patch
from calculator.buff_manager import BuffManager
from world_frame_native import roster_names
from world_projectile_native import observe as plain

@contextmanager
def capture(names):
    resolve,defense,lazy=BuffManager._resolve_target,BuffManager._effective_def,BuffManager._resolve_lazy
    rows=[];stack=[];depth=0
    def target(bm,raw,caster):
        if raw!='allies_below_def':return resolve(bm,raw,caster)
        row=dict(owner=names.index(caster),lazy=depth>0,reads=[]);rows.append(row);stack.append(row)
        try:
            result=resolve(bm,raw,caster);row['picked']=[names.index(n) for n in result];return result
        finally:assert stack.pop() is row
    def read(bm,name):
        value=defense(bm,name)
        if stack:stack[-1]['reads'].append(dict(who=names.index(name),value=value))
        return value
    def deferred(bm,ab):
        nonlocal depth
        depth+=1
        try:return lazy(bm,ab)
        finally:depth-=1
    with patch.object(BuffManager,'_resolve_target',target),patch.object(BuffManager,'_effective_def',read),patch.object(BuffManager,'_resolve_lazy',deferred):yield rows

def observe(case):
    with capture(roster_names(case)) as rows:n,t=plain(case)
    n['below_def_selections']=rows;return n,t
