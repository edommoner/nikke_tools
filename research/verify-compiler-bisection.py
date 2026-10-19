"""Single-case compiler controls. Skipped removal variants are NOT runtime proofs."""
import argparse,array,re,hashlib,importlib.util,io,json,shutil,subprocess,sys,tarfile,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from portable_backend import execute,source_hashes
from portable_runtime import pack_programs,decode
from portable_specs import LIMITS as L
p=argparse.ArgumentParser();p.add_argument('--base',default='cbddc774d9f996e9de9542519a5d851e0e99b897');p.add_argument('--label',default='');p.add_argument('--skip-removal',action='store_true');p.add_argument('--private-queue',action='store_true');a=p.parse_args()
name=('current' if a.base=='current' else 'head')+('-skip-removal' if a.skip_removal else '-full')+('-private-queue' if a.private_queue else '')
assert re.fullmatch('[a-z0-9-]*',a.label)
if a.label:name+='-'+a.label
directory=ROOT/'research/portable-build'/('bisect-'+name);directory.mkdir(parents=True,exist_ok=True)
if a.base=='current':shutil.copytree(ROOT/'gpu',directory/'gpu',dirs_exist_ok=True)
else:
 raw=subprocess.check_output(['git','archive',a.base,'gpu'],cwd=ROOT)
 with tarfile.open(fileobj=io.BytesIO(raw)) as archive:archive.extractall(directory,filter='data')
if a.skip_removal:
 path=directory/'gpu/event_runtime.slang';text=path.read_text();assert text.count('removeNamedResidents(s,row,f.target,f.time);')==1;path.write_text(text.replace('removeNamedResidents(s,row,f.target,f.time);','/* Diagnostic only: scoped removal call omitted. */'))
if a.private_queue:
 path=directory/'gpu/event_runtime.slang';text=path.read_text();needle='multiCarrier[P_DEFINITIONS], removalCount;';assert text.count(needle)==1;path.write_text(text.replace(needle,'multiCarrier[P_DEFINITIONS], removalCount; uint controlNotice[P_REMOVALS];'))
 path=directory/'gpu/carrier_runtime.slang';text=path.read_text();text=text.replace('uint at=s.resourceOutput+P_REMOVAL_QUEUE_BASE+index/2;\n    return (results[at]>>((index&1)*16))&65535;','return s.controlNotice[index];')
 old='uint index=s.removalCount++,at=s.resourceOutput+P_REMOVAL_QUEUE_BASE+index/2,shift=(index&1)*16;\n        results[at]=(results[at]&~(65535U<<shift))|((owner|(name<<3))<<shift);'
 assert old in text;text=text.replace(old,'s.controlNotice[s.removalCount++]=owner|(name<<3);');path.write_text(text)
source=directory/('bisect_'+name.replace('-','_')+'.slang');source.write_text('#include "gpu/event_runtime.slang"\n')
sp=importlib.util.spec_from_file_location('control_case',ROOT/'scripts/verify-portable-combat.py');v=importlib.util.module_from_spec(sp);sp.loader.exec_module(v)
case=v.fixtures()[0];words,metadata=v.compile_case(case)
report=dict(passed=False,gpu_execution_verified=False,scope='Compiler bisection single case; not full runtime verification',variant=name,source_sha256=source_hashes(source.relative_to(ROOT).as_posix()))
try:
 raw,evidence=execute(source.relative_to(ROOT).as_posix(),'portableEvents',pack_programs([(words,metadata)]),L['INPUT_WORDS'],L['OUTPUT_WORDS'],'metal')
 output=array.array('I');output.frombytes(raw)
 if sys.byteorder!='little':output.byteswap()
 actual=decode(output,metadata);assert actual['status']==0;v.contains(actual['queries'],case['expected_queries'])
 report.update(passed=True,case=case['name'],**evidence)
except Exception as error:report['error']=str(error)
finally:
 (ROOT/'research'/('portable-compiler-bisect-'+name+'.json')).write_text(json.dumps(report,indent=2)+'\n')
print(name,report['passed'],report.get('error',''),flush=True)
if not report['passed']:sys.exit(1)
