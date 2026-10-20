"""Independent real CharState firing study for HP-derived attack;CPU only."""
import copy,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
import engine_worker
from calculator.buff_manager import BuffManager
from portable_weapon_oracle import authored_weapon,authored_weapon_state
from timer_registry_cases import NAMES

def main():
 rows=[]
 for owner in range(5):
  for target in ('self','all_allies'):
   shooter=owner if target=='self' else (owner+1)%5
   for weapon_type in ('AR','SG','SR','RL'):
    for duration in (-1,1):
     charge=weapon_type in ('SR','RL');pellets=10 if weapon_type=='SG' else 1
     w=dict(mode='charge' if charge else 'auto',base_weapon_type=weapon_type,coefficient=100,capacity=1000,interval=1,charge=.5,full_charge_mult=300 if charge else 100,pellets=pellets,gauge=0)
     chars=[dict(name=n,skill_levels={'1':10,'2':10,'3':10},_weapon=copy.deepcopy(engine_worker.META[n])) for n in NAMES];authored_weapon(chars[shooter],w)
     effect=dict(name='hp-attack',source='스킬1',type='buff',stat='atk_from_hp_pct',fixed_value=10,target=target,duration=duration,trigger=dict(timing=['battle_start'],condition=[]))
     class BM(BuffManager):
      def _register_all(self):self._effects=[(copy.deepcopy(effect),NAMES[owner])];self._build_notify_index()
     enemy={'def':0,'core_px':0,'code':None,'optimal_range_weapons':[]}
     bm=BM(chars,state=dict(base_stats={n:dict(atk=1000,hp=10000+2000*i,**{'def':0}) for i,n in enumerate(NAMES)},enemy=enemy,full_burst=False,rng_acc={},rng_expected=True,camera=set()))
     st=authored_weapon_state(chars[shooter],w)
     for n in NAMES:bm.notify('battle_start',0,n)
     st.ammo=st._full_ammo(bm,0);hits=[];bad=[]
     for frame in range(121):
      t=frame/60;bm.tick(t)
      for h in st.tick(t,bm,enemy,{'rng_mode':'expected'}):
       flat=(10000+2000*shooter)*.1 if duration==-1 or t<duration else 0
       parent=max(1,round((1000+flat)*1.075*(3 if charge else 1)))
       expected=round(parent/pellets) if pellets>1 else parent
       record=dict(time=t,damage=h.damage,expected=expected)
       hits.append(record)
       if h.damage!=expected:bad.append(record)
     rows.append(dict(owner=owner,target=target,shooter=shooter,weapon_type=weapon_type,duration=duration,passed=not bad and bool(hits),hits=hits,bad=bad))
 passed=all(r['passed'] for r in rows)
 report=dict(passed=passed,cpu_only=True,gpu_execution_performed=False,cases=rows,scope='Actual native CharState.tick,AR/SG/SR/RL,self/other-recipient,finite/infinite HP conversion. No GPU or full-character certification.',source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ['research/characterize-hp-attack-physical.py','research/upstream/nikke-calc-master/calculator/buff_manager.py','research/upstream/nikke-calc-master/calculator/timeline.py']})
 (ROOT/'research/portable-hp-attack-physical-native.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 assert passed,[(r['owner'],r['weapon_type'],r['bad'][:2]) for r in rows if not r['passed']]
 print(len(rows),'native HP-derived actual-firing cases passed')
if __name__=='__main__':main()
