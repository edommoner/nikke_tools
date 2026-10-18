"""Independent ordered/duplicate target list and real whole-squad parity."""
import importlib.util,json,sys,math,hashlib
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from gpu_selector import Cuda
from detail_gpu import run
from detail_coverage import body_for,coverage
spec=importlib.util.spec_from_file_location('list_targets_oracle',ROOT/'scripts/verify-targets-detail.py');base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
E=base.E;oracle=base.oracle;periodic=base.periodic;NAMES=base.NAMES

def primitives():
 out=[]
 def build(name,effects,commands=None,expected=None):
  p=oracle.program(oracle.characters(NAMES),[(e,NAMES[i]) for i,e in effects]);script=[[0,0,0,i,0,-1,0,0] for i in range(5)];qi=0
  for t,op,who in commands or [(0.1,'query',i) for i in range(5)]:
   if op=='query':script.append([t,2,0,who,-1,qi,0,0]);qi+=1
   else:script.append([t,0,op,who,0,-1,0,0])
  out.append((name,p,script,expected))
 buff=lambda name,target,**kw:E(name,'buff','atk_pct',7,target,**kw)
 build('duplicate-target-buff-counted-once',[(0,buff('list',['self','self']))],expected=[7,0,0,0,0])
 build('empty-nested-lists-are-empty',[(0,buff('empty',[[],[[]]]))],expected=[0]*5)
 build('list-rank-is-eager-before-later-stat-buff',[(0,buff('eager',['self','allies_top_atk_excl:1'])),(1,E('strong','buff','atk_pct',100)),(0,E('lazy','buff','atk_pct',13,'allies_top_atk_excl:1'))],expected=[7,113,0,0,7])
 build('rank-preserves-cpu-raw-active-value-semantics',[(1,E('gate','buff','',0)),(1,E('runtime false','buff','atk_pct',100,condition=['self_state:gate'])),(1,E('remove','instant','remove_named_buff',0,event='burst_cast',target_effect='gate')),(0,buff('rank',['allies_top_atk:1'],event='on_attack'))],commands=[(.1,3,1),(.2,7,0)]+[(.3,'query',i) for i in range(5)],expected=[0,7,0,0,0])
 witness=lambda who,value:(who,E('witness '+str(who),'buff','atk_pct',value,event='event:mark',max_stack=100))
 build('recipient-scoped-name-events-preserve-duplicates',[(0,E('mark','buff','',0,[NAMES[3],NAMES[1],NAMES[3]],event_scope='recipients')),witness(1,2),witness(3,3)],expected=[0,2,0,6,0])
 for label,targets,value in [('reverse',[NAMES[3],NAMES[1]],0),('forward',[NAMES[1],NAMES[3]],7),('repeat',[NAMES[3],NAMES[1],NAMES[3]],7)]:
  build('synchronous-recipient-order-'+label,[(0,E('mark','buff','',0,targets,event_scope='recipients')),(1,E('gate','buff','',0,NAMES[3],event='event:mark')),(3,buff('ordered','self',event='event:mark',condition=['self_state:gate']))],expected=[0,0,0,value,0])
 build('twenty-one-recipient-events-cross-32-bit-boundary',[(0,E('mark','buff','',0,['self']*21,event_scope='recipients')),witness(0,1)],expected=[21,0,0,0,0])
 build('nested-list-and-empty-leaves-keep-order',[(0,E('mark','buff','',0,[[],[NAMES[1],[NAMES[3],[]]],NAMES[1]],event_scope='recipients')),witness(1,2),witness(3,3)],expected=[0,4,0,3,0])
 build('state-filter-list-does-not-double-buff-overlap',[(0,E('mark','buff','',0,'all_allies')),(0,buff('list',['allies_with_buff:mark','self']))],expected=[7]*5)
 build('list-partial-removal-retains-other-recipient',[(0,buff('mark',['self','self',NAMES[1]])),(0,E('remove','instant','remove_named_buff',0,event='burst_cast',target_effect='mark',remove_scope='target'))],commands=[(.1,3,0)]+[(.2,'query',i) for i in range(5)],expected=[0,7,0,0,0])
 build('shield-map-emits-once-per-unique-recipient',[(0,E('shield','buff','shield_from_max_hp_pct',10,['self','self'])),(0,E('witness','buff','atk_pct',1,event='event:shield_applied',max_stack=100))],expected=[1,0,0,0,0])
 build('stat-applied-events-retain-duplicate-recipients',[(0,E('split','buff','split_dmg_pct',10,['self','self'])),(0,E('witness','buff','atk_pct',3,event='event:stat_applied:split_dmg_pct',max_stack=100))],expected=[6,0,0,0,0])
 build('default-name-event-broadcast-is-once-per-squad-member',[(0,E('mark','buff','',0,['self','self'])),witness(0,1)],expected=[1,0,0,0,0])
 build('same-recipient-set-different-order-stays-two-states',[(0,buff('same',[NAMES[0],NAMES[1]])),(0,buff('same',[NAMES[1],NAMES[0]]))],expected=[14,14,0,0,0])
 build('same-recipient-order-aliases-across-definitions',[(0,buff('same',[NAMES[0],NAMES[1]])),(0,buff('same',[NAMES[0],NAMES[1]]))],expected=[7,7,0,0,0])
 return out

def full_scenarios():
 n=NAMES
 yield 'full-duplicate-heal-order-and-live-caster-hp',{n[0]:[E('room','buff','max_hp_only_pct',100,'all_allies'),E('heal','instant','heal_hp_pct',1,[n[1],n[3],n[1]],event='every:1s',scaling='max_hp')],n[1]:[E('caster hp grows','buff','max_hp_only_pct',5,n[0],event='event:heal_received',max_stack=30)],n[3]:[E('witness','buff','atk_pct',5,event='event:heal_received',max_stack=20)]},10
 yield 'full-duplicate-current-hp-reduction',{n[0]:[E('drain','instant','current_hp_reduce',10,[n[2],n[2]],event='every:1s')],n[2]:[E('hp gate','buff','atk_pct',50,event='passive',condition=['self_hp_below:80'])]},10
 yield 'full-duplicate-hp-buff-postprocessing',{n[0]:[E('drain','instant','current_hp_reduce',30,'all_allies'),E('hp','buff','max_hp_pct',10,['self','self'])]},4
 yield 'full-duplicate-ammo-operations',{n[0]:[E('ammo','instant','ammo_charge_pct',7,[n[2],n[2],n[3]],event='every:0.5s'),E('flat remove','instant','ammo_charge_flat',-2,[n[3],n[3]],event='every:1s')]},10
 yield 'full-duplicate-burst-cooldown-reduction',{n[0]:[E('cooldown','instant','burst_cooldown_reduce',2,[n[0],n[0],n[1]],event='on_attack_count:15')]},35
 yield 'full-state-list-overlapping-instance-lifetimes',{n[0]:[E('mark','buff','',0,n[3],event='every:2s',duration=1),E('overlap','buff','atk_pct',20,['allies_with_buff:mark','self'],event='every:0.5s',duration=3,max_stack=3)]},12
 yield 'full-list-bullet-refresh-and-consumption',{n[0]:[E('shots','buff','atk_pct',25,[n[2],n[2],n[3]],event='on_attack_count:3',duration_bullets=2,max_stack=3)]},10
 yield 'full-list-skill-clock-reduction-deduplicates',{n[0]:[E('pulse','buff','atk_pct',1,'all_allies',event='every:4s',duration=10,max_stack=20),E('reduce','instant','skill_cooldown_reduce_pct',50,['self','self'],event='every:1s')]},10

def verify(device,backend='auto',include_real=True):
 out=[]
 for name,p,script,expected in primitives():
  bs={n:{'atk':100000+i*10000,'hp':1000000,'def':1000} for i,n in enumerate(NAMES)};cpu,totals=oracle.oracle(p,script,[31784,50],bs);gpu=run(device,[p],script,[[31784,50]],[bs],module_backend=backend);errors=[]
  assert len(cpu)==len(expected)==len(gpu['queries'][0])
  for i,(x,y,z) in enumerate(zip(cpu,gpu['queries'][0],expected)):
   if x[0]!=z or y[0]!=z:errors.append([i,'expected atk',z,x[0],y[0]])
   for k in list(range(32))+[36,37]:
    if not math.isclose(x[k],y[k],rel_tol=1e-12,abs_tol=1e-8):errors.append([i,k,x[k],y[k]])
  c={'name':name,'passed':not errors and totals==gpu['totals'][0],'errors':errors,'backend':backend};out.append(c);print(json.dumps(c),flush=True)
 for name,effects,seconds in full_scenarios():
  with periodic.custom_effects(effects):c=periodic.full.compare(device,name,body_for(NAMES,seconds,True),module_backend=backend)
  if name=='full-duplicate-hp-buff-postprocessing':
   # With 30% lost HP, two +10% current-HP posts give 90% of base HP.
   n=NAMES[0];c['duplicate_hp_posts_exercised']=math.isclose(c['cpu_health'][n]['hp']/c['cpu_health'][n]['max_hp'],.9/1.1,rel_tol=1e-12);c['passed'] &= c['duplicate_hp_posts_exercised']
  c['backend']=backend;out.append(c);print(json.dumps({'name':name,'passed':c['passed'],'cpu':c['cpu_total'],'gpu':c['gpu_total']}),flush=True)
 if include_real:
  before=json.loads((ROOT/'research/detail-coverage-targets.json').read_text(encoding='utf-8'));was={r['character'] for r in before['results'] if r['supported']}
  for r in coverage()['results']:
   if not r['supported'] or r['character'] in was:continue
   name=r['character'];names=[name]+[n for n in NAMES if n!=name][:4];c=periodic.full.compare(device,'real-'+name,body_for(names,60,True),module_backend=backend);c['backend']=backend;out.append(c);print(json.dumps({'name':name,'passed':c['passed'],'cpu':c['cpu_total'],'gpu':c['gpu_total']},ensure_ascii=True),flush=True)
 return out

if __name__=='__main__':
 device=Cuda()
 try:cases=verify(device,'native')+verify(device,'ptx')
 finally:device.close()
 files=['app/detail_gpu.py','app/detail_effects.cu','app/detail_effects.ptx','app/detail_effects-build.json','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','scripts/verify-lists-detail.py']
 report={'generated_at':datetime.now(timezone.utc).isoformat(),'passed':all(c['passed'] for c in cases),'cases':cases,'cpu_trace_used_as_gpu_input':False,'scope':'ordered/duplicate friendly target lists within 21 recipients and 128 total definition rows, static boss; not all effects/characters/combinations','source_sha256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files}}
 (ROOT/'research/detail-lists-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');raise SystemExit(0 if report['passed'] else 1)
