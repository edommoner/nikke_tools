"""Observe original queued AttackHit objects, not a Python scheduler rewrite."""
from unittest.mock import patch
import world_schedule_native as base


def observe(case,patterns):
    queued=[];original=base.BossScript
    names={p.id:p.idx for p in patterns}
    class Observer(original):
        def begin_frame(self,t,enemy):
            events=super().begin_frame(t,enemy)
            for hit in self.attacks:
                node=names[hit.pattern];run=self._runs[node]
                slot=0 if not hit.source else next(i+1 for i,a in enumerate(run.adds) if a.name==hit.source)
                queued.append([node,slot,run.opens,hit.index,*base.bits(t),0,0])
            return events
    with patch.object(base,'BossScript',Observer):native=base.observe(case,patterns)
    native['queued_attacks']=queued
    native['scope']='Shared ADD firing cursor and graph component; authored clear stimuli, no battle damage/ammo/GPU admission'
    return native
