"""Independent native owned-source clocks and references, after GPU readback."""
import copy
import engine_worker
from calculator.buff_manager import BuffManager
from effect_runtime import pool
from periodic_source_specs import specification
from timer_registry_cases import NAMES

def observe(case):
    raw=[(copy.deepcopy(e),NAMES[o]) for e,o in zip(case['effects'],case.get('owners',[0]*len(case['effects'])))];source_rows={};refresh_times={};notifications=[]
    class BM(BuffManager):
        def _register_all(self):self._effects=raw;self._build_notify_index()
        def char_effects(self,name):return [e for e,n in raw if n==name]
        def _dispatch_instant(self,effect,caster,t,*args,**kwargs):
            result=super()._dispatch_instant(effect,caster,t,*args,**kwargs)
            spec=specification(effect)
            if spec is not None:
                record=pool(self,'periodic_sources')[caster,spec.name];source_rows[caster,spec.name]=next(i for i,(e,n) in enumerate(raw) if e is effect);refresh_times[caster,spec.name]=t
            return result
        def notify(self,event,t,caster,*args,**kwargs):
            if event=='feather_tick' or event.startswith('source_tick:'):notifications.append(dict(event=event,time=t,owner=NAMES.index(caster)))
            return super().notify(event,t,caster,*args,**kwargs)
    chars=[dict(name=n,skill_levels={'1':10,'2':10,'3':10},_weapon=engine_worker.META[n]) for n in NAMES]
    bm=BM(chars,state=dict(base_stats={n:dict(atk=1000,hp=1000000,**{'def':0}) for n in NAMES},enemy={'def':0},full_burst=False,rng_acc={},rng_expected=True))
    from calculator import timeline
    timeline._register_instant_handlers(bm,{n:object() for n in NAMES},None)
    queries=[];source_queries=[];started=False
    for t,op,event,who,arg,index,extra,extra2 in case['script']:
        if op==4 and not started:
            for n in NAMES:bm.notify('battle_start',t,n)
            started=True
        if 'combat' not in case or op==4:bm.tick(t)
        if op==0:bm.notify({0:'battle_start',7:'on_attack',8:'hit_count',19:'event:full_reload'}[event],t,NAMES[who])
        elif op==4:pass
        elif op==2:queries.append(dict(attack_buffs=[bm.get_buffs(n,'__enemy__',t)['atk_pct'] for n in NAMES]))
        elif op==29:
            record=pool(bm,'periodic_sources').get((NAMES[who],arg))
            source_queries.append(dict(time=t,owner=who,name=arg,present=record is not None,count=record.count(t) if record else 0,epoch=record.epoch if record else 0,scheduled=record is not None and record.next_at is not None,next_at=record.next_at if record else None))
        else:raise ValueError('Unported owned-source witness stimulus')
    sources=[dict(name=name,owner=NAMES.index(owner),definition=source_rows[owner,name],legacy=record.spec.legacy,epoch=record.epoch,scheduled=record.next_at is not None,count=record.count(t),refreshed=refresh_times[owner,name],next_at=record.next_at) for (owner,name),record in pool(bm,'periodic_sources').items()]
    return dict(queries=queries,source_queries=source_queries,periodic_sources=sources,notifications=notifications)
