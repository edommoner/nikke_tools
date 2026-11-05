"""Native life-cycle/recipient-order evidence before shared enemy target integration."""
import copy,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
import engine_worker
from calculator.buff_manager import BuffManager
from timer_registry_cases import NAMES

def make(owner,target,stat='taunt'):
 effect=dict(name='target-marker',source='스킬1',type='buff',stat=stat,fixed_value=0,target=target,duration=-1,trigger=dict(timing=['battle_start'],condition=[]))
 class BM(BuffManager):
  def _register_all(self):self._effects=[(copy.deepcopy(effect),NAMES[owner])];self._build_notify_index()
 chars=[dict(name=n,skill_levels={'1':10,'2':10,'3':10},_weapon=engine_worker.META[n]) for n in NAMES]
 state=dict(base_stats={n:dict(atk=1000+100*i,hp=10000,**{'def':0}) for i,n in enumerate(NAMES)},hp={n:10000 for n in NAMES},hp_pct={n:100 for n in NAMES},enemy={'def':0},full_burst=False,rng_acc={})
 bm=BM(chars,state=state)
 for n in NAMES:bm.notify('battle_start',0,n)
 return bm

def snapshot(bm,t):return dict(time=t,taunters=bm.taunters(t),carriers=[dict(name=a.effect['name'],caster=a.caster,targets=a.target_chars) for a in bm._active],down=sorted(bm.state.get('down',())))
