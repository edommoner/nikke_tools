"""Independent reach-part lifecycle and complete-squad CPU/GPU parity."""
import argparse,copy,hashlib,importlib.util,json,random,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
def module(name,path):
 s=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
p=module('parts_periodic','scripts/verify-periodic-detail.py');raw=module('parts_raw','scripts/verify-cleanse-detail.py');oracle=module('parts_oracle','scripts/verify-detail.py')
from detail_gpu import compile_effects,run,evaluate_full
from detail_world import packed_enemy
from gpu_selector import Cuda
from gpu_service import resolve_verification
E=p.effect
NAMES=['리타','크라운','앨리스','모더니아','맥스웰']

def reach_primitives(device,backend):
 refs=json.loads((ROOT/'research/detail-range-geometry-cpu-references.json').read_text(encoding='utf-8'));cases=refs['reach'];errors=[]
 for f,h in refs['source_sha256'].items():assert hashlib.sha256((ROOT/f).read_bytes()).hexdigest()==h,f
 script=[[0,0,0,2,0,-1,0,0],[0,4,0,0,0,-1,0,0]]+[[0,2,114,0,k,k,0,0] for k in range(5)]
 for start in range(0,len(cases),16):
  group=cases[start:start+16];programs=[];enemies=[];stats=[]
  for ref in group:
   inp=ref['input'];chars=oracle.characters(NAMES);owner=NAMES[2]
   effects=[(E('pierce range','buff','pierce_range',inp['pierce_range']),owner),(E('explosion range','buff','explosion_range',inp['explosion_range']),owner),(E('authored geometry hit','damage','damage',100,'target'),owner)]
   program=compile_effects(chars,effects)
   # Authored hit-type flags are primitive inputs; the kernel computes the
   # reach and part component. Expected CPU reach is never passed to the GPU.
   program['effects'][-1][39]=(65536 if inp['parts_skill'] else 0)|(8 if inp['explosion'] else 0)|(64 if inp['pierce'] else 0)
   programs.append(program);enemies.append(packed_enemy({'def':0,'core_px':0},[dict(name='tier'+str(k),hp=0,reach=k) for k in range(1,6)]));stats.append({n:{'atk':10000,'def':1000,'hp':100000} for n in NAMES})
  result=run(device,programs,script,enemies,stats,module_backend=backend)
  for i,ref in enumerate(group):
   actual=[q[2] for q in result['queries'][i]];want=[int(k<=ref['expected']) for k in range(1,6)]
   if actual!=want:errors.append(dict(index=start+i,input=ref['input'],actual=actual,expected=want))
 row=dict(kind='reach-primitive',backend=backend,count=len(cases),passed=not errors,errors=errors)
 print(json.dumps(row,ensure_ascii=True),flush=True);return row

def primitives(device,backend):
 refs=json.loads((ROOT/'research/detail-live-reach-cpu-references.json').read_text(encoding='utf-8'))
 for f,h in refs['source_sha256'].items():assert hashlib.sha256((ROOT/f).read_bytes()).hexdigest()==h,f
 cases=sorted([r for r in refs['cases'] if r['input']['pattern']['kind']=='parts'],key=lambda r:(r['input']['reach'],r['input']['aimed']));errors=[]
 for start in range(0,len(cases),3):
  group=cases[start:start+3];script=None;programs=[];enemies=[];stats=[]
  for ref in group:
   inp=ref['input'];parts=[{k:x[k] for k in ('name','hp','reach')} for x in inp['pattern']['targets']]
   chars=oracle.characters(NAMES);effects=[(E('destroy detector','buff','atk_pct',1,event='event:part_destroy',max_stack=32),name) for name in NAMES]
   programs.append(compile_effects(chars,effects));enemies.append(packed_enemy({'def':0,'core_px':0},parts));stats.append({n:{'atk':10000,'def':1000,'hp':100000} for n in NAMES})
   authored=[];qi=0;aimed=next((i for i,x in enumerate(parts) if x['name']==inp['aimed']),-1)
   for frame in range(6):
    t=frame/60;authored.append([t,2,114,0,0,qi,0,0]);qi+=1
    authored.extend([[t,7,1,0,0,-1,0,-1],[t,7,0,0,inp['reach'],-1,10,aimed]])
    for target in range(5):authored.append([t,2,114,0,target,qi,0,0]);qi+=1
    for who in range(5):authored.append([t,2,103,who,0,qi,0,0]);qi+=1
   if script is not None:assert script==authored
   script=authored
  result=run(device,programs,script,enemies,stats,module_backend=backend)
  for i,ref in enumerate(group):
   delivered=0;at={};previous_dead=0
   for frame,want in enumerate(ref['expected_frames']):
    queries=result['queries'][i][frame*11:(frame+1)*11];delivered+=len(want['events'])
    if queries[0][5]!=len(want['events']):errors.append([start+i,frame,'next-frame-events',queries[0][5],len(want['events'])])
    dead=sum(x['destroyed'] for x in want['targets']);pending=dead-previous_dead;previous_dead=dead
    for target,x in enumerate(want['targets']):
     if x['destroyed'] and target not in at:at[target]=frame/60
     expected=[int(x['destroyed']),x['extra_dealt'],x['extra_hits'],at.get(target,-1),want['minimum_reach'],pending]
     if queries[1+target][:6]!=expected:errors.append([start+i,frame,target,queries[1+target][:6],expected])
    if any(q[0]!=delivered for q in queries[6:11]):errors.append([start+i,frame,'broadcast-destroy-events',delivered,[q[0] for q in queries[6:11]]])
 row=dict(kind='primitive',backend=backend,count=len(cases),passed=not errors,errors=errors)
 print(json.dumps(row,ensure_ascii=True),flush=True);return row

def parts():return [dict(name='tier'+str(i),hp=5 if i==1 else 0,reach=i) for i in range(1,6)]

def scenarios():
 owner=NAMES[2]
 pierce=E('pierce','buff','pierce_enabled',1)
 witness=E('destroy response','buff','atk_pct',17,'all_allies',event='event:part_destroy',max_stack=32)
 yield 'timed-pierce-range',NAMES,owner,[pierce,E('wide pierce','buff','pierce_range',100,event='every:2s',duration=1.5),witness],2,False
 yield 'stacked-pierce-range',NAMES,owner,[pierce,E('wide stacks','buff','pierce_range',20,event='full_charge_fire',duration=10,max_stack=5),witness],2,False
 rl=NAMES[:4]+['N102'];rocket='N102'
 yield 'timed-explosion-range',rl,rocket,[E('wide explosion','buff','explosion_range',100,event='every:2s',duration=1.5),witness],4,False
 yield 'negative-explosion-range',rl,rocket,[E('narrow explosion','buff','explosion_range',-100),witness],3,False
 yield 'pierce-skill-multiple-hits',NAMES,owner,[E('pierce skill','damage','pierce_damage:2',250,'target',event='every:0.5s'),E('skill range','buff','pierce_range',100),witness],2,False
 yield 'explosion-skill-multiple-hits',NAMES,owner,[E('explosion skill','damage','projectile_explosion_damage:3',250,'target',event='every:0.5s'),E('skill range','buff','explosion_range',100),witness],4,False
 yield 'parts-skill-and-base-presence',NAMES,owner,[E('parts skill','damage','damage:2',250,'all_enemies',event='every:1s',hits_parts=True),E('part power','buff','part_dmg_pct',35),witness],5,True
 yield 'deferred-b3-bonus-parts',NAMES,owner,[E('burst bonus parts','damage','bonus_damage:2',1000,'all_enemies',event='burst_cast',hits_parts=True),witness],5,False
 yield 'dot-part-snapshots',NAMES,owner,[E('parts dot','damage','dot_damage',100,'target',event='every:3s',tick_interval=.5,duration=2,hits_parts=True),witness],5,False
 yield 'normal-formula-rocket-skill',rl,rocket,[E('normal skill','damage','damage:2',250,'target',event='every:0.5s',damage_formula='normal_attack'),E('wide explosion','buff','explosion_range',100),witness],4,False
 yield 'part-lifesteal-ordered-recipients',NAMES,owner,[pierce,E('wide pierce','buff','pierce_range',100),E('health room','buff','max_hp_only_pct',100,'all_allies'),E('lifesteal','buff','lifesteal_pct',5,'all_allies'),E('heal trigger','buff','atk_pct',5,event='event:heal_received',max_stack=10),witness],2,False

def compare(device,label,body,backend,effects=None,real=False,witness=1):
 context=raw.injected_effects(effects or {}) if real else p.custom_effects(effects or {})
 with context:
  compiled=p.a.evaluate({**body,'_compile_gpu_detail':True});gpu=evaluate_full(device,compiled,module_backend=backend);cpu=p.a.evaluate(body);rng=list(random.getstate()[1])
 result=resolve_verification(gpu,cpu);checks=result['compute']['cpu_verification'].copy()
 checks.update(actual_gpu=result['compute']['backend']=='cuda_detail',final_random_state=rng==gpu['_random_state'],parts_damage_exercised=sum(x['damage'] for x in cpu['parts_state'])>0,
               part_destroyed=cpu['parts_state'][0]['destroyed'],unbreakable_survived=not cpu['parts_state'][1]['destroyed'])
 if witness:checks['reach_witness_hit']=cpu['parts_state'][witness-1]['damage']>0
 row=dict(kind='battle',name=label,backend=backend,mode=body['burst_gauge_mode'],passed=all(checks.values()),checks=checks,raw_skills_retained=real,
          cpu_total=cpu['total_damage'],gpu_total=gpu['total_damage'],parts_state=cpu['parts_state'])
 if not row['passed']:row.update(gpu_parts_state=gpu.get('parts_state'),cpu_members=cpu['members'],gpu_members=gpu['members'],cpu_bursts=cpu['burst_timeline'],gpu_bursts=gpu['burst_timeline'])
 print(json.dumps(row,ensure_ascii=True),flush=True);return row

def verify(device,backend,quick=False):
 rows=[reach_primitives(device,backend),primitives(device,backend)]
 for label,names,subject,effects,witness,base_presence in scenarios():
  for mode in ('fixed','accumulate'):
   body=p.body_for(names,14,True);body.update(seed=12345,burst_policy='rules',burst_gauge_mode=mode,_debug_random_state=True)
   body['enemy'].update(parts=parts(),core_px=50,has_parts=base_presence)
   rows.append(compare(device,label,body,backend,{subject:effects},witness=witness))
 if not quick:
  before=json.loads((ROOT/'research/detail-coverage-optimal-range.json').read_text(encoding='utf-8'));after=json.loads((ROOT/'research/detail-coverage-live-parts.json').read_text(encoding='utf-8'))
  old={r['character'] for r in before['results'] if r['supported']}
  for subject in [r['character'] for r in after['results'] if r['supported'] and r['character'] not in old]:
   names=[subject,'리타','크라운','앨리스','모더니아']
   for mode in ('fixed','accumulate'):
    for core in (0,50):
     body=p.body_for(names,35,True);body.update(seed=12345,shooting_policy='character',burst_policy='rules',burst_gauge_mode=mode,_debug_random_state=True)
     body['profile']['chars'][subject]['skill_levels']={'1':10,'2':10,'3':10};body['enemy'].update(parts=parts(),core_px=core)
     rows.append(compare(device,'raw-'+subject,body,backend,real=True,witness=1))
 return rows

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--backend',choices=['native','ptx','both'],default='both');parser.add_argument('--quick',action='store_true');args=parser.parse_args()
 files=['scripts/verify-live-parts-detail.py','app/detail_gpu.py','app/detail_effects.cu','app/detail_effects.ptx','app/detail_effects-build.json','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','app/detail_world.py','app/engine_worker.py','app/gpu_service.py']
 hashes={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in files};d=Cuda()
 try:rows=[r for b in (('native','ptx') if args.backend=='both' else (args.backend,)) for r in verify(d,b,args.quick)]
 finally:d.close()
 assert hashes=={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in files},'Sources changed during verification'
 report=dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=all(r['passed'] for r in rows),objective_complete=False,cases=rows,source_sha256=hashes,cpu_trace_used_as_gpu_input=False,
  scope='Fixed simultaneous non-penalty reach parts only; coordinates, interrupts, spawns, movement, aim targets, damage/cover/down/revive and other unsupported effects remain.')
 suffix='quick' if args.quick else 'verification';(ROOT/f'research/detail-live-parts-{suffix}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 raise SystemExit(0 if report['passed'] else 1)
