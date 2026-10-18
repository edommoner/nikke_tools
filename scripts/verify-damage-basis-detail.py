"""Shared HP basis, exclusive ammo and live activation-predicate witnesses."""
import argparse,copy,hashlib,importlib.util,json,sys
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from detail_coverage import a,body_for
import detail_gpu as g
from gpu_selector import Cuda
from calculator.buff_manager import BuffManager
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,ROOT/path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
p=load('basis_periodic','scripts/verify-periodic-detail.py')
incoming=load('basis_incoming','scripts/verify-incoming-detail.py')
primitive=load('basis_primitive','scripts/verify-detail.py')
E=p.effect;N=p.NAMES

def quantities(device,backend):
 rows=[];stats={n:dict(atk=1000,hp=10000,def_=100) for n in N}
 for value in stats.values():value['def']=value.pop('def_')
 for mode,hp_boost,expected in ((None,0,1500),('max_hp_additive',0,2500),('max_hp_additive',100,3500),('max_hp_replacement',0,400),('max_hp_replacement',100,900)):
  effects=[E('ATK percent','buff','atk_pct',50),E('caster-based flat ATK','buff','atk_caster_based_pct',10),E('no crit','buff','crit_rate',-15)]
  if hp_boost:effects.append(E('maximum only','buff','max_hp_only_pct',hp_boost))
  effects.append(E('current HP is not the basis','instant','current_hp_reduce',50))
  attack=E('test hit','damage','damage',100,'target',event='on_attack')
  if mode:attack.update(scaling=mode,scaling_hp_pct=10 if mode=='max_hp_additive' else 5)
  effects.append(attack);chars=primitive.characters(N);program=g.compile_effects(chars,[(e,N[0]) for e in effects])
  result=g.run(device,[program],[[0,0,0,0,0,-1,0,0],[.1,0,7,0,0,-1,0,0],[.1,2,101,0,0,0,0,0]],[[100,0]],[stats],module_backend=backend)
  actual=result['totals'][0][0];assert actual==expected,(mode,hp_boost,actual,expected)
  rows.append(dict(name=f'quantity-{mode}-{hp_boost}',passed=True,expected=expected,actual=actual))
 # Percent reductions are compared as groups before rounding each survivor.
 for name,parts,expected_pct,expected_clip in (
  ('ordinary-addition',[(-49,False,None,None),(-51,False,None,None),(20,False,None,None)],-80,1),
  ('strongest-before-rounding',[(-49,True,None,None),(-51,False,None,None),(20,False,None,None)],-31,2),
  ('equal-reductions-once',[(-51,True,None,None),(-51,False,None,None),(20,False,None,None)],-31,2),
  ('compare-group-sums',[(-30,False,'group',None),(-30,False,'group',None),(-51,True,None,None),(20,False,None,None)],-40,2),
  ('expired-exclusive',[(-70,True,None,.05),(-49,False,None,None),(-51,False,None,None),(20,False,None,None)],-80,1),
  ('positive-flag-does-not-suppress',[(-49,False,None,None),(-51,False,None,None),(20,True,None,None)],-80,1)):
  effects=[]
  for i,(value,exclusive,group,duration) in enumerate(parts):
   e=E('ammo'+str(i),'buff','max_ammo_pct',value,max_ammo_reduction_exclusive=exclusive)
   if group:e['_quant_group']=group
   if duration:e['duration']=duration
   effects.append(e)
  chars=primitive.characters(N);chars[0]['_weapon']=copy.deepcopy(chars[0]['_weapon']);chars[0]['_weapon']['max_ammo']=3
  program=g.compile_effects(chars,[(e,N[0]) for e in effects])
  result=g.run(device,[program],[[0,0,0,0,0,-1,0,0],[.1,3,0,0,0,-1,0,0],[.1,2,0,0,-1,0,0,0]],[[100,0]],[stats],module_backend=backend)
  actual=result['queries'][0][0];assert actual[18]==expected_pct and actual[44]==expected_clip-1,(name,actual[18],actual[44],expected_pct,expected_clip)
  rows.append(dict(name=name,passed=True,expected_pct=expected_pct,expected_clip=expected_clip,actual_pct=actual[18],ammo_after_one_shot=actual[44]))
 # A borrowed marker with a different name, lazy target and exact expiry.
 effects=[(E('foreign name','buff','undying',0,'allies_lowest_hp_excl:1',duration=.2),N[1]),(E('witness','buff','atk_pct',10,event='on_attack',condition=['self_undying'],duration=.1),N[0])]
 result=g.run(device,[g.compile_effects(primitive.characters(N),effects)],[[0,0,0,1,0,-1,0,0],[.1,0,7,0,0,-1,0,0],[.1,2,103,0,0,0,0,0],[.3,0,7,0,0,-1,0,0],[.3,2,103,0,0,1,0,0]],[[100,0]],[stats],module_backend=backend)
 values=[q[0] for q in result['queries'][0]];assert values==[10,0],values
 rows.append(dict(name='borrowed-lazy-undying-then-expiry',passed=True,expected=[10,0],actual=values))
 return rows

def real_fixtures():
 for name in ('메이든 : 아이스 로즈','킬로','K','마키마','릴리'):
  names=[name]+['리타','크라운','앨리스','모더니아'];b=body_for(names,60,True)
  if name=='K':names=[name,'리타','크라운','프리바티','모더니아'];b=body_for(names,60,True)
  b.update(seed=12345,shooting_policy='character',burst_gauge_mode='fixed',_debug_random_state=True,_debug_boss_random_state=True,_debug_incoming_frames=True)
  if name=='마키마':b['enemy']['patterns']=[dict(id='undying-gate',kind='attack',delay=.1,until={'time':.7},spec=dict(coeff=100,atk=100000000,target='slot:1',hits=1,interval=.3,pierce=True))]
  if name=='릴리':b['enemy']['patterns']=[dict(id='cover-gate',kind='attack',delay=.1,until={'time':.7},spec=dict(coeff=100,atk=4000000,target='slot:2',hits=1,interval=.3))]
  extra={'리타':[E('cover test stimulus','instant','force_reload',0)]} if name=='릴리' else {}
  yield name,b,extra

@contextmanager
def observations(owner):
 observed=[];activate=BuffManager._activate;register=BuffManager.register_damage_handler
 def activated(manager,eff,caster,t,*args,**kwargs):
  cover_before=dict(manager.state.get('cover_hp',{}))
  result=activate(manager,eff,caster,t,*args,**kwargs)
  interesting=eff.get('max_ammo_reduction_exclusive') or any(c in eff.get('trigger',{}).get('condition',[]) for c in ('self_undying','no_broken_cover_ally')) or owner=='릴리' and eff.get('target','').startswith('allies_broken_cover')
  if caster==owner and interesting:
   carriers=[ab for ab in manager._active if ab.effect is eff and ab.caster==caster and t<ab.expires_at]
   live=any(ab.target_chars!=[] for ab in carriers)
   observed.append(dict(name=eff.get('name'),time=t,active=live,stat=eff.get('stat'),conditions=eff.get('trigger',{}).get('condition',[]),targets=[ab.target_chars for ab in carriers],cover_before=cover_before,cover_after=dict(manager.state.get('cover_hp',{}))))
  return result
 def registered(manager,handler):
  def damage(eff,caster,t):
   if caster==owner and eff.get('scaling') in ('max_hp_additive','max_hp_replacement'):observed.append(dict(name=eff.get('name'),time=t,active=True,max_hp=manager.effective_max_hp(caster)))
   return handler(eff,caster,t)
  return register(manager,damage)
 with patch.object(BuffManager,'_activate',activated),patch.object(BuffManager,'register_damage_handler',registered):yield observed

def real_cases(device,backend,cpu_only=False):
 rows=[]
 for owner,body,extra in real_fixtures():
  name='raw-basis-'+owner+('' if body['enemy'].get('patterns') else '-no-shots')
  with observations(owner) as observed:
   if cpu_only:
    with incoming.context(name,extra):result=a.evaluate(body)
    row=dict(name=name,passed=True,cpu_total=result['total_damage'])
   elif any(p.get('kind')=='attack' for p in body.get('enemy',{}).get('patterns',[])):row=incoming.compare(device,name,body,extra,backend)
   else:
    with incoming.context(name,extra):row=p.full.compare(device,name,body,module_backend=backend)
    row['raw_skills_retained']=True
  row['observations']=observed;row['passed']=row['passed'] and any(e['active'] for e in observed)
  if owner=='릴리':
   restored=any(e.get('stat')=='cover_revive' and any(hp<=0 and e['cover_after'].get(n,0)>0 for n,hp in e['cover_before'].items()) for e in observed)
   row['cover_both_branches_exercised']=restored and any('no_broken_cover_ally' in e.get('conditions',[]) and e['active'] for e in observed)
   row['passed']&=row['cover_both_branches_exercised']
  rows.append(row);print(json.dumps(dict(name=name,passed=row['passed'],observations=observed),ensure_ascii=True),flush=True)
 return rows

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--backend',choices=('native','ptx'),default='native');ap.add_argument('--cpu-preflight',action='store_true');args=ap.parse_args()
 files=sorted({str(p.relative_to(ROOT)).replace('\\','/') for p in (ROOT/'app').glob('*.py')}|{'app/detail_effects.cu','scripts/verify-damage-basis-detail.py','scripts/verify-incoming-detail.py','scripts/verify-detail.py','scripts/verify-periodic-detail.py','scripts/verify-extended-detail.py'})
 if not args.cpu_preflight:files+=['app/detail_effects-sm86.cubin','app/detail_effects-sm86.json'] if args.backend=='native' else ['app/detail_effects.ptx','app/detail_effects-build.json']
 def hashes():return {p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files}
 before=hashes();device=None if args.cpu_preflight else Cuda()
 try:rows=real_cases(None,args.backend,True) if args.cpu_preflight else quantities(device,args.backend)+real_cases(device,args.backend)
 finally:
  if device:device.close()
 assert hashes()==before
 report=dict(passed=all(r['passed'] for r in rows),cases=rows,source_stable=True,source_sha256=before,cpu_trace_used_as_gpu_input=False)
 suffix='cpu-preflight' if args.cpu_preflight else args.backend
 (ROOT/f'research/damage-basis-{suffix}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 raise SystemExit(0 if report['passed'] else 1)
if __name__=='__main__':main()
