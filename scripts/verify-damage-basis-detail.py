"""Shared HP basis, exclusive ammo and live activation-predicate witnesses."""
import argparse,copy,hashlib,importlib.util,json,sys
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from detail_coverage import a,body_for
import detail_gpu as g
from calculator.buff_manager import BuffManager
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,ROOT/path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
p=load('basis_periodic','scripts/verify-periodic-detail.py')
incoming=load('basis_incoming','scripts/verify-incoming-detail.py')
primitive=load('basis_primitive','scripts/verify-detail.py')
E=p.effect;N=p.NAMES


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


if __name__=='__main__':main()
