"""Static declaration/allocation proof; not compiler register or peak memory data."""
import hashlib,json,re,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'app'))
from portable_specs import LIMITS as L
old=subprocess.check_output(['git','show','b8ae1c7:gpu/event_runtime.slang'],cwd=R,text=True);new=(R/'gpu/event_runtime.slang').read_text()
def declaration(s,name):return re.search(r'struct '+name+r'\s*\{.*?\n\};',s,re.S).group()
assert declaration(old,'Runtime')==declaration(new,'Runtime')
def fields(s):
 out={}
 for kind,names in re.findall(r'(uint64_t|uint|int)\s+([^;]+);',declaration(s,'Frame')):
  for name in names.split(','):out[name.strip()]=kind
 return out
before,after=fields(old),fields(new);assert before.keys()==after.keys();assert [(n,before[n],after[n]) for n in before if before[n]!=after[n]]==[('value','uint','uint64_t')]
assert L['SPLIT_HIT_BASE']==135168 and (L['INPUT_WORDS'],L['OUTPUT_WORDS'])==(86016,159744)
x=dict(passed=True,prior_proof_commit='b8ae1c7',runtime_declaration_unchanged=True,runtime_sha256=hashlib.sha256(declaration(new,'Runtime').encode()).hexdigest(),frame_fields_added=0,frame_value_widened_from_bits=32,frame_value_widened_to_bits=64,frame_fields=after,frame_layout_estimate=dict(assumptions='4-byte uint/int,8-byte uint64 alignment, no compiler elimination',old_bytes=72,new_bytes=80,count=32,estimated_growth_bytes=256),input_words=L['INPUT_WORDS'],output_words=L['OUTPUT_WORDS'],input_growth_bytes=(L['INPUT_WORDS']-81920)*4,output_growth_bytes=(L['OUTPUT_WORDS']-135168)*4,new_regions=dict(ordered_selector_nodes_bytes=L['RECIPIENT_NODES']*8*4,additional_hit_trace_bytes=64*5*4*16*4,wide_carrier_orders_bytes=L['CARRIERS']*2*4),max_ordered_deliveries=21,scope='Wide carrier orders live in output storage only for programs with composite targets; existing Runtime arrays remain unchanged. Frame byte figures are static layout estimates, not registers/spills, physical local storage or measured peak memory.')
(R/'research/portable-split-storage.json').write_text(json.dumps(x,indent=2)+'\n');print('Split storage declarations verified')
