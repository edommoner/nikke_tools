"""CPU-only native-state observation paired with already-retained real GPU data."""
import copy,importlib.util,json,sys
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
import engine_worker
from calculator import timeline
from detail_coverage import body_for
spec=importlib.util.spec_from_file_location('state_roster',ROOT/'scripts/verify-portable-roster-battles.py');roster=importlib.util.module_from_spec(spec);spec.loader.exec_module(roster)
def main():
 prior=json.loads((ROOT/'research/portable-mode-entry-first-real-candidate-metal.json').read_text());rows=[]
 for stored in prior['cases']:
  body={**body_for(roster.roster_for('라플라스 : 얼티밋 히어로'),duration=180,grown=stored['grown']),'burst_gauge_mode':'accumulate'};managers=[];results=[];Original=timeline.BurstController;execute=engine_worker.sim.execute
  class Recording(Original):
   def tick(self,t,bm,state):e=super().tick(t,bm,state);managers.append((bm,t));return e
  def record(run):r=execute(run);results.append(r);return r
  with patch.object(timeline,'BurstController',Recording),patch.object(engine_worker.sim,'execute',record):native=roster.reference.native_reference(copy.deepcopy(body))
  bm,t=managers[-1];name=body['squad'][0];before=[None if a.target_chars is None else a.target_chars.copy() for a in bm._active];buffs=bm.get_buffs(name,'__enemy__',t);carriers=[]
  for a in bm._active:
   index=next(i for i,(e,n) in enumerate(bm._effects) if e is a.effect and n==a.caster)
   carriers.append(dict(definition=index,name=a.effect['name'],owner=a.caster,stat=a.effect.get('stat'),stack=a.stack,targets=a.target_chars,value=bm._get_value(a.effect,a,name),expires=a.expires_at))
  gpu=stored['gpu'];lookup={a['definition']:a for a in gpu['carriers']};diff=[]
  for c in carriers:
   g=lookup.get(c['definition']);mask=None if c['targets'] is None else sum(1<<body['squad'].index(n) for n in set(c['targets']) if n in body['squad'])
   if g is None or mask is not None and mask!=g['recipients']:diff.append(dict(native=c,gpu=g))
  hits=[vars(h) for h in results[-1].hits if h.caster==name]
  rows.append(dict(grown=stored['grown'],native_final_buffs=buffs,native_carriers=carriers,retained_gpu_carriers=gpu['carriers'],membership_differences=diff,native_hits=hits,reload_events=[vars(e) for e in results[-1].log.reload_log if e.caster==name],native=native))
 (ROOT/'research/portable-mode-entry-native-state-diagnosis.json').write_text(json.dumps(dict(cpu_only=True,new_gpu_runs=0,cases=rows),ensure_ascii=False,indent=2)+'\n')
 for r in rows:print(r['grown'],'atk flat',r['native_final_buffs']['atk_flat'],'membership differences',[(x['native']['name'],x['native']['targets'],None if x['gpu'] is None else (x['gpu']['recipients'],x['gpu']['lazy_pending'])) for x in r['membership_differences']])
if __name__=='__main__':main()
