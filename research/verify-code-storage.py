"""Static equality of shared declarations and reuse of alignment padding."""
import hashlib,json,re,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'app'))
from portable_specs import ABI,LIMITS as L
source=(R/'gpu/event_runtime.slang').read_text();old=subprocess.check_output(['git','show','ed68e68:gpu/event_runtime.slang'],cwd=R,text=True);rows={}
for name in ('Runtime','Definition','Frame'):
    pattern=r'struct '+name+r'\s*\{.*?\n\};';before=re.search(pattern,old,re.S).group();after=re.search(pattern,source,re.S).group();assert before==after,name
    rows[name]=dict(declaration_unchanged=True,sha256=hashlib.sha256(after.encode()).hexdigest())
assert ABI==0x5045566A and (L['INPUT_WORDS'],L['OUTPUT_WORDS'])==(86016,159744)
assert L['WORLD_META_BASE']==L['AIM_POLICY_BASE']+1 and L['WORLD_META_WORDS']==7 and L['WORLD_META_BASE']+7==L['PERIODIC_DEFINITION_BASE']
x=dict(passed=True,source_commit='dd7d62b98a63f9fa99892dd964809775b136a9d6',wire_abi=hex(ABI),prior_source='ed68e68',input_words=L['INPUT_WORDS'],output_words=L['OUTPUT_WORDS'],input_stride_growth_words=0,output_stride_growth_words=0,added_runtime_arrays=0,added_runtime_scalars=0,added_definition_fields=0,added_frame_fields=0,declarations=rows,world_metadata=dict(base=L['WORLD_META_BASE'],words=7,used_words=2,storage_origin='Previously zero alignment padding after the aim policy'),scope='Static shared declarations and wire layout only; no compiler register/spill,physical private storage or peak-memory measurement.')
(R/'research/portable-enemy-code-storage.json').write_text(json.dumps(x,indent=2)+'\n');print('Shared declarations and input/output strides unchanged')
