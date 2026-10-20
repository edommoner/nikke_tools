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
def main():
 rows=[]
 for owner in range(5):
  bm=make(owner,'allies_top_atk_excl:1');initial=snapshot(bm,0);assert initial['taunters']==[] and initial['carriers'][0]['targets'] is None
  winner=4 if owner!=4 else 3;assert bm.has_live_stat(NAMES[winner],'taunt',.1)
  resolved=snapshot(bm,.1);assert resolved['taunters']==[NAMES[winner]]
  bm.knock_down(NAMES[winner],.2);down=snapshot(bm,.2);assert down['taunters']==[]
  bm.revive(NAMES[winner],.3,100);revived=snapshot(bm,.3);assert revived['taunters']==[] and revived['carriers'][0]['targets'] is None
  assert bm.has_live_stat(NAMES[winner],'taunt',.4);queried=snapshot(bm,.4);assert queried['taunters']==[NAMES[winner]]
  rows.append(dict(owner=owner,scenario='lazy-taunt-explicit-query-down-revive',observations=[initial,resolved,down,revived,queried]))
  bm=make(owner,'all_allies');initial=snapshot(bm,0);assert initial['taunters']==[NAMES[0]]
  bm.knock_down(NAMES[0],.2);down=snapshot(bm,.2);assert down['taunters']==[NAMES[1]]
  bm.revive(NAMES[0],.3,100);revived=snapshot(bm,.3)
  expected=NAMES[1]
  assert revived['taunters']==[expected],revived
  rows.append(dict(owner=owner,scenario='all-allies-first-member-down-revive-appends',observations=[initial,down,revived]))
  bm=make(owner,['allies_right:1','self']);initial=snapshot(bm,0);first=min(owner+1,4);assert initial['taunters']==[NAMES[first]]
  rows.append(dict(owner=owner,scenario='ordered-first-recipient-not-smallest-slot',observations=[initial]))
  bm=make(owner,'boss');initial=snapshot(bm,0);assert initial['taunters']==[NAMES[owner]]
  bm.drop_enemies(['__enemy__'],.2);gone=snapshot(bm,.2);assert gone['taunters']==[]
  rows.append(dict(owner=owner,scenario='enemy-membership-dropped',observations=[initial,gone]))
  bm=make(owner,'allies_top_atk_excl:1','stealth');initial=snapshot(bm,0);assert initial['carriers'][0]['targets'] is None
  assert not bm.has_live_stat(NAMES[owner],'stealth',.1)
  resolved=snapshot(bm,.1);assert resolved['carriers'][0]['targets']==[NAMES[winner]]
  rows.append(dict(owner=owner,scenario='stealth-resolves-on-first-pool-query-even-nonmember',observations=[initial,resolved]))
 paths=['research/characterize-taunt-edges.py','research/upstream/nikke-calc-master/calculator/buff_manager.py']
 r=dict(passed=True,cpu_only=True,cases=rows,gpu_admission_enabled=False,gpu_execution_performed=False,scope='25 native boundary cases. Revive behavior is characterization of an outstanding shared executor feature,not a GPU certification.',source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths})
 (ROOT/'research/portable-taunt-edge-native-study.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(len(rows),'native target-marker edge cases passed;GPU admission unchanged')
if __name__=='__main__':main()
