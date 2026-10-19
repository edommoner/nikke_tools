"""Actual installed CPU timeline for authored static packet/landing fixtures."""
import copy
import engine_worker
from calculator import timeline,buff_manager
from calculator.buff_manager import BuffManager
from portable_weapon_oracle import authored_weapon,authored_weapon_state
from timer_registry_cases import NAMES

def observe(case):
    raw=[(copy.deepcopy(e),NAMES[o]) for e,o in zip(case['effects'],case['owners'])];allies=case['environment']['allies'];attacks=case.get('base_atk',[1000]*5);cfg=case['combat'];duration=case['native_duration'];history=[];capture={};frames=[]
    old_bm,old_char,old_controller,old_boss=timeline.BuffManager,timeline.CharState,timeline.BurstController,timeline.BossScript
    add_raw={n:0 for n in NAMES}
    tables=[]
    for table in (timeline._NIKKE,buff_manager._NIKKE):
        if not any(table is other for other,_ in tables):tables.append((table,{n:table[n] for n in NAMES}))
    class Manager(BuffManager):
        def _register_all(self):self._effects=raw;self._build_notify_index()
        def char_effects(self,name):return [e for e,n in raw if n==name]
        def __init__(self,*args,**kwargs):
            super().__init__(*args,**kwargs);capture['bm']=self
            for n,h,a in zip(NAMES,allies,attacks):self.state['base_stats'][n].update(atk=a,hp=h['base_hp']);self.state['hp'][n]=h['hp'];self.state['hp_pct'][n]=h['hp']/h['base_hp']*100
            self.state['burst_gauge']=cfg.get('initial_gauge',0)
        def notify(self,event,t,owner,*args,**kwargs):
            if event in ('on_attack','hit_count','event:heal_received') or event.startswith('hit_count:'):history.append(dict(event=event,time=t,owner=NAMES.index(owner),hp=self.state['hp'][owner]))
            return super().notify(event,t,owner,*args,**kwargs)
        def apply_shared_body_heal(self,name,amount,t):
            history.append(dict(event='native-body-heal',time=t,owner=NAMES.index(name),hp=self.state['hp'][name],amount=amount));return super().apply_shared_body_heal(name,amount,t)
    class Boss(old_boss):
        def __init__(self,*args,**kwargs):super().__init__(*args,**kwargs);capture['boss']=self
        def hit_add(self,event,name,t):
            result=super().hit_add(event,name,t)
            if result:add_raw[event.caster]+=event.damage
            return result
    class Controller(old_controller):
        def __init__(self,*args,**kwargs):super().__init__(*args,**kwargs);capture['controller']=self
    def actor(char,*args):
        index=NAMES.index(char['name']);w=cfg['weapons'][index];authored_weapon(char,w);st=authored_weapon_state(char,w,attacks[index]);tick=st.tick
        def run(t,*a,**k):
            if index==0:frames.append(t)
            return tick(t,*a,**k) if w.get('enabled',False) else []
        st.tick=run;return st
    try:
        for table,saved in tables:
            for n,w in zip(NAMES,cfg['weapons']):table[n]={**saved[n],'burst_stage':str(w.get('stage',0)),'burst_cooldown':w.get('cooldown',40),'charge_time':0}
        timeline.BuffManager=Manager;timeline.CharState=actor;timeline.BurstController=Controller;timeline.BossScript=Boss
        chars=[dict(name=n,skill_levels={'1':10,'2':10,'3':10},_weapon=copy.deepcopy(engine_worker.META[n])) for n in NAMES]
        result=timeline.simulate(chars,dict(duration=duration,rng_mode='expected',burst_gauge_mode='accumulate'),dict(**{'def':0},core_px=0,code=None,optimal_range_weapons=[],**case.get('native_enemy',{})))
        bm=capture['bm'];ctrl=capture['controller'];totals=[result.char_total.get(n,0)+add_raw[n] for n in NAMES]
        query=dict(damage=totals,allies=[dict(hp=bm.state['hp'][n],max_hp=bm.effective_max_hp(n),hp_pct=bm.state['hp_pct'][n],down=bm.is_down(n)) for n in NAMES],attack_buffs=[bm.get_buffs(n,'__enemy__',duration)['atk_pct'] for n in NAMES],pending_burst=dict(count=len(ctrl._pending_burst_dmg)))
        return dict(queries=[query],history=history,frames=frames,hits=[dict(owner=NAMES.index(h.caster),time=h.t,damage=h.damage,tag=h.hit_tag) for h in result.hits])
    finally:
        timeline.BuffManager=old_bm;timeline.CharState=old_char;timeline.BurstController=old_controller;timeline.BossScript=old_boss
        for table,saved in tables:
            for n,data in saved.items():table[n]=data
