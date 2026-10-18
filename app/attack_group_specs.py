"""Identity and frozen target sets for one explicitly delimited attack.

The producer chooses eligible actor kinds; this module does not guess whether
parts, cover, shields or summoned units satisfy a particular game's clause.
"""
from dataclasses import dataclass
import math
from impact_specs import ActorHandle,ActorKind

MAX_GROUPS=32
MAX_TARGETS=128

def checked_time(t):
    if type(t) not in (int,float) or not math.isfinite(t) or t<0:raise ValueError('Invalid attack group time')
    return t

@dataclass(frozen=True)
class AttackKey:
    caster:str
    identity:int
    epoch:int
    def __post_init__(self):
        if not isinstance(self.caster,str) or not self.caster or type(self.identity) is not int or not 1<=self.identity<2**24 or type(self.epoch) is not int or self.epoch<1:
            raise ValueError('Invalid attack group identity')

@dataclass(frozen=True)
class AttackTargets:
    key:AttackKey
    targets:tuple
    def __post_init__(self):
        object.__setattr__(self,'targets',tuple(self.targets))
        if not isinstance(self.key,AttackKey) or len(self.targets)>MAX_TARGETS or any(not isinstance(t,ActorHandle) for t in self.targets) or len(set(self.targets))!=len(self.targets):
            raise ValueError('Invalid distinct attack targets')

def actor_policy(kinds):
    values=tuple(kinds)
    if not values or any(type(k) not in (int,ActorKind) for k in values):raise ValueError('Attack groups require explicit eligible actor kinds')
    return frozenset(ActorKind(k) for k in values)

def simultaneous_threshold(timing):
    raw=timing.split(':',1)[1]
    if not raw.isascii() or not raw.isdecimal() or str(int(raw))!=raw or not 1<=int(raw)<=MAX_TARGETS:raise ValueError('Invalid simultaneous-target threshold')
    return int(raw)

def listener_plan(effects,caster):
    result=[];seen=set()
    for effect,owner in effects:
        if owner!=caster:continue
        for timing in effect.get('trigger',{}).get('timing',()):
            if not timing.startswith('multi_hit:') or timing in seen:continue
            threshold=simultaneous_threshold(timing)
            seen.add(timing);result.append((timing,threshold))
    return tuple(result)
