"""Whole-squad parity for every character accepted by the current compiler audit.
This reports the rejected catalog too: passing this check does not mean all
characters, favorite stages, or combinations have GPU implementations.
"""
import hashlib,importlib.util,json,sys
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from detail_coverage import coverage,body_for
from gpu_selector import Cuda
spec=importlib.util.spec_from_file_location('catalog_oracle',ROOT/'scripts/verify-extended-detail.py');full=importlib.util.module_from_spec(spec);spec.loader.exec_module(full)

def verify():
 audit=coverage();cases=[];device=Cuda()
 try:
  for backend in ('native','ptx'):
   for entry in audit['results']:
    if not entry['supported']:continue
    name=entry['character'];names=[name]+[n for n in ['모더니아','루주','마스트 : 로망틱 메이드','도라','얀'] if n!=name][:4]
    try:case=full.compare(device,'catalog-'+name,body_for(names,30,True),module_backend=backend)
    except (Exception,SystemExit) as error:case={'name':name,'passed':False,'error':str(error)}
    case.update(character=name,backend=backend);cases.append(case)
    print(json.dumps({'character':name,'backend':backend,'passed':case['passed'],**({'error':case['error']} if 'error' in case else {'total':case['gpu_total']})},ensure_ascii=True),flush=True)
 finally:device.close()
 files=['app/detail_gpu.py','app/detail_effects.cu','app/detail_effects.ptx','app/detail_effects-build.json','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','scripts/verify-catalog-detail.py']
 return {'generated_at':datetime.now(timezone.utc).isoformat(),'passed':all(c['passed'] for c in cases),'catalog_characters':audit['characters'],'compiled_characters':audit['supported'],'rejected_characters':[r for r in audit['results'] if not r['supported']],'scope':'every currently compiler-accepted character in one fixed grown five-member squad, favorite zero/no cube, 30 seconds, native and PTX; not every character, favorite stage or combination','cpu_trace_used_as_gpu_input':False,'cases':cases,'source_sha256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files}}

if __name__=='__main__':
 report=verify();(ROOT/'research/detail-catalog-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');raise SystemExit(0 if report['passed'] else 1)
