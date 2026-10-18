"""Named/generic stack operations against independent CPU state and full squads."""
import copy,hashlib,importlib.util,json,math,sys
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from gpu_selector import Cuda
from detail_gpu import run
from detail_coverage import body_for
s=importlib.util.spec_from_file_location('stack_instance_oracle',ROOT/'scripts/verify-instances-detail.py');base=importlib.util.module_from_spec(s);s.loader.exec_module(base)
E=base.E;NAMES=base.NAMES;oracle=base.oracle;periodic=base.periodic

def primitives():
 out=[]
 def build(name,effects,events,checks):
  p=oracle.program(oracle.characters(NAMES),[(e,NAMES[i]) for i,e in effects]);script=[[0,0,0,i,0,-1,0,0] for i in range(5)]
  commands=[(t,0,ev,who,-1) for t,ev,who in events]+[(t,2,0,who,i) for i,(t,who,atk,ref) in enumerate(checks)]
  for t,op,ev,who,i in sorted(commands,key=lambda x:(x[0],x[1])):script.append([t,op,ev,who,p['states']['state'] if op==2 else 0,i,0,0])
  out.append((name,p,script,checks))
 def source(**kw):return E('state','buff','atk_pct',10,**({'duration':1,'max_stack':3,'polarity':'beneficial'}|kw))
 def op(stat,value=1,event='burst_cast',target='self',**kw):return E('operation '+stat,'buff' if stat=='buff_max_stack_add' else 'instant',stat,value,target,event=event,**({} if stat=='buff_max_stack_add' else {'target_effect':'state'}),**kw)
 build('named-add-refreshes-at-cap-remove-keeps-one',[(0,source()),(0,op('buff_stack_add',2,target='N102')),(0,op('buff_stack_remove',9,event='on_attack'))],[(.5,3,0),(1.2,3,0),(1.3,7,0)],[(.6,0,30,3),(1.1,0,30,3),(1.4,0,10,1),(2.21,0,0,0)])
 src=source();src['trigger']['timing']=['battle_start','on_attack']
 build('generic-add-at-cap-does-not-refresh-expiry',[(0,src),(0,op('buff_max_stack_add',2))],[(.1,7,0),(.5,3,0)],[(.2,0,20,2),(.6,0,30,3),(1.11,0,30,3),(1.51,0,0,0)])
 # Reach cap before generic add; a later call must leave its expiry untouched.
 src=source(max_stack=2);src['trigger']['timing']=['battle_start','on_attack']
 build('generic-cap-no-op-is-not-a-duration-refresh',[(0,src),(0,op('buff_max_stack_add',2))],[(.1,7,0),(.5,3,0)],[(.6,0,20,2),(1.11,0,0,0)])
 src=source(event='on_attack',max_stack=5,max_trigger=0,condition=['during_full_burst'],duration_values={'10':5})
 witnesses=[E('name witness','buff','crit_dmg',11,event='event:state'),E('reach witness','buff','crit_dmg',13,event='stack_reach:state:4')]
 build('init-bypasses-gate-budget-and-emits-no-name-or-reach',[(0,src),(0,op('buff_stack_init',4)),*[(0,e) for e in witnesses]],[(.1,3,0),(.2,3,0)],[(.15,0,40,4),(.3,0,40,4),(1.11,0,0,0)])
 src=source(event='on_attack',target='allies_top_atk:1',max_stack=2,duration=2)
 build('lazy-init-appends-separate-unresolved-instances',[(0,src),(0,op('buff_stack_init',2))],[(.1,3,0),(.2,3,0)],[(.3,4,40,0),(.3,0,0,2)])
 src=source(target='all_allies')
 build('generic-add-skips-mixed-recipient-instance',[(0,src),(0,op('buff_max_stack_add',2)),(1,op('buff_max_stack_add',2,event='on_attack',target='all_allies'))],[(.1,3,0),(.2,7,1)],[(.15,0,10,1),(.25,0,30,3),(.25,4,30,0)])
 immune=E('immune','buff','stack_change_immune',0,event='passive',condition=['during_full_burst'])
 build('false-permanent-immune-still-blocks-stack-changes',[(0,source(target='all_allies')),(0,immune),(0,op('buff_stack_add',2)),(1,op('buff_max_stack_add',2,event='on_attack',target='all_allies'))],[(.1,3,0),(.2,7,1)],[(.3,0,10,1),(.3,1,10,0)])
 immune=E('immune','buff','stack_change_immune',0,duration=.3)
 build('zero-valued-immune-expires-and-allows-later-change',[(0,source()),(0,immune),(0,op('buff_stack_add',2))],[(.1,3,0),(.4,3,0)],[(.2,0,10,1),(.5,0,30,3)])
 src=source(max_stack=4);src['trigger']['timing']=['battle_start','on_attack']
 watch=E('still present','buff','crit_dmg',11,event='passive',condition=['self_state:state'])
 build('named-debuff-zero-remains-present-and-blocks-init',[(0,src),(0,op('debuff_stack_remove',3,event='hit_count:1')),(0,op('buff_stack_init',3)),(0,watch)],[(.1,8,0),(.2,3,0),(.3,7,0)],[(.15,0,0,0),(.25,0,0,0),(.35,0,10,1)])
 src=source(max_stack=1);src['trigger']['timing']=['battle_start','on_attack']
 build('single-stack-buff-reapplication-retains-zero-stack',[(0,src),(0,op('debuff_stack_remove',1,event='hit_count:1')),(0,watch)],[(.1,8,0),(.2,7,0)],[(.15,0,10,0),(.25,0,10,0)])
 src=source(max_stack=4,polarity='harmful');src['trigger']['timing']=['battle_start','on_attack']
 generic=E('generic remove','instant','debuff_stack_remove',9,event='burst_cast')
 build('generic-debuff-floor-one-named-floor-zero',[(0,src),(0,generic),(0,op('debuff_stack_remove',9,event='hit_count:1'))],[(.01,7,0),(.02,7,0),(.1,3,0),(.2,8,0)],[(.05,0,30,3),(.15,0,10,1),(.25,0,0,0)])
 enemy=E('state','buff','def_pct',-10,'target',duration=1,max_stack=3,polarity='harmful')
 build('enemy-debuff-zero-keeps-target-state-present',[(0,enemy),(0,op('debuff_stack_remove',1,target='target')),(0,E('enemy remains','buff','crit_dmg',17,event='passive',condition=['target_state:state']))],[(.1,3,0)],[(.05,0,0,1),(.15,0,0,0)])
 drain=op('debuff_stack_remove',9,event='hit_count:1',scaling='stack_count',scaling_ref='fuel')
 build('gauge-zero-overrides-default-delta',[(0,source()),(0,E('fuel','instant','gauge_charge',0,gauge_id='fuel')),(0,E('charge fuel','instant','gauge_charge',2,event='burst_cast',gauge_id='fuel')),(0,drain)],[(.1,8,0),(.2,3,0),(.3,8,0)],[(.15,0,10,1),(.35,0,0,0)])
 a=source(target='all_allies');b=source(target='all_allies')
 remove=E('remove all','instant','remove_named_buff',0,event='stack_reach:state:2',target_effect='state')
 witness=E('latched callback','buff','atk_pct',7,event='stack_reach:state:2',condition=['not_self_state:state'])
 build('all-stacks-updated-before-latched-reach-callbacks',[(0,a),(1,b),(0,op('buff_stack_add',1)),(0,remove),(1,witness)],[(.1,3,0)],[(.2,0,0,0),(.2,1,7,0)])
 src=source(target='all_allies',duration_bullets=3)
 build('generic-add-updates-bullet-stacks-even-representative-at-cap',[(0,src),(0,op('buff_stack_add',2)),(0,op('buff_max_stack_add',1,event='on_attack',target='all_allies'))],[(.1,3,0),(.2,7,0),(.3,7,0)],[(.15,0,10,3),(.25,0,20,3),(.35,0,30,3),(1.11,0,0,0)])
 src=source(event='on_attack',duration=2,duration_values={'10':-1},condition=['during_full_burst'])
 build('init-uses-raw-finite-lifetime-for-runtime-gating',[(0,src),(0,op('buff_stack_init',2))],[(.1,3,0)],[(.2,0,20,2),(2.11,0,0,0)])
 build('enemy-stun-does-not-disable-squad-actions',[(0,E('state','buff','stun',1,'target',duration=1))],[],[(.1,0,0,1),(.1,1,0,0)])
 src=source(event='on_attack',duration=None,duration_values={'10':5},condition=['during_full_burst'])
 other=source(event='on_attack',duration=5)
 build('init-permanent-runtime-condition-prevents-cross-definition-merge',[(0,src),(0,other),(0,op('buff_stack_init',2))],[(.1,3,0),(.3,7,0)],[(.2,0,0,2),(.4,0,10,2),(5.31,0,0,2)])
 src=source(duration=2,scaling='stack_count',scaling_ref='fuel')
 build('missing-capture-stays-dynamic-after-name-creates-reference',[(0,src),(0,E('fuel created','instant','gauge_charge',3,event='event:state',gauge_id='fuel'))],[],[(.1,0,30,1)])
 src=source(event='on_attack',duration=None,duration_values={'10':5},condition=['during_full_burst'])
 build('runtime-enabled-at-init-persists-through-finite-refresh',[(0,src),(0,op('buff_stack_init',2))],[(.1,3,0),(.2,1,0),(.3,7,0),(.4,2,0)],[(.15,0,0,2),(.25,0,20,2),(.35,0,30,3),(.45,0,0,3)])
 src=source(event='on_attack',duration=2,duration_values={'10':-1},condition=['during_full_burst'])
 build('runtime-disabled-at-init-persists-through-permanent-alias-refresh',[(0,src),(0,source(event='on_attack',duration=-1)),(0,op('buff_stack_init',2))],[(.1,3,0),(.2,1,0),(.3,7,0),(.4,2,0)],[(.15,0,20,2),(.35,0,30,3),(.45,0,30,3),(10,0,30,3)])
 return out

def full_scenarios():
 n=periodic.NAMES
 src=E('state','buff','atk_pct',11,'all_allies',event='on_attack_count:3',duration=1.1,max_stack=4,polarity='beneficial')
 yield 'full-named-add-remove-and-partial-instances',{n[0]:[src,E('scope','instant','remove_named_buff',0,event='every:0.35s',target_effect='state',remove_scope='target')],n[1]:[E('add','instant','buff_stack_add',2,event='every:0.4s',target_effect='state'),E('remove','instant','buff_stack_remove',1,event='every:0.7s',target_effect='state')]},8
 yield 'full-zero-presence-ref-hit-count-and-init',{n[0]:[E('state','buff','atk_pct',10,event='on_attack_count:3',duration=2,max_stack=4),E('zero','instant','debuff_stack_remove',99,event='every:0.3s',target_effect='state'),E('init','instant','buff_stack_init',3,event='every:0.2s',target_effect='state'),E('reference damage','damage','damage:state',100,'target',event='on_attack_count:4'),E('present','buff','atk_dmg_pct',33,event='passive',condition=['self_state:state'])]},8
 yield 'full-bullet-map-stacks-independent-of-representative',{n[0]:[E('state','buff','atk_pct',10,'all_allies',event='on_attack_count:3',max_stack=4,duration_bullets=2,polarity='beneficial')],n[1]:[E('raise rep','instant','buff_stack_add',9,event='every:0.15s',target_effect='state')],n[4]:[E('raise maps','buff','buff_max_stack_add',1,'all_allies',event='every:0.2s')]},8
 yield 'full-init-has-no-health-shield-or-named-posts',{n[0]:[E('state','buff','max_hp_pct',50,'all_allies',event='on_attack',max_trigger=0,duration=30,max_stack=4),E('init','instant','buff_stack_init',3,event='burst_cast',target_effect='state'),E('name witness','buff','atk_pct',70,'all_allies',event='event:state')],n[1]:[E('shield','buff','shield_from_max_hp_pct',10,'all_allies',event='on_attack',max_trigger=0,duration=30,max_stack=4),E('init shield','instant','buff_stack_init',3,event='burst_cast',target_effect='shield'),E('shield witness','buff','atk_pct',70,event='passive',condition=['during_shield'])]},8
 yield 'full-beneficial-generic-add-with-shared-target-skip',{n[0]:[src],n[1]:[E('all raise','buff','buff_max_stack_add',2,'all_allies',event='every:0.4s'),E('partial raise','buff','buff_max_stack_add',2,event='every:0.3s')],n[2]:[E('immune','buff','stack_change_immune',0,duration=2)]},8
 yield 'full-stack-init-does-not-create-bullet-counters',{n[0]:[E('state','buff','atk_pct',10,'all_allies',event='on_attack',max_trigger=0,duration=30,duration_bullets=1,max_stack=4),E('init','instant','buff_stack_init',3,target_effect='state')]},8

def verify(device,backend='auto',include_real=True):
 cases=[]
 for name,p,script,checks in primitives():
  bs={n:{'atk':100000+i*10000,'hp':1000000,'def':1000} for i,n in enumerate(NAMES)};cpu,total=oracle.oracle(p,script,[31784,50],bs);gpu=run(device,[p],script,[[31784,50]],[bs],module_backend=backend);errors=[]
  for i,(x,y,expected) in enumerate(zip(cpu,gpu['queries'][0],checks)):
   for key,value in [(0,expected[2]),(37,expected[3])]:
    if x[key]!=value or y[key]!=value:errors.append([i,'expected',key,value,x[key],y[key]])
   for key in list(range(32))+[36,37]:
    if not math.isclose(x[key],y[key],rel_tol=1e-12,abs_tol=1e-8):errors.append([i,key,x[key],y[key]])
  c={'name':name,'passed':not errors and total==gpu['totals'][0],'errors':errors,'backend':backend};cases.append(c);print(json.dumps(c),flush=True)
 for name,effects,seconds in full_scenarios():
  with periodic.custom_effects(effects):c=periodic.full.compare(device,name,body_for(periodic.NAMES,seconds,True),module_backend=backend)
  c['backend']=backend;cases.append(c);print(json.dumps({'name':name,'passed':c['passed'],'cpu':c['cpu_total'],'gpu':c['gpu_total']}),flush=True)
 if include_real:
  old=json.loads((ROOT/'research/detail-coverage-instances.json').read_text(encoding='utf-8'));now=json.loads((ROOT/'research/detail-coverage-stackops.json').read_text(encoding='utf-8'));was={r['character'] for r in old['results'] if r['supported']}
  for entry in now['results']:
   name=entry['character']
   if not entry['supported'] or name in was:continue
   names=[name]+[n for n in NAMES if n!=name][:4]
   c=periodic.full.compare(device,'real-'+name,body_for(names,60,True),module_backend=backend);c['backend']=backend;cases.append(c);print(json.dumps({'name':name,'passed':c['passed'],'cpu':c['cpu_total'],'gpu':c['gpu_total']},ensure_ascii=True),flush=True)
 return cases

if __name__=='__main__':
 d=Cuda()
 try:cases=verify(d,'native')+verify(d,'ptx')
 finally:d.close()
 files=['app/detail_gpu.py','app/detail_effects.cu','app/detail_effects.ptx','app/detail_effects-build.json','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','scripts/verify-stackops-detail.py']
 report={'generated_at':datetime.now(timezone.utc).isoformat(),'passed':all(c['passed'] for c in cases),'cpu_trace_used_as_gpu_input':False,'scope':'authored stack operations, independent full squads, and newly accepted real characters in fixed static-boss squads; not all characters or combinations','cases':cases,'source_sha256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files}}
 (ROOT/'research/detail-stackops-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');raise SystemExit(0 if report['passed'] else 1)
