"""Pinned native BuffManager and damage formula;never supply CPU state to GPU."""
import copy
import engine_worker
from calculator.buff_manager import BuffManager
from calculator.damage import calc_damage,default_hit_type
from calculator import timeline
from timer_registry_cases import NAMES

def observe(case):
    attacks=case.get('base_atk',[1000]*5);allies=case['environment']['allies']
    chars=[dict(name=n,skill_levels={'1':10,'2':10,'3':10},_weapon=copy.deepcopy(engine_worker.META[n])) for n in NAMES]
    effects=[(copy.deepcopy(e),NAMES[o]) for e,o in zip(case['effects'],case['owners'])]
    class BM(BuffManager):
        def _register_all(self):self._effects=effects;self._build_notify_index()
    enemy={'def':0,'core_px':0,'code':None,'optimal_range_weapons':[]}
    state=dict(base_stats={n:dict(atk=a,hp=h['base_hp'],**{'def':0}) for n,a,h in zip(NAMES,attacks,allies)},hp={n:h.get('hp',h['base_hp']) for n,h in zip(NAMES,allies)},hp_pct={n:h.get('hp',h['base_hp'])/h['base_hp']*100 for n,h in zip(NAMES,allies)},enemy=enemy,full_burst=False,rng_acc={},rng_expected=True)
    bm=BM(chars,state=state);timeline._register_instant_handlers(bm,{n:object() for n in NAMES},None)
    total=[0]*5;packets=[];observations=[];queries=[];started=False
    def damage(e,caster,t):
        who=NAMES.index(caster);kind=e['stat'];assert kind in ('damage','burst_damage')
        buffs=bm.get_buffs(caster,'__enemy__',t)
        ht=default_hit_type(coeff=e.get('fixed_value',e.get('values',{}).get('10',0)),is_final_atk=True,is_burst_damage=kind=='burst_damage',is_single_burst=False,is_aoe_burst=False)
        amount=calc_damage(base_atk=attacks[who],buffs=buffs,weapon=chars[who]['_weapon'],hit_type=ht,enemy_def=0,expected=True)['damage']
        total[who]+=amount;packets.append(dict(time=t,owner=who,name=e['name'],amount=amount,atk_flat=buffs.get('atk_flat',0)))
    bm.register_damage_handler(damage)
    event_names={0:'battle_start',7:'on_attack',8:'hit_count',19:'event:full_reload'}
    for t,op,event,who,arg,index,extra,extra2 in case['script']:
        bm.tick(t)
        if op==4:
            assert not started
            for n in NAMES:bm.notify('battle_start',t,n)
            started=True
        elif op==0:bm.notify(event_names[event],t,NAMES[who])
        elif op==2:
            buffs=[bm.get_buffs(n,'__enemy__',t) for n in NAMES]
            queries.append(dict(damage=total.copy(),attack_buffs=[b['atk_pct'] for b in buffs]))
            observations.append(dict(time=t,flat=[b.get('atk_flat',0) for b in buffs],native_max_hp=[bm.effective_max_hp(n) for n in NAMES],native_rank=[bm._effective_atk(n) for n in NAMES],memberships=[None if ab.target_chars is None else ab.target_chars.copy() for ab in bm._active]))
        else:raise ValueError('HP attack oracle supports native notification and query stimuli only')
    return dict(queries=queries,native_observations=observations,packets=packets)
