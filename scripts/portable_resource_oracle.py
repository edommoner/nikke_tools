"""Independent original BuffManager/resource arithmetic and notification witness."""
import copy
import engine_worker
from calculator.buff_manager import BuffManager
from timer_registry_cases import NAMES

def observe(case):
    raw=[(copy.deepcopy(e),NAMES[o]) for e,o in zip(case['effects'],case.get('owners',[0]*len(case['effects'])))];ctx=[];trace=[]
    class BM(BuffManager):
        def _register_all(self):self._effects=raw;self._build_notify_index()
        def char_effects(self,n):return [e for e,o in raw if o==n]
        def _dispatch_instant(self,e,caster,t,*args,**kw):
            ctx.append(e.get('gauge_id'))
            try:return super()._dispatch_instant(e,caster,t,*args,**kw)
            finally:ctx.pop()
    chars=[dict(name=n,skill_levels={'1':10,'2':10,'3':10},_weapon=engine_worker.META[n]) for n in NAMES]
    allies=case.get('environment',{}).get('allies',[{} for _ in NAMES]);base={n:dict(atk=case.get('base_atk',[1000]*5)[i],hp=a.get('base_hp',1000000),**{'def':a.get('base_defense',0)}) for i,(n,a) in enumerate(zip(NAMES,allies))}
    bm=BM(chars,state=dict(base_stats=base,enemy={'def':0},full_burst=False,rng_acc={},rng_expected=True,hp={n:a.get('hp',base[n]['hp']) for n,a in zip(NAMES,allies)},hp_pct={n:100 for n in NAMES}))
    original=bm.notify
    def notify(event,t,caster,**kw):
        if event.startswith('every_stack:'):trace.append(dict(event=30,owner=NAMES.index(caster),resource=event.split(':',1)[1],time=t,boundary=kw['stack_value']))
        elif event=='squad_ammo_consume' and ctx and ctx[-1]:trace.append(dict(event=26,owner=NAMES.index(caster),resource=ctx[-1],time=t,boundary=1))
        return original(event,t,caster,**kw)
    bm.notify=notify;queries=[];resource_queries=[];started=False
    def query(name,who,t):
        gauges=bm.state.get('gauges',{}).get(NAMES[who],{});cap=gauges.get('_gauge_max:'+name)
        add=sum(a.effect.get('fixed_value',0.0) for a in bm._active if a.caster==NAMES[who] and a.effect.get('stat')=='gauge_max_add' and a.effect.get('gauge_id')==name)
        return dict(time=t,owner=who,resource=name,present=name in gauges,value=gauges.get(name,0.0),cap_present=cap is not None,base_cap=cap,effective_cap=cap+add if cap is not None else None)
    for t,op,event,who,arg,index,extra,extra2 in case['script']:
        if 'combat' not in case or op==4:bm.tick(t)
        if op==0:
            if event in (1,2):bm.state['full_burst']=event==1
            bm.notify({0:'battle_start',1:'full_burst_start',2:'full_burst_end',3:'burst_cast',7:'on_attack',8:'hit_count',19:'event:full_reload'}[event],t,NAMES[who])
        elif op==4:
            if not started:
                for n in NAMES:bm.notify('battle_start',t,n)
                started=True
            bm.tick(t)
        elif op==28:resource_queries.append(query(arg,who,t))
        elif op==2:queries.append(dict(attack_buffs=[bm.get_buffs(n,'__enemy__',t)['atk_pct'] for n in NAMES]))
        elif op==25:
            # This fixture family uses a lethal raw attack with no mitigation
            # effects; original knock_down owns actual resource/cap retention.
            for i,n in enumerate(NAMES):
                if arg&(1<<i):
                    assert extra*extra2/100>=bm.state['hp'][n]
                    bm.state['hp'][n]=0;bm.knock_down(n,t);bm.notify_down(n,t)
        else:raise ValueError('Unported resource witness command')
    return dict(queries=queries,resource_queries=resource_queries,resource_trace=trace,resource_trace_total=len(trace))
