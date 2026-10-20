"""Retain a one-case correctness finding for original-predicate metadata."""
import array,datetime,hashlib,importlib.util,json,sys,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from portable_runtime import dispatch_programs,pack_programs,decode
from portable_target_state_oracle import observe
from portable_specs import LIMITS as L
spec=importlib.util.spec_from_file_location('alias_core',ROOT/'scripts/verify-portable-combat.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()=='36bde18ca18e64f910e9bc5baf586e6a7ba9dfee','Historical diagnostic only;do not rerun with fixed source'
assert not (ROOT/'research/portable-target-stack-alias-finding.json').exists(),'Do not overwrite the retained finding'
c=json.loads((ROOT/'research/portable-target-stack-alias-study-input.json').read_text());program=v.compile_case(c)
raw,e=dispatch_programs([program],backend='metal')
folder=ROOT/'research/portable-build'/('target-stack-alias-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));folder.mkdir(parents=True)
(folder/'input.bin').write_bytes(pack_programs([program]));(folder/'readback.bin').write_bytes(raw);(folder/'receipt.json').write_text(json.dumps(e,indent=2)+'\n')
w=array.array('I');w.frombytes(raw);actual=decode(w,program[1]);native=observe(c)
passed=actual['queries'][0]['attack_buffs']==native['queries'][0]['attack_buffs']
report=dict(passed=passed,actual=actual,native=native,capture_directory=str(folder),evidence=e,case=c,
 scope='One original-predicate alias merge correctness case;not a benchmark',cpu_trace_used_as_gpu_input=False)
(ROOT/'research/portable-target-stack-alias-finding.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print('alias metadata parity',passed,'GPU',actual['queries'][0]['attack_buffs'],'native',native['queries'][0]['attack_buffs'])
