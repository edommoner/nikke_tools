"""Native overlay contracts,including effect lifecycle and full simulation witnesses.
Manual actions below are oracle stimuli,never prepared GPU intermediate inputs.
"""
import copy,hashlib,importlib.util,json,struct,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts'),str(ROOT/'research')]
import engine_worker
from calculator.boss_pattern import BossScript,validate
from calculator.buff_manager import in_optimal_range
from calculator.sim_result import HitEvent
from world_frame_native import observe

def bits(value):return list(struct.unpack('<II',struct.pack('<d',float(value))))
def build(patterns,base=None):
 enemy={'def':7,'core_px':5,'has_parts':False,'optimal_range_weapons':['AR'],'distance':None,**(base or {})}
 return BossScript(validate(copy.deepcopy(patterns),squad_size=5),enemy,lambda caster,code:code in caster.split('|')),enemy

def state(boss,enemy,t):
 events=boss.begin_frame(t,enemy)
 row=dict(time=t,enemy={k:copy.deepcopy(enemy[k]) for k in ('def','core_px','has_parts','optimal_range_weapons','distance')},def_bits=bits(enemy['def']),active=[r.p.id for r in boss._runs if r.active],dispelled=[r.p.id for r in boss._runs if r.dispelled],opened_effects=copy.deepcopy(boss.enemy_effects),released=list(boss.released),events=list(events),vanished=boss.vanished,vanish_return_at=boss.vanish_return_at)
 boss.enemy_effects.clear();boss.released.clear()
 return row

def contracts():
 rows=[]
 def add(name,fn):
  try:actual=fn()
  except Exception as error:rows.append(dict(name=name,passed=False,error=repr(error)))
  else:rows.append(dict(name=name,passed=True,actual=actual))
 def fold(stagger):
  patterns=[dict(id='a',kind='buff',delay=.2 if stagger else 0,enemy=dict(def_mult=2,def_add=1)),dict(id='b',kind='buff',enemy=dict(def_mult=3,def_add=4))]
  b,e=build(patterns);result=[state(b,e,t) for t in (0,.2)]
  assert result[-1]['enemy']['def']==(51 if stagger else 49)
  return result
 add('fold-by-open-time-before-declaration',lambda:fold(True));add('fold-declaration-tie',lambda:fold(False))
 def negative():
  b,e=build([dict(id='a',kind='buff',enemy=dict(def_mult=0,def_add=-10)),dict(id='b',kind='buff',enemy=dict(def_mult=2,def_add=30))],{'def':10});r=state(b,e,0);assert e['def']==10;return r
 add('no-intermediate-defense-clamp',negative)
 def unfused():
  b,e=build([dict(kind='buff',enemy=dict(def_mult=1.0000000000000002,def_add=-9007199254740992))],{'def':9007199254740991});r=state(b,e,0);assert e['def']==0;return r
 add('binary64-multiply-round-before-add',unfused)
 def dispel():
  pats=[dict(id='a',kind='buff',enemy=dict(def_mult=2,received_dmg_pct=-30)),dict(id='b',kind='buff',irremovable=True,enemy=dict(def_add=10,received_dmg_pct=-10)),dict(id='c',kind='buff',delay=.1,enemy=dict(def_mult=3,received_dmg_pct=50))]
  b,e=build(pats,{'def':10});r=[state(b,e,0),state(b,e,.1)]
  assert b.dispel(1,.1)==['c'] and e['def']==90
  r.append(dict(after_dispel_same_frame=copy.deepcopy(e),pending=list(b._dispel_carry)))
  r.append(state(b,e,.2));assert e['def']==30 and r[-1]['released']==['c']
  assert b.dispel(5,.2)==['a'] and e['def']==30
  r.append(state(b,e,.3));assert e['def']==20 and r[-1]['released']==['a']
  assert len(r[0]['opened_effects'])==2 and len(r[1]['opened_effects'])==1
  assert all(x['target']=='self' and x['_boss_bound'] and x['polarity']=='beneficial' for x in r[0]['opened_effects'])
  return r
 add('buff-reverse-dispel-skip-irremovable-next-frame-release',dispel)
 def repeat():
  b,e=build([dict(id='a',kind='buff',after=['start','a'],repeat=0,until={'time':.2},enemy=dict(def_mult=2,received_dmg_pct=-30))],{'def':10});r=[state(b,e,0)]
  assert b.dispel(1,.1)==['a'];r.append(state(b,e,.15));assert e['def']==10
  r.append(state(b,e,.2));assert e['def']==20 and len(r[-1]['opened_effects'])==1 and r[-1]['released']==['a']
  assert not b._runs[0].dispelled;return r
 add('reopen-resets-dispel-release-before-reapply',repeat)
 def core():
  b,e=build([dict(id='a',kind='core',core_px=10,until={'time':.2}),dict(id='b',kind='core',core_px=20,delay=.1,until={'time':.2})]);r=[state(b,e,t) for t in (0,.1,.2,.31)]
  assert [x['enemy']['core_px'] for x in r]==[10,20,20,5];return r
 add('core-maximum-and-base-restoration',core)
 def move(distance):
  a={'distance':20} if distance else {'weapons':['SR']};z={'distance':70} if distance else {'weapons':['SMG']};base={'optimal_range_weapons':[],'distance':40} if distance else {}
  b,e=build([dict(id='a',kind='move',until={'time':.2},**a),dict(id='b',kind='move',delay=.1,until={'time':.2},**z)],base);r=[state(b,e,t) for t in (0,.1,.2,.31)]
  assert [x['enemy']['distance' if distance else 'optimal_range_weapons'] for x in r]==([20,70,70,40] if distance else [['SR'],['SMG'],['SMG'],['AR']]);return r
 add('move-latest-open-distance-restore',lambda:move(True));add('move-latest-open-weapons-restore',lambda:move(False))
 def gates():
  b,e=build([dict(id='v',kind='vanish',until={'time':.2}),dict(id='a',kind='shield',code='수냉'),dict(id='b',kind='shield',code='풍압')]);r=[state(b,e,0)]
  gate=lambda caster,tag,name:b.gate(HitEvent(0,caster,100,False,tag,skill_name=name))
  assert not gate('수냉|풍압','pellet:1','기본 공격')
  assert not gate('풍압','normal','named-mode-skill')
  assert not gate('수냉','dot_damage','dot')
  assert gate('수냉|풍압','bonus_damage','skill')
  blocked={x.p.id:x.blocked for x in b._runs};assert blocked=={'v':100,'a':100,'b':100}
  r.append(dict(blocked=blocked));r.append(state(b,e,.2));assert gate('수냉|풍압','normal','기본 공격');return r
 add('vanish-normal-before-shields-first-blocker-accounting',gates)
 def vanish_return():
  b,e=build([dict(id='a',kind='vanish',until={'time':.2}),dict(id='b',kind='vanish',until={'time':.3})]);r=state(b,e,0);assert r['vanish_return_at']==.3
  b2,e2=build([dict(id='a',kind='vanish',until={'after':[{'node':'b'}]}),dict(id='b',kind='idle',until={'time':.2})]);r2=state(b2,e2,0);assert r2['vanish_return_at'] is None;return [r,r2]
 add('vanish-return-known-only-all-fixed',vanish_return)
 def epsilon():
  b,e=build([dict(id='a',kind='buff',delay=.1,until={'time':.2},enemy=dict(def_mult=2))]);r=[state(b,e,t) for t in (0,.1-2e-9,.1-.5e-9)]
  assert [x['enemy']['def'] for x in r]==[7,7,14];return r
 add('overlay-opening-eps-boundary',epsilon)
 def ranges():
  rows=[]
  for distance,expect in [(10-2e-9,False),(10-.5e-9,True),(20+.5e-9,True),(20+2e-9,False)]:
   from calculator import buff_manager
   from unittest.mock import patch
   with patch.dict(buff_manager._NIKKE,{'overlay-probe':dict(weapon_type='AR',optimal_range=[10,20])}):actual=in_optimal_range({'distance':distance},'overlay-probe','AR',{})
   assert actual==expect;rows.append(dict(distance=distance,expected=expect,actual=actual))
  return rows
 add('range-closed-with-binary64-eps',ranges)
 def mixed():
  rejects=[]
  for patterns,base in [([dict(kind='move',distance=20),dict(kind='move',weapons=['AR'])],{}),([dict(kind='move',distance=20)],{'optimal_range_weapons':['AR']}),([dict(kind='move',weapons=['AR'])],{'distance':20})]:
   try:build(patterns,base)
   except ValueError as error:rejects.append(str(error))
   else:raise AssertionError('mixed move mode admitted')
  return rejects
 add('reject-mixed-range-domains',mixed)
 return rows

def full_simulations():
 spec=importlib.util.spec_from_file_location('overlay_frame_fixtures',ROOT/'research/verify-world-frame.py');f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)
 base=copy.deepcopy(f.fixtures()[0]);base.update(duration=.5,patterns=[dict(id='base',kind='idle')],enemy={'def':100,'core_px':0},weapon_metadata=dict(spread_start=20,spread_end=10,spread_change_pershot=2,optimal_range=[10,20]));base['combat']['weapons']=[dict(enabled=True,stage=0,gauge=0,capacity=1000,interval=.1,reload=1) for _ in range(5)]
 profiles=[('base',[]),('defense',[dict(id='armor',kind='buff',enemy=dict(def_mult=2,def_add=10),until={'time':.2})]),('received',[dict(id='received',kind='buff',enemy=dict(received_dmg_pct=-30),until={'time':.2})]),('core',[dict(id='core',kind='core',core_px=52,until={'time':.2})]),('range',[dict(id='range',kind='move',weapons=['AR'],until={'time':.2})]),('vanish',[dict(id='vanish',kind='vanish',until={'time':.2})]),('shield',[dict(id='shield',kind='shield',code='수냉',until={'time':.2})])]
 rows=[]
 for name,patterns in profiles:
  case=copy.deepcopy(base);case['name']='native-overlay-'+name;case['patterns']+=patterns
  try:result=observe(case)
  except Exception as error:rows.append(dict(name=case['name'],passed=False,error=repr(error),case=case))
  else:rows.append(dict(name=case['name'],passed=True,case=case,actual=result))
 debug=ROOT/'research/portable-build/overlay-native-full-before-assert.json';debug.parent.mkdir(parents=True,exist_ok=True)
 debug.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
 if all(r['passed'] for r in rows):
  original=rows[0]['actual']['damage']
  assert all(a<b for a,b in zip(rows[1]['actual']['damage'],original))
  assert all(a<b for a,b in zip(rows[2]['actual']['damage'],original))
  assert all(a>b for a,b in zip(rows[3]['actual']['damage'],original))
  assert all(a>b for a,b in zip(rows[4]['actual']['damage'],original))
  assert all(a<b for a,b in zip(rows[5]['actual']['damage'],original))
 return rows

def main():
 rows=contracts();full=full_simulations();paths=['research/characterize-world-overlays.py','research/world_frame_native.py','app/world_frame_runtime.py','research/upstream/nikke-calc-master/calculator/boss_pattern.py','research/upstream/nikke-calc-master/calculator/timeline.py','research/upstream/nikke-calc-master/calculator/buff_manager.py']
 report=dict(passed=all(x['passed'] for x in rows+full),source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths},contracts=rows,full_native_profiles=full,gpu_executions=0,gpu_overlay_verified=False,canonical_world_admission=False,full_character_verified=0,full_goal_complete=False,scope='Native scheduler/lifecycle contracts plus seven actual full simulations. No generated CPU state is used as GPU input;no GPU overlay or full-character support claim.')
 out=ROOT/'research/portable-world-overlay-native.json';out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');assert report['passed'],[(r['name'],r.get('error')) for r in rows+full if not r['passed']]
 print(len(rows),'native overlay contracts and',len(full),'full simulate profiles passed')
if __name__=='__main__':main()
