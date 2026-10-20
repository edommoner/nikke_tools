"""Real Heavyarms identity with authored mechanics;no prepared battle states."""
import copy,importlib.util,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];HEAVY='스노우 화이트 : 헤비암즈'
def fixtures():
 s=importlib.util.spec_from_file_location('hold_gates',ROOT/'research/world_overlay_gate_cases.py');g=importlib.util.module_from_spec(s);s.loader.exec_module(g)
 base=copy.deepcopy(next(c for c in g.fixtures() if c['name']=='vanish-charge-camera'));base['names']=[HEAVY,*base['camera'][1:]];base['camera']=list(base['names']);base['observe_charge_hold']=True;rows=[]
 def add(name,patterns,duration=.3):
  c=copy.deepcopy(base);c.update(name='charge-hold-'+name,patterns=patterns,duration=duration);rows.append(c);return c
 def v(time=None,**kw):return dict(id='v',kind='vanish',**(dict(until={'time':time}) if time else {}),**kw)
 add('no-vanish',[dict(id='open',kind='idle')],1)
 for end in (.1,.2,.25,1,2.19,2.2,2.3,3):add('fixed-'+str(end),[v(end)])
 ready=0.
 while ready<.2:ready+=1/60
 boundary=ready+2
 for end in (math.nextafter(boundary,-math.inf),boundary,math.nextafter(boundary,math.inf)):add('remaining-two-boundary-'+repr(end),[v(end)])
 add('fixed-release',[v(.5)],1.2)
 add('unknown-holds',[v()])
 add('unknown-max-two-seconds',[v()],2.6)
 add('unknown-until-after',[v(until={'after':[dict(node='timer')]}),dict(id='timer',kind='idle',until={'time':.5})],1)
 add('multiple-fixed-latest',[v(.25),dict(id='later',kind='vanish',until={'time':.5})],1)
 add('mixed-unknown-and-long-fixed',[v(3),dict(id='unknown',kind='vanish',until={'after':[dict(node='timer')]}),dict(id='timer',kind='idle',until={'time':.5})],1)
 add('delayed-vanish',[v(.5,delay=.3)],1.3)
 add('repeat-generation',[v(.25,after=['start','v'],repeat=0)],1.2)
 c=add('unobserved',[v(.5)],1);c['camera']=[];c['camera_mode']='single'
 for w in c['combat']['weapons']:w['gauge_mult']=100
 c=add('full-latch-survives-speed-expiry',[v(.15)],.18);c['effects']=[dict(name='temporary-charge-speed',source='스킬1',type='buff',stat='charge_speed_pct',fixed_value=100,target='self',duration=.12,trigger=dict(timing=['battle_start'],condition=[]))];c['owners']=[0]
 c=add('weapon-switch-while-holding',[v()],1);c['effects']=[dict(name='temporary-mode',source='스킬1',type='weapon_change',weapon_type='AR',damage_coeff=100,max_ammo=-1,fire_rate=10,fire_rate_max=10,charge=False,pellets=1,muzzles=1,post_fire_delay=0,burst_energy=.25,core_dmg_mult=200,target='self',duration=.2,max_trigger=1,trigger=dict(timing=['every:0.3s'],condition=[]))];c['owners']=[0]
 c=add('regular-character-does-not-hold',[v(.5)]);c['names']=['리타',*c['names'][1:]];c['camera']=list(c['names'])
 return rows
