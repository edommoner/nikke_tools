"""Fixed-v41 compiler control (system shader cache may apply); not certification of the current candidate."""
import array,hashlib,importlib.util,io,json,struct,subprocess,sys,tarfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from portable_backend import execute
from portable_runtime import pack_programs,decode
from portable_specs import LIMITS as L
BASE='70f90181245ff1ca5d0930bc2e332762d99ebde1';directory=ROOT/'research/portable-build/control-v41';directory.mkdir(parents=True,exist_ok=True)
raw=subprocess.check_output(['git','archive',BASE,'gpu'],cwd=ROOT)
with tarfile.open(fileobj=io.BytesIO(raw)) as archive:archive.extractall(directory,filter='data')
renamed='--entry-rename' in sys.argv
entry='portableV41RenamedControl' if renamed else 'portableEvents'
if renamed:
 path=directory/'gpu/event_runtime.slang';text=path.read_text();assert text.count('void portableEvents(')==1;path.write_text(text.replace('void portableEvents(','void '+entry+'('))
source=directory/('portable_v41_renamed_control.slang' if renamed else 'portable_v41_control.slang');source.write_text('#include "gpu/event_runtime.slang"\n')
sp=importlib.util.spec_from_file_location('control_case',ROOT/'scripts/verify-portable-combat.py');v=importlib.util.module_from_spec(sp);sp.loader.exec_module(v)
case=v.fixtures()[0];words,metadata=v.compile_case(case);words[0]=0x50455658
raw,evidence=execute(source.relative_to(ROOT).as_posix(),entry,pack_programs([(words,metadata)]),L['INPUT_WORDS'],L['OUTPUT_WORDS'],'metal')
output=array.array('I');output.frombytes(raw)
if sys.byteorder!='little':output.byteswap()
actual=decode(output,metadata);assert actual['status']==0;v.contains(actual['queries'],case['expected_queries'])
report=dict(passed=True,scope='One unchanged authored case at frozen v41 full kernel with a separate generated shader path; compiler/hardware control only, not current runtime verification',fixed_source_commit=BASE,entry_symbol_renamed=renamed,system_shader_cache_status='unknown',case=case['name'],actual=actual,**evidence)
(ROOT/('research/portable-v41-renamed-compiler-control.json' if renamed else 'research/portable-v41-compiler-control.json')).write_text(json.dumps(report,indent=2)+'\n');print('Frozen v41 full kernel compiler control passed',flush=True)
