"""Whole-squad production GPU down/revive parity against the explicit CPU bridge.

No CPU trace is used as GPU input. This verifier imports the ordinary application modules.
HP-edge trigger definitions are separately rejected until their own GPU port.
"""
import argparse,copy,hashlib,importlib.util,json,random,sys,ast,inspect,textwrap
from pathlib import Path
from datetime import datetime,timezone
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
 s=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
sys.path.insert(0,str(ROOT/'app'))
import engine_worker
import detail_gpu as g
v=load('survival_incoming_oracle','scripts/verify-incoming-detail.py')
from calculator import timeline
from calculator.timeline import CharState
from calculator.buff_manager import BuffManager
N=v.NAMES;B=v.B;E=v.E

def lethal(target='slot:1',at=.1,hits=1,interval=.3):return dict(id='lethal',kind='attack',delay=at,until={'time':.7},spec=dict(coeff=100,atk=100000000,target=target,hits=hits,interval=interval,pierce=True))

def fixtures(quick=False):
 for case in ('down','revive','preserve-marker','restore-passive-not-periodic','shared-passive-no-double-stack','once-only-revive','whole-squad-hit-order'):
  b=v.body(1);b['enemy']['patterns']=[lethal('all' if case=='whole-squad-hit-order' else 'slot:1',hits=2 if case=='once-only-revive' else 1)]
  extra={N[0]:[B('own permanent','atk_pct',10),B('shared permanent','atk_pct',10,'all_allies',max_stack=3)],N[1]:[]}
  if case!='down':extra[N[1]].append(E('revive ally','instant','revive',50,'allies_down_top_atk_excl:1',event='event:ally_down',max_trigger=1))
  if case=='preserve-marker':extra[N[0]].append(B('preserved','atk_pct',7,persist_on_revive=True))
  if case=='restore-passive-not-periodic':extra[N[0]]+=[B('passive hp','max_hp_pct',25),B('periodic permanent','atk_pct',5,event='every:0.03s')]
  yield case,b,extra
 for case in ('registered-dot','registered-heal','new-every-trigger','normal-shots-stop','global-ammo-counter','personal-attack-counter','persisted-dot-power'):
  b=v.body(2);b['enemy']['patterns']=[lethal(at=.35)];extra={N[0]:[],N[1]:[]}
  if case in ('registered-dot','persisted-dot-power'):extra[N[0]]=[E('observed dot','damage','dot_damage',100,'target',tick_interval=.2,duration=1)]
  if case=='persisted-dot-power':extra[N[0]].append(B('preserved power','atk_pct',77,persist_on_revive=True))
  if case=='registered-heal':extra[N[0]]=[B('room for healing','max_hp_only_pct',100,'all_allies'),E('observed heal','instant','heal_hp_pct',1,'all_allies',tick_interval=.2,duration=1)]
  if case=='new-every-trigger':extra[N[0]]=[B('observed every','atk_pct',5,'all_allies',event='every:0.2s',duration=.4)]
  if case.endswith('counter'):
   extra[N[0]]=[B('observed counter','atk_pct',1,'all_allies',event='squad_ammo_consume:10' if case.startswith('global') else 'on_attack_count:10',max_stack=100)]
   extra[N[1]]=[E('late revive','instant','revive',50,'allies_down_top_atk_excl:1',event='every:0.8s',max_trigger=1)]
  if quick and case not in ('registered-dot','global-ammo-counter','persisted-dot-power'):continue
  yield case,b,extra
 if quick:return
 for character in ('모더니아','맥스웰'):
  for restore in (False,True):
   names=[N[0],N[1],character,N[3],N[4]];b=v.body(8,True,names);b['burst_gauge_mode']='fixed';b['enemy']['patterns']=[lethal('slot:3',3.8)]
   extra={names[-1]:[E('late revive','instant','revive',50,'allies_down_top_atk_excl:1',event='every:5.5s',max_trigger=1)]} if restore else {}
   yield 'raw-mode-'+character+'-'+str(restore),b,extra
 for character in ('앨리스','솔린','크라운'):
  names=[character]+[n for n in N if n!=character][:4];b=v.body(4,True,names);b['burst_gauge_mode']='fixed';b['enemy']['patterns']=[lethal(at=.35)]
  yield 'raw-hp-passive-'+character,b,{names[-1]:[E('late revive','instant','revive',50,'allies_down_top_atk_excl:1',event='every:0.8s',max_trigger=1)]}
 for pct in (50,100):
  b=v.body(1);b['burst_gauge_mode']='fixed';b['enemy']['patterns']=[lethal(at=.35)]
  yield 'hp-predicate-'+str(pct),b,{N[0]:[B('larger maximum','max_hp_pct',25),B('healthy','atk_pct',50,event='passive',condition=['self_hp_above:80'])],N[1]:[E('late revive','instant','revive',pct,'allies_down_top_atk_excl:1',event='every:0.8s',max_trigger=1)]}
 for rule in ('all','slot:1','slot:2,4','random:2','top_atk:2'):
  b=v.body(2);b['enemy']['patterns']=[lethal(),dict(id='selection',kind='attack',delay=.2,until={'time':1.6},spec=dict(coeff=100,atk=1,target=rule,hits=7,interval=.2))]
  yield 'targets-after-down-'+rule,b,{}
 b=v.body(1);b['enemy']['patterns']=[lethal(at=.1),{**lethal('slot:5',.2),'id':'other-down'}]
 role=v.v.a.META[N[0]]['class']
 yield 'revive-class-random',b,{N[1]:[E('class revive','instant','revive',50,'allies_down_class_random:'+role+':1',event='every:0.8s',max_trigger=1)]}
 names=[N[0],N[1],N[2],N[3],'맥스웰'];b=v.body(8,False,names);b['burst_gauge_mode']='fixed';b['enemy']['patterns']=[lethal(at=2.8)]
 yield 'waiting-burst-resumes-after-only-b1-revives',b,{N[1]:[E('late revive','instant','revive',50,'allies_down_top_atk_excl:1',event='every:5.5s',max_trigger=1)]}
 b=v.body(4);b['enemy']['patterns']=[lethal()]
 yield 'count-limited-class-does-not-refill',b,{N[1]:[B('support power','atk_pct',100,'allies_class:'+role+':1',event='every:0.6s')]}
 b=v.body(4);b['enemy']['patterns']=[lethal(at=100)]
 yield 'count-limited-class-first-alive',b,{N[1]:[B('support power','atk_pct',100,'allies_class:'+role+':1',event='every:0.6s')]}
 charged=[n for n in N if (v.v.a.META[n].get('charge_time') or 0)>0];charged.sort(key=lambda n:-v.v.a.META[n]['charge_time']);assert len(charged)>=2
 b=v.body(4);b['enemy']['patterns']=[lethal('slot:'+str(N.index(charged[0])+1))]
 yield 'charge-prefix-does-not-refill',b,{N[1]:[B('charge prefix power','atk_pct',100,'allies_top_base_charge_time:1',event='every:0.6s')]}
 names=[N[0],N[1],'라푼젤','라플라스',N[2]];b=v.body(4,False,names);b['enemy']['patterns']=[lethal('slot:3')]
 code=v.v.a.META[names[2]]['element_code'];weapon=v.v.a.META[names[2]]['weapon_type'];assert (code,weapon)==(v.v.a.META[names[3]]['element_code'],v.v.a.META[names[3]]['weapon_type'])
 yield 'leftmost-living-refills',b,{N[1]:[B('leftmost living power','atk_pct',100,'allies_code_weapon_leftmost:'+code+':'+weapon+':1',event='every:0.6s')]}
 for restore in (False,True):
  b=v.body(8);b['burst_gauge_mode']='fixed';b['enemy']['patterns']=[lethal(at=2.8)]
  extra={N[1]:[E('late revive','instant','revive',50,'allies_down_top_atk_excl:1',event='every:5.5s',max_trigger=1)]} if restore else {}
  yield 'dead-first-b1-keeps-backup-priority-'+str(restore),b,extra
 b=v.body(8);b['burst_gauge_mode']='fixed';b['enemy']['patterns']=[lethal('slot:2',2.8)]
 yield 'dead-b2-waits-for-revival',b,{N[4]:[E('late revive','instant','revive',50,'allies_down_top_atk_excl:1',event='every:5.5s',max_trigger=1)]}
 for predicate in ('has_burst1_ally','no_burst1_ally'):
  for restore in (False,True):
   names=[*N[:4],'맥스웰'];b=v.body(4,False,names);b['burst_gauge_mode']='fixed';b['enemy']['patterns']=[lethal(at=.1)]
   extra={names[1]:[B('B1 predicate power','atk_pct',100,'all_allies',event='every:0.3s',condition=[predicate])]}
   if restore:extra[names[2]]=[E('late revive','instant','revive',50,'allies_down_top_atk_excl:1',event='every:2.0s',max_trigger=1)]
   yield 'dead-b1-ally-'+predicate+'-'+str(restore),b,extra
 for character in ('디젤 : 윈터 스위츠','앤 : 미라클 페어리','라푼젤','마나'):
  names=[character]+[n for n in N if n!=character][:4]
  for attacked in (False,True):
   b=v.body(30,True,names);b['burst_gauge_mode']='fixed';target='slot:1' if character.startswith('디젤') else 'slot:5'
   b['enemy']['patterns']=[lethal(target,2.8 if attacked else 100)]
   yield 'raw-new-'+character+('-death' if attacked else '-no-shot'),b,{}

def compare(device,name,b,extra,backend):
 frames=[];down_frames=[];captured={};revived=[];activation_witness=[];code=timeline.simulate.__code__;lines,first=inspect.getsourcelines(timeline.simulate);tree=ast.parse(textwrap.dedent(''.join(lines)))
 advance=[n for n in ast.walk(tree) if isinstance(n,ast.AugAssign) and isinstance(n.target,ast.Name) and n.target.id=='t' and isinstance(n.value,ast.Name) and n.value.id=='DT'];assert len(advance)==1
 end_line=first+advance[0].lineno-1;names=b['squad']
 def snapshot(state):return {n:dict(hp=state['hp'][n],cover_hp=state['cover_hp'][n],cover_max_hp=state['cover_max_hp'][n]) for n in names}
 def mask(state):return sum(1<<i for i,n in enumerate(names) if n in state.get('down',set()))
 def trace(frame,event,arg):
  if frame.f_code is not code:return None
  local=frame.f_locals
  if event=='line' and frame.f_lineno==end_line:frames.append(dict(time=local['t'],state=snapshot(local['state'])));down_frames.append(dict(time=local['t'],mask=mask(local['state'])))
  if event=='return':
   state=local['state'];captured.update(state=snapshot(state),down=mask(state),burst_stages=copy.deepcopy(state.get('burst_stages',{})),boss_rng=list(local['boss_rng'].getstate()[1]),control={n:dict(charging=bool(state.get('charging',{}).get(n,False)),ammo=local['char_states'][n].ammo,reloading_until=local['char_states'][n].reloading_until) for n in names})
  return trace
 original_revive=CharState.on_revive
 def on_revive(self,t,bm):revived.append(dict(time=t,name=self.name));return original_revive(self,t,bm)
 original_activate=BuffManager._activate
 def activated(self,eff,caster,t,*args,**kwargs):
  result=original_activate(self,eff,caster,t,*args,**kwargs)
  if eff.get('name') in ('B1 predicate power','support power','charge prefix power','leftmost living power'):
   activation_witness.append(dict(name=eff['name'],time=t,caster=caster,active_targets=[list(a.target_chars or []) for a in self._active if a.effect.get('name')==eff['name'] and a.caster==caster]))
  return result
 with v.context(name,extra):
  compiled=v.v.a.evaluate({**b,'_compile_gpu_detail':True});gpu=g.evaluate_full(device,compiled,module_backend=backend)
  previous=sys.gettrace()
  with patch.object(CharState,'on_revive',on_revive),patch.object(BuffManager,'_activate',activated):
   try:sys.settrace(trace);cpu=v.v.a.evaluate(b)
   finally:sys.settrace(previous)
  skill_rng=list(random.getstate()[1])
 checks=v.v.v.resolve_verification(gpu,cpu)['compute']['cpu_verification']
 control={n:{k:gpu['compute']['final_control'][n][k] for k in ('charging','ammo','reloading_until')} for n in names}
 checks.update(actual_gpu=gpu['compute']['backend']=='cuda_detail',incoming_frames=v.close(gpu['_incoming_frames'],frames),final_state=v.close(gpu['_incoming_state'],captured['state']),down_frames=gpu['_down_frames']==down_frames,final_down=gpu['_down_mask']==captured['down'],boss_rng=gpu['_boss_random_state']==captured['boss_rng'],skill_rng=gpu['_random_state']==skill_rng,final_control=v.close(control,captured['control']))
 if name.startswith('dead-b1-ally-'):
  before_revive=[x for x in activation_witness if x['time']<1 and x['active_targets']]
  checks['b1_composition_positive_control']=bool(before_revive)==('has_burst1_ally' in name) and captured['burst_stages'].get(names[0])=='1'
 if name in ('count-limited-class-does-not-refill','charge-prefix-does-not-refill'):checks['fixed_prefix_empty_recipient_exercised']=bool(activation_witness) and all(x['active_targets']==[[]] for x in activation_witness)
 if name=='count-limited-class-first-alive':checks['fixed_prefix_alive_recipient_exercised']=any([N[0]] in x['active_targets'] for x in activation_witness)
 if name=='leftmost-living-refills':checks['living_prefix_refill_exercised']=any([names[3]] in x['active_targets'] for x in activation_witness)
 row=dict(name=name,backend=backend,passed=all(checks.values()),checks=checks,cpu_total=cpu['total_damage'],gpu_total=gpu['total_damage'],cpu_revives=revived,raw_skills_retained=name.startswith('raw-'),incoming_hits=len(cpu['incoming_hits']))
 if activation_witness or name.startswith('dead-b1-ally-'):row.update(cpu_activation_witness=activation_witness,cpu_burst_stages=captured['burst_stages'])
 if not checks['incoming_hits_equal']:row['hit_difference']=next((dict(index=i,cpu=c,gpu=x) for i,(c,x) in enumerate(zip(cpu['incoming_hits'],gpu['incoming_hits'])) if c!=x),dict(cpu_count=len(cpu['incoming_hits']),gpu_count=len(gpu['incoming_hits'])))
 if not checks['incoming_frames']:row['frame_difference']=next((dict(index=i,cpu=c,gpu=x) for i,(c,x) in enumerate(zip(frames,gpu['_incoming_frames'])) if not v.close(c,x)),dict(cpu_count=len(frames),gpu_count=len(gpu['_incoming_frames'])))
 if not checks['down_frames']:row['down_difference']=next((dict(index=i,cpu=c,gpu=x) for i,(c,x) in enumerate(zip(down_frames,gpu['_down_frames'])) if c!=x),None)
 if not checks['final_control']:row.update(cpu_control=captured['control'],gpu_control=control)
 print(json.dumps(row,ensure_ascii=True),flush=True);return row

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--backend',choices=['native','ptx'],default='native');ap.add_argument('--quick',action='store_true');ap.add_argument('--fail-fast',action='store_true');ap.add_argument('--output',default='research/detail-survival-verification.json');args=ap.parse_args()
 files=['scripts/verify-survival-detail.py','scripts/verify-incoming-detail.py','app/detail_gpu.py','app/detail_effects.cu','app/detail_effects.ptx','app/detail_effects-build.json','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','app/survival_compat.py','app/detail_boss.py','app/detail_world.py','app/engine_worker.py','app/engine_compat.py','app/gpu_service.py','research/upstream/nikke-calc-master/calculator/timeline.py','research/upstream/nikke-calc-master/calculator/buff_manager.py']
 sha=lambda p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest();hashes={p:sha(p) for p in files};planned=list(fixtures(args.quick));rows=[];device=v.v.v.Cuda()
 try:
  for name,b,extra in planned:
   try:row=compare(device,name,b,extra,args.backend)
   except Exception as error:row=dict(name=name,passed=False,error=repr(error));print(json.dumps(row,ensure_ascii=True),flush=True)
   rows.append(row)
   if args.fail_fast and not row['passed']:break
 finally:device.close()
 assert hashes=={p:sha(p) for p in files}
 report=dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=len(rows)==len(planned) and all(r['passed'] for r in rows),objective_complete=False,abi=g.DETAIL_ABI,stage_only=False,planned_cases=len(planned),not_run_cases=len(planned)-len(rows),cases=rows,source_sha256=hashes,cpu_trace_used_as_gpu_input=False,remaining='HP-edge trigger definitions and other unsupported effects remain fail-closed; this is not all-character completion.')
 (ROOT/args.output).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');raise SystemExit(0 if report['passed'] else 1)
