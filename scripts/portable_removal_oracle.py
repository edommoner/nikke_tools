"""Native named-removal state, membership and timer reference after GPU readback.
The command table drives an independent native ActorRegistry and BuffManager;
no GPU targets, modifier sums or intermediate state are fed to this observer.
"""
import copy
import engine_worker
from calculator import timeline
from calculator.buff_manager import BuffManager
from calculator.boss_pattern import BossScript,Pattern,SummonSpec,DEFAULT_BOSS_ATK,_Add,AIM_ADDS
from effect_runtime import state
from impact_specs import ActorKind
from world_actor_runtime import ActorRegistry
from world_condition_specs import target_inheritance_events
from timer_registry_cases import NAMES


def observe(case):
    targets=case['combat']['targets'];raw=[(copy.deepcopy(e),NAMES[o]) for e,o in zip(case['effects'],case.get('owners',[0]*len(case['effects'])))]
    endings=[]
    class BM(BuffManager):
        def notify(self,event,t,caster,*args,**kwargs):
            if event.startswith("event:state_end:"):endings.append(dict(name=event.split(":",2)[2],caster=NAMES.index(caster),time=t))
            return super().notify(event,t,caster,*args,**kwargs)
        def _register_all(self):self._effects=raw;self._build_notify_index()
        def char_effects(self,name):return [e for e,n in raw if n==name]
    chars=[dict(name=n,skill_levels={'1':10,'2':10,'3':10},_weapon=engine_worker.META[n]) for n in NAMES]
    allies=case.get('environment',{}).get('allies',[{} for _ in NAMES]);attacks=case.get('base_atk',[1000]*5)
    enemy={'def':targets[0].get('defense',0),'core_px':0,'code':None,'atk':targets[0].get('attack',DEFAULT_BOSS_ATK)}
    bm=BM(chars,state=dict(base_stats={n:dict(atk=attacks[i],hp=a.get('base_hp',1000000),**{'def':a.get('base_defense',0)}) for i,(n,a) in enumerate(zip(NAMES,allies))},enemy=enemy,full_burst=False,rng_acc={},rng_expected=True))
    bm.state['hp']={n:a.get('hp',a.get('base_hp',1000000)) for n,a in zip(NAMES,allies)}
    bm.state['hp_pct']={n:bm.state['hp'][n]/a.get('base_hp',1000000)*100 for n,a in zip(NAMES,allies)}
    timeline._register_instant_handlers(bm,{n:object() for n in NAMES},None)
    boss=BossScript([Pattern(idx=0,id='authored',kind='summon',after=())],enemy,lambda *_:False);run=boss._runs[0];run.active=True
    run.adds=[_Add(id=f'__enemy__:add:{i}',name=f'__enemy__:add:{i}',spec=SummonSpec(name=f'__enemy__:add:{i}',hp=t['hp'],atk=t.get('attack',0)),order=i,gone='' if t.get('active',True) else 'retired') for i,t in enumerate(targets) if i]
    generations=[t.get('generation',1) for t in targets];active=[t.get('active',True) for t in targets]
    registry=ActorRegistry();registry.bind(ActorKind.BODY,'__enemy__',lambda:(generations[0],active[0],None),identity=0)
    for i in range(1,len(targets)):
        registry.bind(ActorKind.ADD,f'__enemy__:add:{i}',lambda i=i:(generations[i],active[i] and run.adds[i-1].alive,None),identity=i-1)
    state(bm).world_actor_registry=(boss,registry)
    auto=case['combat'].get('automatic_add_aim',[False]*5)
    boss.aim_of={n:AIM_ADDS if auto[i] else 'body' for i,n in enumerate(NAMES)}
    bm.enemy_resolver=lambda target,caster:boss.resolve_enemies(target,caster=caster)
    packets=[]
    def packet(effect,caster,t):
        members=[]
        for ab in bm._active:
            if ab.effect is effect:members.extend(ab.target_chars or [])
        targets=[0 if n=='__enemy__' else int(n.rsplit(':',1)[1]) for n in members if n.startswith('__enemy__')]
        packets.append(dict(name=effect.get('name'),caster=NAMES.index(caster),time=t,target_mask=sum(1<<i for i in set(targets))))
    bm.register_damage_handler(packet)
    events={0:'battle_start',14:'last_bullet',7:'on_attack',8:'hit_count',17:'event:cover_healed',19:'event:full_reload'}
    current=0;started=False;queries=[];spawn_order=len(targets)
    for t,op,event,who,arg,index,extra,extra2 in case['script']:
        bm.tick(t)
        if op==4:
            if not started:
                for n in NAMES:bm.notify('battle_start',t,n)
                started=True
        elif op==20:
            current=arg;boss.aim_of[NAMES[who]]=AIM_ADDS if arg else 'body'
        elif op==27:
            boss.aim_of[NAMES[who]]=AIM_ADDS if arg else 'body'
            label=boss.resolve_enemies('enemies_nearest:1',caster=NAMES[who])[0]
            current=0 if label=='__enemy__' else int(label.rsplit(':',1)[1])
        elif op==22:
            active[arg]=False
            if arg:run.adds[arg-1].gone='retired'
            bm._invalidate_buffs_cache()
        elif op==21:
            generations[arg]+=1;active[arg]=True
            if arg:
                run.adds[arg-1]=_Add(id=f'__enemy__:add:{arg}',name=f'__enemy__:add:{arg}',spec=SummonSpec(name=f'__enemy__:add:{arg}',hp=extra,atk=targets[arg].get('attack',0)),order=spawn_order)
                spawn_order+=1
            bm._invalidate_buffs_cache()
        elif op==0:
            target=current if event in target_inheritance_events() else 0
            actor=registry.view(ActorKind.BODY if target==0 else ActorKind.ADD,'__enemy__' if target==0 else f'__enemy__:add:{target}').handle
            bm.notify(events[event],t,NAMES[who],target_context=actor)
        elif op==2:
            target=max(arg,0);label='__enemy__' if target==0 else f'__enemy__:add:{target}'
            buffs=bm.get_buffs(NAMES[who],label,t)
            queries.append(dict(allies=[dict(hp=bm.state['hp'][n],max_hp=bm.effective_max_hp(n),hp_pct=bm.state['hp_pct'][n]) for n in NAMES],enemy_modifiers=dict(defense_pct=buffs['enemy_def_down_pct'],defense_flat=buffs['enemy_def_down_flat'],received_damage_pct=buffs['received_dmg']),attack_buffs=[bm.get_buffs(n,'__enemy__',t)['atk_pct'] for n in NAMES]))
        else:raise ValueError('Unsupported enemy-buff reference stimulus')
    def member(label):
        if label in NAMES:return 1<<NAMES.index(label)
        if label=='__enemy__':return 1<<5
        return 1<<(int(label.rsplit(':',1)[1])+5)
    carriers=[]
    for ab in bm._active:
        definition=next(i for i,(e,_) in enumerate(raw) if e is ab.effect)
        carriers.append(dict(definition=definition,recipients=sum(member(n) for n in (ab.target_chars or [])),stacks=ab.stack,lazy_pending=ab.target_chars is None))
    clocks=[]
    for timers in (bm._instant_timers,bm._dot_timers):
        for key,(_,due,expiry) in timers.items():
            definition=next(i for i,(e,_) in enumerate(raw) if id(e)==key)
            clocks.append(dict(definition=definition,due=due,expiry=1e30 if expiry==float('inf') else expiry))
    return dict(queries=queries,carriers=carriers,timers=sorted(clocks,key=lambda c:c['definition']),endings=endings,packets=packets)
