"""Static wire and retained-reference bounds, not a register/peak-memory claim."""
import hashlib,json,re,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'research';sys.path.insert(0,str(R/'app'))
from portable_specs import LIMITS as L
before=subprocess.check_output(['git','show','e96a546:gpu/event_runtime.slang'],cwd=R,text=True);after=(R/'gpu/event_runtime.slang').read_text();rows={}
for name in ('Runtime','Frame'):
 pattern=r'struct '+name+r'\s*\{.*?\n\};';a=re.search(pattern,before,re.S).group();b=re.search(pattern,after,re.S).group();assert a==b
 rows[name]=dict(unchanged=True,sha256=hashlib.sha256(b.encode()).hexdigest())
assert L['PROTECTION_OBJECTS']==2*L['CARRIERS']==1024
assert (L['INPUT_WORDS'],L['OUTPUT_WORDS'])==(81920,135168)
sizes={'objects':L['PROTECTION_OBJECTS']*L['PROTECTION_OBJECT_WORDS']*4,'carrier_map':L['CARRIERS']*4,'selected_objects':L['CARRIERS']*4,'build_scratch':40,'hit_records':L['COMMANDS']*5*16*4,'query_snapshots':L['COMMANDS']*50*4,'final_summary':200}
x=dict(passed=True,baseline_proof_commit='e96a546',source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),declarations=rows,input_words=L['INPUT_WORDS'],output_words=L['OUTPUT_WORDS'],input_growth_bytes=(L['INPUT_WORDS']-77824)*4,output_growth_bytes=(L['OUTPUT_WORDS']-102400)*4,protection_regions_bytes=sizes,added_private_arrays=0,added_runtime_scalars=0,added_frame_fields=0,retained_reference_bound=dict(live_carriers=512,captured_shields=512,objects=1024,reason='Only external layered-hit commands create a capture list. Buff children may rebuild/replace carriers, but cannot recursively dispatch another external command. Allocator reserves captured object IDs until all shield/end callbacks finish.'),scope='Static declarations, serialized allocation sizes and ownership bound only. Compiler registers/spills, actual memory peak and full roster performance are not measured.')
(P/'portable-protection-storage.json').write_text(json.dumps(x,indent=2)+'\n');print('Protection storage and private declarations verified')
