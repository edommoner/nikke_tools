"""CPU-only control references for the next GPU port; never used as GPU inputs."""
import sys,json,copy,hashlib
from pathlib import Path
from datetime import datetime,timezone
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from detail_coverage import a,body_for
from calculator import buff_manager

def audit():
 inventory=json.loads((ROOT/'research/detail-charge-control-frontier.json').read_text(encoding='utf-8'))
 names=list(dict.fromkeys(r['character'] for r in inventory['records']));results=[]
 for subject in names:
  records=[r for r in inventory['records'] if r['character']==subject];has_hold=any(r['timings'] for r in records);has_focus=any('focusing' in r['conditions'] for r in records)
  policies=['app-auto','engine-default','own-full-burst','after-own-full-burst'] if has_hold else ['app-auto','engine-default','camera-off','camera-on'] if has_focus else ['app-auto','engine-default','own-full-burst']
  for policy in policies:
   squad=[subject]+[n for n in ['리타','크라운','앨리스','모더니아','N102'] if n!=subject][:4];body=body_for(squad,30,True);body['profile']['chars'][subject]['skill_levels']={'1':10,'2':10,'3':10}
   observed={'subject':subject,'policy':policy,'operation_auto':policy!='engine-default','post_prepare_control_override':policy in ('own-full-burst','after-own-full-burst'),'hold_events':[],'full_charge_count':0,'controls':{},'camera':None};original_prepare=a.sim.prepare;original_notify=buff_manager.BuffManager.notify
   def prepare(request):
    request=copy.deepcopy(request)
    if policy=='engine-default':request['operation']['auto']=False
    prepared=original_prepare(request)
    for c in prepared.squad:
     if c['name']!=subject:continue
     if policy=='own-full-burst':c['control']={'hold':{'policy':'own_full_burst','lead':.1}}
     if policy=='after-own-full-burst':c['control']={'hold':{'policy':'charge_hold_after_fb','lead':.1}}
     observed['controls']=copy.deepcopy(c.get('control',{}))
    if policy in ('camera-on','camera-off'):prepared.config['camera']=subject if policy=='camera-on' else ''
    observed['camera']=prepared.config.get('camera');return prepared
   def notify(self,event,t,caster,*args,**kw):
    if caster==subject:
     if event=='full_charge':observed['full_charge_count']+=1
     if event.startswith('charge_hold:'):observed['hold_events'].append({'time':t,'event':event,'charging':bool(self.state.get('charging',{}).get(subject)),'full_burst':bool(self.state.get('full_burst')),'camera':subject in self.state.get('camera',())})
    return original_notify(self,event,t,caster,*args,**kw)
   try:
    with patch.object(a.sim,'prepare',prepare),patch.object(buff_manager.BuffManager,'notify',notify):result=a.evaluate(body)
    observed.update(cpu_total=result['total_damage'],subject_damage=next(m['damage'] for m in result['members'] if m['name']==subject),bursts=result['burst_timeline'],input=body)
   except (Exception,SystemExit) as e:observed['validation_error']=str(e)
   results.append(observed);print(json.dumps({k:observed.get(k) for k in ['subject','policy','full_charge_count','hold_events','subject_damage','validation_error']},ensure_ascii=True),flush=True)
 files=['scripts/audit-charge-control.py','research/upstream/nikke-calc-master/calculator/timeline.py','research/upstream/nikke-calc-master/calculator/buff_manager.py','research/upstream/nikke-calc-master/docs/CONTROL.md']
 return {'generated_at':datetime.now(timezone.utc).isoformat(),'objective_complete':False,'scope':'CPU-only current-app auto, engine character defaults, post-prepare manual hold and camera references; no GPU implementation or parity claim. The production adapter currently forces operation.auto=True, so engine-default and explicit control cases require the documented preparation overrides.','cpu_trace_used_as_gpu_input':False,'cases':results,'source_sha256':{f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in files}}
if __name__=='__main__':
 r=audit();(ROOT/'research/detail-charge-control-cpu-references.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
