"""CPU-only witnesses for the authored zero-stack and real persona stimuli.
These observations are verification output, never GPU simulation input.
"""
import sys,importlib.util,json,hashlib
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
spec=importlib.util.spec_from_file_location('stimuli_predicate_oracle',ROOT/'scripts/verify-predicates-detail.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
from calculator.buff_manager import BuffManager

def verify():
 original=BuffManager._resolve_target_raw;records=[]
 for name,p,script,expected in v.primitives():
  seen=[]
  def tracked(manager,target,caster):
   result=original(manager,target,caster)
   if target=='allies_burst3_persona_excl_self':seen.append({'selected':list(result),'markers':[{'stack':ab.stack,'recipients':ab.target_chars} for ab in manager._active if ab.effect.get('stat')=='persona_state']})
   return result
  bs={n:{'atk':100000+i*10000,'hp':1000000,'def':1000+i*100} for i,n in enumerate(v.NAMES)}
  with patch.object(BuffManager,'_resolve_target_raw',tracked):cpu,totals=v.oracle.oracle(p,script,[31784,50],bs)
  assert len(cpu)==len(expected) and all(x[0]==z for x,z in zip(cpu,expected)),name
  if name=='zero-stack-persona-marker-still-counts':assert any(m['stack']==0 and m['recipients'] for s in seen for m in s['markers'])
  records.append({'name':name,'passed':True,'observations':seen})
 body=v.body_for(['퀸(마코토)','유키코','아이기스','루주','마스트 : 로망틱 메이드'],60,True);seen=[]
 def traced_real(manager,target,caster):
  result=original(manager,target,caster)
  if target=='allies_burst3_persona_excl_self':seen.append({'caster':caster,'selected':list(result)})
  return result
 with patch.object(BuffManager,'_resolve_target_raw',traced_real):result=v.periodic.a.evaluate(body)
 assert result['total_damage']==997057331 and any(s['selected'] for s in seen)
 assert all(s['caster'] not in s['selected'] for s in seen)
 files=['scripts/verify-predicate-stimuli.py','scripts/verify-predicates-detail.py','app/detail_gpu.py','app/engine_compat.py','research/upstream/nikke-calc-master/calculator/buff_manager.py']
 return {'passed':True,'cpu_trace_used_as_gpu_input':False,'scope':'CPU-only proof that authored zero-stack marker and real cross-character persona selection actually occur','primitives':records,'real_persona':{'cpu_total':result['total_damage'],'selections':seen},'source_sha256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files}}

if __name__=='__main__':
 report=verify();(ROOT/'research/detail-predicate-stimuli.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({'passed':True,'primitive_witnesses':len(report['primitives']),'real_persona_selections':len(report['real_persona']['selections'])}))
