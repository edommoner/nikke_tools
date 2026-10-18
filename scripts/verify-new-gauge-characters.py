"""First check newly compiler-accepted characters before the broad regression set."""
import sys,json,hashlib,importlib.util
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from detail_coverage import body_for
from gpu_selector import Cuda
s=importlib.util.spec_from_file_location('new_gauge_char_oracle',ROOT/'scripts/verify-extended-detail.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
if __name__=='__main__':
 before=json.loads((ROOT/'research/detail-coverage-pre-gauges.json').read_text(encoding='utf-8'));after=json.loads((ROOT/'research/detail-coverage-after.json').read_text(encoding='utf-8'));old={r['character'] for r in before['results'] if r['supported']};names=[r['character'] for r in after['results'] if r['supported'] and r['character'] not in old];cases=[];d=Cuda()
 try:
  for n in names:
   squad=[n]+[x for x in ['모더니아','루주','마스트 : 로망틱 메이드','도라','얀'] if x!=n][:4]
   try:case=v.compare(d,n,body_for(squad,60))
   except (Exception,SystemExit) as e:case={'name':n,'passed':False,'error':str(e)}
   cases.append(case);print(json.dumps({'character':n,'passed':case['passed'],**({'error':case['error']} if 'error' in case else {'cpu':case['cpu_total'],'gpu':case['gpu_total'],'members':case['members']})},ensure_ascii=True),flush=True)
 finally:d.close()
 sources=['app/detail_gpu.py','app/detail_effects.cu','app/detail_effects.ptx','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json']
 report={'generated_at':datetime.now(timezone.utc).isoformat(),'passed':all(c['passed'] for c in cases),'cpu_trace_used_as_gpu_input':False,'cases':cases,'source_sha256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sources}}
 (ROOT/'research/detail-new-gauge-characters.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');raise SystemExit(0 if report['passed'] else 1)
