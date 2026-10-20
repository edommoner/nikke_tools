"""Observe native late-pass attack arithmetic and independent rank semantics;CPU only."""
import copy,hashlib,itertools,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
import engine_worker
from calculator.buff_manager import BuffManager
from timer_registry_cases import NAMES

def main():
 rows=[]
 for owner in range(5):
  for order in itertools.permutations(('hp-positive','hp-negative','caster')):
   for target in ('self','all_allies'):
    specs={'hp-positive':('atk_from_hp_pct',1e14),'hp-negative':('atk_from_hp_pct',-1e14),'caster':('atk_caster_based_pct',.1)}
    effects=[dict(name=kind,source='스킬1',type='buff',stat=specs[kind][0],fixed_value=specs[kind][1],target=target,duration=1,trigger=dict(timing=['battle_start'],condition=[])) for kind in order]
    class BM(BuffManager):
     def _register_all(self):
      self._effects=[(copy.deepcopy(e),NAMES[owner]) for e in effects];self._build_notify_index()
    chars=[dict(name=n,skill_levels={'1':10,'2':10,'3':10},_weapon=engine_worker.META[n]) for n in NAMES]
    bm=BM(chars,state=dict(base_stats={n:dict(atk=1000,hp=10000,**{'def':100}) for n in NAMES},hp={n:10000 for n in NAMES},hp_pct={n:100 for n in NAMES},enemy={'def':0,'core_px':0},full_burst=False,rng_acc={}))
    bm.notify('battle_start',0,NAMES[owner]);observations=[]
    for phase,t in [('initial',0),('expired',1)]:
     bm.tick(t)
     expected=[1.0 if phase=='initial' and (target=='all_allies' or i==owner) else 0.0 for i in range(5)]
     actual=[bm.get_buffs(n,'__enemy__',t).get('atk_flat',0) for n in NAMES]
     assert actual==expected,(owner,order,target,phase,actual,expected)
     rank=[bm._effective_atk(n) for n in NAMES]
     if phase=='initial':assert rank[owner]==1001.0 and bm.final_atk(NAMES[owner],t)==1001.0
     observations.append(dict(phase=phase,actual_flat=actual,expected_flat=expected,native_rank_attack=rank))
    rows.append(dict(owner=owner,registration_order=order,target=target,observations=observations))
 report=dict(passed=True,cpu_only=True,gpu_admission_enabled=False,gpu_execution_performed=False,cases=rows,
   arithmetic='HP+1e16 andHP-1e16 cancel before caster1 for every registration permutation;interleaving caster between HP terms would yield0',
   ranking='Native _effective_atk does not include HP-derived attack;do not silently use damage final_atk for ranking',
   source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ['research/characterize-atk-from-hp-order.py','research/upstream/nikke-calc-master/calculator/buff_manager.py']})
 (ROOT/'research/portable-atk-from-hp-order-native.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 print(len(rows),'native ordered/ranking cases passed')
if __name__=='__main__':main()
