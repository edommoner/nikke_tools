"""Independent CPU weapon regression for authored mechanical inputs.
Called only after the shared GPU dispatch. No CPU state enters the GPU input.
"""
import copy
from calculator.buff_manager import BuffManager
from calculator.timeline import CharState
from timer_registry_cases import NAMES
import engine_worker


def authored_weapon(char,w):
    weapon=char['_weapon']
    weapon.update(weapon_type='MG' if w.get('mode')=='auto_warmup' else 'AR',damage_coeff=w.get('coefficient',100),
                  max_ammo=w.get('capacity',1),reload_time=w.get('reload',1),core_dmg_mult=w.get('core_mult',200),
                  fire_rate=w.get('rate',1/w.get('interval',1)),fire_rate_max=w.get('rate_max',w.get('rate',1/w.get('interval',1))),
                  pellets=w.get('pellets',1),muzzles=w.get('muzzles',1),full_charge_mult=w.get('full_charge_mult',100))
    return weapon


def authored_weapon_state(char,w,base_atk=1000):
    weapon=char['_weapon']
    st=CharState(char,base_atk,None)
    st.weapon=weapon;st.weapon_type=weapon['weapon_type'];st.base_weapon_type=weapon['weapon_type'];st.base_element_match=w.get('element_match',False)
    st.post_fire_delay=0;st.post_reload_delay=0;st.input_type='DOWN'
    st.charge_time_base=w.get('charge',1);st._min_fire_cycle=w.get('min_cycle',0)
    st.post_fire_delay=w.get('interval',1)-w.get('charge',1) if w.get('mode')=='charge' else 0
    st.cover_during_delay=w.get('cover_during_delay',False)
    st.fire_mode=w.get('mode','auto');st.fire_rate=weapon['fire_rate'];st.fire_rate_max=weapon['fire_rate_max']
    st.warmup_bullets=w.get('warmup',1);st.mech={**st.mech,'cooldown_time':w.get('cooldown_time',1)}
    st.clip_count=w.get('clip_count',1);st.is_clip=st.clip_count>1;st.post_reload_delay=w.get('post_reload_delay',0)
    st.spread_start=w.get('spread_start',1);st.spread_end=w.get('spread_end',1);st._spread_shots_needed=w.get('spread_shots',0)
    st.burst_energy=w.get('gauge',0)
    st.pellets=w.get('pellets',1);st.muzzles=w.get('muzzles',1)
    return st


def observed_next_fire(st,bm):
    """Project native split auto/charge clocks onto the common availability field."""
    mode=bm.get_weapon_change(st.name)
    charge=(mode.get('charge',mode.get('weapon_type','SR') in ('SR','RL'))
            if mode is not None else st.fire_mode=='charge')
    return max(st.next_fire_time,st._post_delay_end_t) if charge else st.next_fire_time


def _observe(case):
    w=case['combat']['weapons'][0]
    if any(x.get('enabled',False) for x in case['combat']['weapons'][1:]):raise ValueError('Oracle fixture needs one enabled shooter')
    names=list(NAMES)
    chars=[dict(name=n,skill_levels={'1':10,'2':10,'3':10},_weapon=copy.deepcopy(engine_worker.META[n])) for n in names]
    weapon=authored_weapon(chars[0],w)
    raw=[(copy.deepcopy(e),names[o]) for e,o in zip(case['effects'],case.get('owners',[0]*len(case['effects'])))]
    class BM(BuffManager):
        def _register_all(self):self._effects=raw;self._build_notify_index()
    bs={n:dict(atk=1000,defense=0,hp=1000000) for n in names}
    enemy=dict(defense=0,core_px=w.get('core_diameter',0),code=None,optimal_range_weapons=[weapon['weapon_type']] if w.get('optimal',False) else [])
    # The engine uses 'def', while the public fixture avoids reserved identifiers.
    enemy['def']=case['combat']['targets'][0].get('defense',0)
    bm=BM(chars,state=dict(base_stats=bs,enemy=enemy,full_burst=False,rng_acc={},rng_expected=True,camera=set()))
    st=authored_weapon_state(chars[0],w)
    total=0;shots=0;gauge=0;queries=[];started=False
    # Canonical charge next means the post-shot availability clock; the native
    # auto-fire clock is unused while charge uses _post_delay_end_t.
    commands=[];next_frame=0;clock=0.0;accumulated=case['combat'].get('clock')=='accumulated'
    for command in case['script']:
        if command[1]==24:
            while next_frame<=10800 and (clock if accumulated else next_frame/60)<=command[0]:
                commands.append([clock if accumulated else next_frame/60,4,0,0,0,-1,0,0]);next_frame+=1
                if accumulated:clock+=1/60
        else:commands.append(command)
    for t,op,event,owner,arg,index,extra,extra2 in commands:
        if op==4:
            if not started:
                for n in names:bm.notify('battle_start',t,n)
                st.ammo=st._full_ammo(bm,t);started=True
            bm.tick(t)
            hits=st.tick(t,bm,enemy,{'rng_mode':'expected'})
            total+=sum(h.damage for h in hits);shots+=int(bool(hits))
            if hits:gauge=min(100,gauge+st._burst_gain(bm.get_buffs(names[0],'__enemy__',t),len(hits),full_charge=st.fire_mode=='charge' and case.get('weapon_reference_context',{}).get('camera',False)))
        elif op==2:queries.append(dict(damage=[total,0,0,0,0],combat={'gauge':gauge,'clock':'accumulated' if accumulated else 'grid','weapons':[dict(ammo=st.ammo,shots=shots,next=observed_next_fire(st,bm),reload_until=st.reloading_until)]}))
        else:raise ValueError('Oracle accepts frame/query fixtures only')
    return queries,dict(warm=st.warmup_shots,last_interval=st._last_inter)


def observe(case):
    # Only static raw weapon metadata is overridden for this regression.
    # Restore it even on a failed assertion; no CPU observation becomes GPU input.
    from calculator import buff_manager
    metadata=buff_manager._NIKKE;saved={n:metadata[n] for n in NAMES}
    try:
        for name,w in zip(NAMES,case['combat']['weapons']):
            replacement=dict(saved[name]);raw=w.get('raw_charge',w.get('charge',1) if w.get('mode')=='charge' else 0)
            if raw:replacement['charge_time']=raw
            else:replacement.pop('charge_time',None)
            metadata[name]=replacement
        return _observe(case)
    finally:
        for name,original in saved.items():metadata[name]=original
