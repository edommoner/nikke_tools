"""Authored duration rules. Native CPU checks validate, never generate expectations."""
import copy,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def effect(name,value=10,target='self',duration=.5,owner=0):return dict(name=name,source='스킬1',type='buff',stat='atk_pct',fixed_value=value,target=target,duration=duration,trigger=dict(timing=['battle_start'],condition=[]))
def extension(prefix='State',target='self',value=.5):return dict(name='Extend',source='스킬1',type='instant',stat='named_buff_duration_extend',fixed_value=value,target_effect=prefix,target=target,trigger=dict(timing=['on_attack'],condition=[]))
def command(t,op,event=0,who=0,arg=None,index=None):return [t,op,event,who,(-1 if op==2 else 0) if arg is None else arg,(0 if op==2 else -1) if index is None else index,0,0]
def make(name,effects,owners,script,expected,targets=None):
 return dict(name='duration-extend-'+name,effects=effects,owners=owners,combat=dict(weapons=[dict(enabled=False)]*5,targets=targets or [dict(hp=1e30)]),environment=dict(allies=[dict(base_hp=1000,hp=500)]*5),script=script,expected_queries=expected,duration_extend_reference=True)
def attack(*values):return dict(attack_buffs=list(values or [10,0,0,0,0]))
start=command(0,4);cast=command(.25,0,7);query=command(.6,2);frame=command(.6,4)
cases=[]
cases.append(make('exact-space-prefix',[effect('State'),effect('State 2',20),effect('Stateful',30),extension()], [0]*4,[start,cast,frame,query],[attack(30,0,0,0,0)]))
cases.append(make('shared-instance-whole-expiry',[effect('State',target='all_allies'),extension()], [0,0],[start,cast,frame,query],[attack(10,10,10,10,10)]))
cases.append(make('cross-caster',[effect('State'),effect('State',20),extension(target='all_allies')],[0,1,4],[start,command(.25,0,7,4),frame,query],[attack(10,20,0,0,0)]))
for prefix in ('','Absent'):
 cases.append(make('empty-prefix' if not prefix else 'missing-name',[effect('State'),extension(prefix=prefix)],[0,0],[start,cast,frame,query],[attack(0,0,0,0,0)]))
cases.append(make('empty-target',[effect('State'),extension(target='allies:0')],[0,0],[start,cast,frame,query],[attack(0,0,0,0,0)]))
c=make('rank-at-activation',[effect('State'),effect('State',20),extension(target='allies_top_atk:1')],[0,1,0],[start,cast,frame,query],[attack(0,20,0,0,0)]);c['base_atk']=[1000,2000,1000,1000,1000];cases.append(c)
cases.append(make('with-buff-selector',[effect('State'),effect('State',20),effect('Marker',0,duration=3),extension(target='allies_with_buff:Marker')],[0,2,2,0],[start,cast,frame,query],[attack(0,0,20,0,0)]))
for resolved in (False,True):
 script=[start]+([command(.1,2)] if resolved else [])+[cast,frame,command(.6,2,index=int(resolved))]
 c=make('lazy-resolved' if resolved else 'lazy-unresolved',[effect('State',target='allies_lowest_hp:1'),extension(target='all_allies')],[0,0],script,([attack()] if resolved else [])+[attack(10 if resolved else 0,0,0,0,0)])
 if not resolved:c['effects'][0].update(stat='invincible',fixed_value=1)
 cases.append(c)
cases.append(make('infinite-unchanged',[effect('State',duration=-1),extension(value=-.5)],[0,0],[start,cast,command(2,4),command(2,2)],[attack()]))
cases.append(make('finite-one-e30-is-not-infinity',[effect('State',duration=1e30),extension(value=1e30)],[0,0],[start,cast,query],[attack()]))
cases.append(make('zero-does-not-refresh',[effect('State'),extension(value=0)],[0,0],[start,cast,frame,query],[attack(0,0,0,0,0)]))
ended=effect('Ended',1,duration=-1);ended.update(max_stack=99,trigger=dict(timing=['event:state_end:State'],condition=[]))
cases.append(make('negative-retires-on-next-frame',[effect('State'),extension(value=-.4),ended],[0,0,0],[start,cast,command(.25,2),command(.3,4),command(.3,2,index=1)],[attack(0,0,0,0,0),attack(1,0,0,0,0)]))
cases.append(make('expired-unretired-can-revive',[effect('State',duration=.2),extension()],[0,0],[start,command(.3,0,7),command(.35,2),command(.9,4),command(.9,2,index=1)],[attack(),attack(0,0,0,0,0)]))
clock=effect('State',duration=.5);clock.update(type='instant',stat='heal_hp_pct',tick_interval=.25)
cases.append(make('instant-clock-has-no-resident',[clock,extension(value=1)],[0,0],[start,command(.2,0,7),command(.3,4),command(.3,2),command(.6,4),command(.6,2,index=1)],[dict(allies=[dict(hp=600)]),dict(allies=[dict(hp=600)])]))
targets=[dict(hp=1e30)]+[dict(kind=5,identity=i,hp=1e12) for i in range(2)]
for target in ('boss','all_enemies','enemies_lowest_hp:1'):
 state=effect('State',-20,target='all_enemies');state['stat']='def_pct'
 script=[start,cast,frame,command(.6,2,arg=0),command(.6,2,arg=1,index=1),command(.6,2,arg=2,index=2)]
 expected=[dict(enemy_modifiers=dict(defense_pct=(-20 if (target=='all_enemies' or target=='boss' and i==0 or target=='enemies_lowest_hp:1' and i==1) else 0))) for i in range(3)]
 cases.append(make('enemy-independent-'+target.replace(':','-'),[state,extension(target=target),copy.deepcopy(ended)],[0,0,0],script,expected,targets))
state=effect('State',-20,target='all_enemies');state['stat']='def_pct'
# Reapply after only two recipients expired; the surviving body refreshes once.
state['trigger']['timing'].append('hit_count:1')
cases.append(make('enemy-reapply-after-partial-expiry',[state,extension(target='boss')],[0,0],[start,cast,frame,command(.65,0,8),command(.7,2,arg=0),command(.7,2,arg=1,index=1)],[dict(enemy_modifiers=dict(defense_pct=-20)),dict(enemy_modifiers=dict(defense_pct=-20))],targets))
# A DoT remains one native resident holding all retained targets.
no_crit=effect('no critical',-15,target='all_allies',duration=-1);no_crit['stat']='crit_rate'
dot=dict(name='State',source='스킬1',type='damage',stat='dot_damage',fixed_value=100,target='all_enemies',duration=.5,tick_interval=.25,trigger=dict(timing=['battle_start'],condition=[]))
cases.append(make('retained-dot-whole-clock',[no_crit,dot,extension(target='boss')],[0,0,0],[start,command(.1,0,7),command(.3,4),command(.3,2),command(.6,4),command(.6,2,index=1)],[dict(damage=[3000,0,0,0,0]),dict(damage=[6000,0,0,0,0])],targets))
# Names bind logical actors, so a new generation must not inherit the old expiry.
state=effect('State',-20,target='all_enemies',duration=1);state['stat']='def_pct'
cases.append(make('enemy-new-life-does-not-extend-old-carrier',[state,extension(target='all_enemies')],[0,0],[start,command(.1,22,arg=1),[.2,21,0,0,1,-1,1e12,0],command(.25,0,7),command(.3,2,arg=1)],[dict(enemy_modifiers=dict(defense_pct=0))],targets))
listener=effect('Listener',1,duration=-1);listener.update(max_stack=99,trigger=dict(timing=['event:State'],condition=[]))
cases.append(make('enemy-notice-once-per-cell',[copy.deepcopy(state),copy.deepcopy(listener)],[0,0],[start,command(.1,2)],[attack(3,0,0,0,0)],targets))
remove=dict(name='Remove',source='스킬1',type='instant',stat='remove_named_buff',fixed_value=0,target='self',target_effect='State',trigger=dict(timing=['event:State'],condition=[]))
cases.append(make('enemy-child-removes-before-next-receiver',[copy.deepcopy(state),remove,copy.deepcopy(ended)],[0,0,0],[start,command(.1,2)],[attack(3,0,0,0,0)],targets))
# Query-driven maximum-HP and duration expiry use the original native cache path.
hp=effect('State',20,target='all_allies');hp['stat']='max_hp_pct'
cases.append(make('shared-max-hp-expiry',[hp,extension()],[0,0],[start,cast,frame,query],[dict(allies=[dict(max_hp=1200)]*5)]))
# Integer/binary64 additions retain fractions, signed zero and accumulated expiry.
cases.append(make('fractional-repeated',[effect('State',duration=.5),extension(value=.125)],[0,0],[start,command(.1,0,7),command(.2,0,7),command(.6,4),command(.6,2)],[attack()]))
periodic=extension(value=.25);periodic.update(tick_interval=.25,duration=1,trigger=dict(timing=['battle_start'],condition=[]))
cases.append(make('periodic-does-not-reset-state-phase',[effect('State',duration=.3),periodic],[0,0],[start,command(.25,4),command(.5,4),command(.75,4),command(1.04,2),command(1.1,4),command(1.1,2,index=1)],[attack(),attack(0,0,0,0,0)]))
limited=extension();limited['max_trigger']=1
cases.append(make('activation-budget-once',[effect('State'),limited],[0,0],[start,command(.1,0,7),command(.2,0,7),command(1.1,4),command(1.1,2)],[attack(0,0,0,0,0)]))
# Empty target at the first attempt must not charge a finite activation budget.
limited=extension(target='allies_with_buff:Marker');limited['max_trigger']=1
marker=effect('Marker',0,duration=2);marker['trigger']['timing']=['hit_count:1']
cases.append(make('empty-target-preserves-budget',[effect('State'),limited,marker],[0,0,0],[start,command(.1,0,7),command(.2,0,8),command(.3,0,7),frame,query],[attack()]))
for when in (.5,1.1):
 staged=copy.deepcopy(json.loads((R/'tests/fixtures/portable-staged.json').read_text())['cases'][0])
 ext=extension(prefix='dot',target='boss');ext['trigger']['timing']=['hit_count:1']
 staged['effects'].append(ext);staged['owners']=[0]*4
 script=[start,command(.1,0,7)];expected=[];index=0
 for t,total in [(.35,1000),(.6,3000),(.85,6000),(1.35,9000),(2.35,12000)]:
  if script[-1][0]<when<t:script.append(command(when,0,8))
  script.extend([command(t,4),command(t,2,index=index)]);index+=1;expected.append(dict(damage=[total,0,0,0,0]))
 staged.update(name='duration-extend-staged-before-ramp-end' if when==.5 else 'duration-extend-staged-after-ramp-end',script=script,expected_queries=expected,duration_extend_reference=True)
 cases.append(staged)
for initial,refresh,label,delta in [(-1,.5,'infinite-definition-refreshed-finite',.5),(.5,-1,'finite-definition-refreshed-infinite',1e30)]:
 a=effect('State',duration=initial);b=effect('State',duration=refresh);b['trigger']['timing']=['hit_count:1']
 cases.append(make(label,[a,b,extension(value=delta)],[0,0,0],[start,command(.1,0,8),cast,frame,query],[attack()]))
for delta,label in [(1e308,'positive-overflow-is-infinite'),(-1e308,'negative-overflow-expires')]:
 cases.append(make(label,[effect('State'),extension(value=delta)],[0,0],[start,command(.1,0,7),command(.2,0,7),command(.25,2)],[attack(10 if delta>0 else 0,0,0,0,0)]))
periodic_limited=copy.deepcopy(periodic);periodic_limited['max_trigger']=1
cases.append(make('periodic-one-registration-budget',[effect('State',duration=.3),periodic_limited],[0,0],[start,command(.25,4),command(.5,4),command(.75,4),command(1.04,2)],[attack()]))
plus=extension(value=1e308);minus=extension(value=-1e308);minus.update(name='Minus',trigger=dict(timing=['hit_count:1'],condition=[]))
cases.append(make('overflow-infinity-is-not-a-large-finite-number',[effect('State'),plus,minus],[0,0,0],[start,command(.1,0,7),command(.2,0,7),command(.3,0,8),command(.35,2)],[attack()]))
state=effect('State',-20,target='all_enemies');state['stat']='def_pct'
inherited=extension(target='target');inherited['trigger']['timing']=['hit_count:1']
cases.append(make('inherited-enemy-target',[state,inherited],[0,0],[start,command(.1,20,arg=2),command(.25,0,8),frame,command(.6,2,arg=0),command(.6,2,arg=2,index=1)],[dict(enemy_modifiers=dict(defense_pct=0)),dict(enemy_modifiers=dict(defense_pct=-20))],targets))
fillers=[effect('Filler'+str(i),0,duration=.01) for i in range(254)]
cases.append(make('definition-255-mask-boundary',[extension()]+fillers+[effect('State')],[0]*256,[start,cast,frame,query],[attack()]))
(R/'tests/fixtures/portable-duration-extend.json').write_text(json.dumps(dict(cases=cases),ensure_ascii=False,indent=2)+'\n')
print('Authored duration cases',len(cases))
