"""One common GPU session for the already-proved world regression families."""
import argparse,array,datetime,hashlib,importlib.util,json,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
from portable_backend import execute,source_hashes

def load_module(name,path):
 spec=importlib.util.spec_from_file_location(name,ROOT/path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
f=load_module('suite_frame','research/verify-world-frame.py')
e=load_module('suite_extended','research/verify-world-frame-extended.py')
z=load_module('suite_zero','research/verify-world-zero-once.py')
n=load_module('suite_notices','research/verify-world-notices.py')
SOURCE='gpu/world_frame_entry.slang'
GOLDEN=ROOT/'research/portable-world-suite-golden.json'
FIXTURES=['research/verify-world-frame.py','research/verify-world-frame-extended.py','research/verify-world-zero-once.py','research/verify-world-notices.py','app/portable_runtime.py','app/portable_specs.py','app/portable_world_schedule_specs.py','app/portable_trigger_specs.py']

def sha(data):return hashlib.sha256(data).hexdigest()
def fixture_hashes():return {p:sha((ROOT/p).read_bytes()) for p in FIXTURES}
def normalize(raw):
 text=raw.decode().replace('\r\n','\n').replace('\r','\n');text='\n'.join(x for x in text.split('\n') if not re.match(r'^\s*#line\b',x))
 return re.sub(r'(?m)^#include "[^"\n]*slang-cuda-prelude.h"','#include "slang-cuda-prelude.h"',text).encode()
def cases():
 rows=[]
 for family,module in [('frame',f),('extended',e),('zero',z),('notices',n)]:
  for case in module.fixtures():rows.append((family+':'+case['name'],f.compile_case(case)[0]))
 rows.extend(('notices-rejected:'+name,words) for name,words in n.negative_inputs())
 assert len(rows)==49
 return rows

def make_golden():
 rows=cases();proofs=[('research/portable-world-frame-metal.json',17),('research/portable-world-notices-extended-metal.json',5),('research/portable-world-zero-once-metal.json',4),('research/portable-world-notices-metal.json',23)];offset=0;expected=[];outputs=bytearray();stride=f.L['WORLD_FRAME_OUTPUT_WORDS']*4
 for path,count in proofs:
  report=json.loads((ROOT/path).read_text());assert report['passed'];evidence=report.get('evidence',report);assert evidence['source_sha256']==source_hashes(SOURCE) and evidence['gpu_execution_verified'] and evidence['backend']=='metal'
  capture=Path(report['captured']);raw=(capture/'readback.bin').read_bytes();packed=(capture/'input.bin').read_bytes();assert sha(raw)==evidence['output_sha256'] and sha(packed)==evidence['input_sha256']
  assert len(raw)==count*stride and int.from_bytes(packed[:4],'little')==count
  for i in range(count):
   name,words=rows[offset+i];input_data=array.array('I',words)
   if sys.byteorder!='little':input_data.byteswap()
   begin=4+i*f.L['WORLD_FRAME_INPUT_WORDS']*4;assert input_data.tobytes()==packed[begin:begin+len(input_data)*4]
   block=raw[i*stride:(i+1)*stride];expected.append(dict(name=name,input_sha256=sha(input_data.tobytes()),output_sha256=sha(block),status=int.from_bytes(block[:4],'little')));outputs.extend(block)
  offset+=count
 assert offset==49
 generated={backend:sha(normalize((ROOT/'research/portable-build'/('world_frame_entry.'+suffix)).read_bytes())) for backend,suffix in [('cuda','cu'),('metal','metal')]}
 golden=dict(cases=expected,source_sha256=source_hashes(SOURCE),fixture_sha256=fixture_hashes(),generated_normalized_sha256=generated,output_sha256=sha(outputs),basis_source_commit='15bcbfe9ecf7484f0b53afdf2feec7e85c97b6ad',basis='Full native fields and complete readback bytes from four independently proved Metal families;no CPU intermediate state is used as input',full_character_verified=0)
 GOLDEN.write_text(json.dumps(golden,indent=2)+'\n');print('Golden cases',offset)
