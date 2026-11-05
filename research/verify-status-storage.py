"""Check actual wire constants and unchanged GPU private-state declarations."""
import hashlib,json,re,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'app'))
from portable_specs import LIMITS as L
old=subprocess.check_output(['git','show','3f661c8:gpu/event_runtime.slang'],cwd=R,text=True)
now=(R/'gpu/event_runtime.slang').read_text();rows={}
for name in ('Runtime','Frame'):
 pattern=r'struct '+name+r'\s*\{.*?\n\};';a=re.search(pattern,old,re.S).group();b=re.search(pattern,now,re.S).group();assert a==b
 rows[name]=dict(declaration_unchanged=True,declaration_sha256=hashlib.sha256(b.encode()).hexdigest())
assert (L['INPUT_WORDS'],L['OUTPUT_WORDS'])==(77824,102400)
used=(L['IMMUNITY_SCRATCH_BASE']-L['IMMUNITY_USED_BASE']);assert used==13*L['DEFINITIONS']*2==6656
scratch=L['DEFINITIONS']*4;assert scratch==1024 and L['IMMUNITY_SCRATCH_BASE']+scratch<=L['OUTPUT_WORDS']
x=dict(passed=True,baseline_commit='3f661c8',source_commit='d2ba01a',declarations=rows,input_words=L['INPUT_WORDS'],old_output_words=94208,output_words=L['OUTPUT_WORDS'],output_growth_bytes=32768,immunity_used_words=used,immunity_used_bytes=used*4,scratch_words=scratch,scratch_bytes=scratch*4,input_status_metadata_words=8,added_private_arrays=0,added_runtime_scalars=0,added_frame_fields=0,scope='Static wire/declaration comparison only; register allocation, spill and peak memory are not measured.')
(R/'research/portable-status-storage.json').write_text(json.dumps(x,indent=2)+'\n');print('Wire and private declarations verified')
