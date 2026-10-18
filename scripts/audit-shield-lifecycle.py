"""CPU shield subsystem references from authored effects/absorption operations.
Amounts returned by CPU are oracle outputs, never inputs to a future GPU run.
"""
import copy,hashlib,importlib.util,json,math,random,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
spec=importlib.util.spec_from_file_location('shield_cpu',ROOT/'scripts/audit-debuff-cleanse.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
E=v.E;NAMES=v.NAMES

def scenarios():
 def shield(name,stat,target='all_allies',**kw):return E(name,'buff',stat,25,target,duration=60,**kw)
 for first,second in [('shield_from_max_hp_pct','shield_from_max_hp_pct'),('shared_shield_from_max_hp_pct','shared_shield_from_max_hp_pct'),('shield_from_max_hp_pct','shared_shield_from_max_hp_pct'),('shared_shield_from_max_hp_pct','shield_from_max_hp_pct')]:
  effects={NAMES[0]:[shield('old shield',first)],NAMES[1]:[shield('new shield',second,event='every:0.5s',max_trigger=1)]}
  for pierce in (False,True):
   yield first+'-'+second+('-pierce' if pierce else '-ordinary'),effects,[('absorb',0,100000,pierce),('absorb',1,100000,pierce),('absorb',0,1e9,pierce),('heal',0,200000,False)]
 for end in (False,True):
  effects={NAMES[0]:[shield('shared carrier','shared_shield_from_max_hp_pct',end_on_shield_consumed=end),E('ended probe','buff','atk_pct',1,event='event:state_end:shared carrier',max_stack=10)]}
  yield 'carrier-'+('end-after-all-recipients' if end else 'retained-after-zero'),effects,[('absorb',i,1e9,False) for i in range(5)]+[('heal',0,1e9,False)]
 for owner in (0,1):
  effects={NAMES[0]:[shield('protected shield','shield_from_max_hp_pct')],NAMES[owner]:[E('shield protection','buff','shield_invincible',1)]}
  # Keep the shield when marker owner and shield owner are the same.
  if owner==0:effects[NAMES[0]].insert(0,shield('protected shield','shield_from_max_hp_pct'))
  yield 'invincibility-owner-'+str(owner),effects,[('absorb',0,1e9,False),('absorb',1,1e9,False)]
 effects={NAMES[0]:[E('next shield amp','buff','next_shield_hp_pct',50,'all_allies'),shield('first consumes amp','shared_shield_from_max_hp_pct'),shield('second unamplified','shield_from_max_hp_pct')]}
 yield 'next-amplifier-consumed-per-recipient',effects,[('absorb',0,100000,True),('heal',0,1e9,False)]
 effects={NAMES[0]:[E('lazy next shield amp','buff','next_shield_hp_pct',50,'allies_random:1'),shield('random amp consumer','shared_shield_from_max_hp_pct')]}
 yield 'lazy-random-amplifier-resolves-on-first-shield',effects,[('absorb',0,100000,False)]
 effects={NAMES[0]:[shield('refreshed shield','shared_shield_from_max_hp_pct'),E('conditional amp','buff','next_shield_hp_pct',50,'all_allies',event='every:0.5s',max_trigger=1,condition=['during_shield']),shield('refreshed shield','shared_shield_from_max_hp_pct',event='every:1s',max_trigger=1)]}
 yield 'refresh-amplifier-sees-old-positive-shield',effects,[('tick',0,1.1,False)]
 effects={NAMES[0]:[shield('externally protected shield','shared_shield_from_max_hp_pct')],NAMES[2]:[E('protection from another caster','buff','shield_invincible',1,NAMES[0])]}
 yield 'maker-protected-by-another-caster',effects,[('absorb',0,1e9,True),('absorb',1,1e9,False)]
 effects={NAMES[0]:[shield('stack shield','shared_shield_from_max_hp_pct',max_stack=5)]}
 yield 'stack-add-does-not-rebuild-capacity',effects,[('addstack',0,2,False),('absorb',0,100000,False),('heal',0,1e9,False)]
 effects={NAMES[0]:[E('expires shield','buff','shared_shield_from_max_hp_pct',25,'all_allies',duration=1.5)]}
 yield 'expiration-removes-shield-maps-with-carrier',effects,[('tick',0,2,False),('absorb',0,100000,False)]
 effects={NAMES[0]:[shield('refreshable','shared_shield_from_max_hp_pct',event='battle_start'),E('on break refresh','buff','shared_shield_from_max_hp_pct',50,'all_allies',event='event:shield_consumed',duration=60)]}
 yield 'synchronous-consumed-callback-creates-shield',effects,[('absorb',0,1e9,False),('absorb',1,100000,False)]
 for scope in ('target','global'):
  effects={NAMES[0]:[shield('strip shield','shared_shield_from_max_hp_pct')]}
  yield 'named-removal-'+scope,effects,[('remove',0,scope,False),('absorb',0,100000,False),('absorb',1,100000,False)]

def snapshot(bm):
 return dict(entries=[dict(uid=ab.uid,name=ab.effect.get('name'),caster=ab.caster,targets=copy.deepcopy(ab.target_chars),stack=ab.stack,shield=copy.deepcopy(ab.shield_per_target),capacity=copy.deepcopy(ab.shield_max_per_target)) for ab in bm._active if ab.effect.get('stat') in ('shield_from_max_hp_pct','shared_shield_from_max_hp_pct','next_shield_hp_pct')],
             amount={n:bm.shield_amount(n) for n in NAMES},capacity={n:bm.shield_capacity(n) for n in NAMES},has_shield={n:bm.has_shield(n) for n in NAMES},ended_probe=[ab.stack for ab in bm._active if ab.effect.get('name')=='ended probe'])

def main():
 cases=[]
 for label,effects,operations in scenarios():
  body=v.c.body_for(NAMES,1,True);body['seed']=0
  with v.c.p.custom_effects(effects),v.c.observe() as (_,manager,_):cpu=v.c.a.evaluate(body)
  bm=manager['bm'];steps=[];before=snapshot(bm);t=1.1
  for op,who,value,pierce in operations:
   if op=='absorb':returned=bm.absorb_shield(NAMES[who],value,t,pierce=pierce)
   elif op=='heal':returned=bm.heal_shield(NAMES[who],value,t)
   elif op=='remove':
    e=E('remove shield','instant','remove_named_buff',0,NAMES[who],target_effect='strip shield',remove_scope=value)
    returned=bm._dispatch_instant(e,NAMES[who],t)
   elif op=='addstack':returned=bm._dispatch_instant(E('add shield stack','instant','buff_stack_add',value,'self',target_effect='stack shield'),NAMES[who],t)
   else:t=float(value);returned=bm.tick(t)
   after=snapshot(bm);assert all(x>=0 for x in after['amount'].values())
   steps.append(dict(time=t,operation=op,recipient=NAMES[who],value=value,pierce=pierce,returned=returned,after=after));t+=.1
  cases.append(dict(name=label,input=body,authored_effects=effects,authored_operations=operations,initial=before,steps=steps,final_random_state=list(random.getstate()[1]),cpu_total=cpu['total_damage'],members=cpu['members']))
  print(json.dumps(dict(name=label,operations=len(steps),initial_shields=len(before['entries']),last_amount=steps[-1]['after']['amount']),ensure_ascii=True),flush=True)
 by_name={r['name']:r for r in cases}
 for row in cases[:8]:
  assert row['steps'][0]['returned']==(200000 if row['authored_operations'][0][3] else 100000)
  assert row['steps'][0]['after']['amount'][NAMES[2]]==row['initial']['amount'][NAMES[2]]
 ended=by_name['carrier-end-after-all-recipients'];kept=by_name['carrier-retained-after-zero']
 assert not ended['steps'][3]['after']['ended_probe'] and ended['steps'][4]['after']['ended_probe']==[1]
 assert ended['steps'][-1]['returned']==0 and not ended['steps'][-1]['after']['entries']
 assert kept['steps'][-1]['returned']>0 and not kept['steps'][-1]['after']['ended_probe']
 for label in ('invincibility-owner-0','maker-protected-by-another-caster'):
  row=by_name[label];assert row['steps'][0]['returned']==1e9 and row['steps'][-1]['after']['amount']==row['initial']['amount']
 assert by_name['invincibility-owner-1']['steps'][0]['after']['amount'][NAMES[0]]==0
 row=by_name['stack-add-does-not-rebuild-capacity'];assert row['steps'][0]['after']['capacity']==row['initial']['capacity'] and row['steps'][0]['after']['entries'][0]['stack']==3
 row=by_name['lazy-random-amplifier-resolves-on-first-shield'];values=list(row['initial']['amount'].values());assert sum(x==max(values) for x in values)==1 and math.isclose(max(values),min(values)*1.5)
 row=by_name['named-removal-target'];assert NAMES[0] not in row['steps'][0]['after']['entries'][0]['targets'] and row['steps'][0]['after']['amount'][NAMES[0]]==row['initial']['amount'][NAMES[0]]
 assert not by_name['expiration-removes-shield-maps-with-carrier']['steps'][0]['after']['entries']
 files=['scripts/audit-shield-lifecycle.py','research/upstream/nikke-calc-master/calculator/buff_manager.py','app/engine_worker.py']
 report=dict(generated_at=datetime.now(timezone.utc).isoformat(),cpu_reference_only=True,gpu_implemented=False,cpu_trace_used_as_gpu_input=False,semantic_assertions_passed=True,cases=cases,
             scope='Authored shield absorption/heal subsystem inputs, not a complete incoming boss-attack simulation. Pinned shared shield stat currently uses independent recipient maps.',source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files})
 (ROOT/'research/detail-shield-lifecycle-cpu-references.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
if __name__=='__main__':main()
