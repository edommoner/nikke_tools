"""Static layout evidence only; not physical GPU memory measurements."""
import hashlib,json,re,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'app'))
from portable_specs import ABI,LIMITS as L
source=(R/'gpu/event_runtime.slang').read_text();old=subprocess.check_output(['git','show','6be8eb5:gpu/event_runtime.slang'],cwd=R,text=True)
rows={}
for name in ('Runtime','Definition','Frame'):
    pattern=r'struct '+name+r'\s*\{.*?\n\};'
    before=re.search(pattern,old,re.S).group();after=re.search(pattern,source,re.S).group();assert before==after,name
    rows[name]=dict(declaration_unchanged=True,sha256=hashlib.sha256(after.encode()).hexdigest())
assert ABI==0x50455669 and (L['INPUT_WORDS'],L['OUTPUT_WORDS'])==(86016,159744)
x=dict(passed=True,wire_abi=hex(ABI),source_commit='ed68e6847fe8e7f0d13ed81a6af6dec6837ca915',prior_source='6be8eb5',input_words=L['INPUT_WORDS'],output_words=L['OUTPUT_WORDS'],input_stride_growth_words=0,output_stride_growth_words=0,added_runtime_arrays=0,added_runtime_scalars=0,added_definition_fields=0,added_frame_fields=0,declarations=rows,base_weapon_rl_bit=dict(existing_field='attackContext',mask=4,scope='Explosion classification on charge path only; immutable base type survives mode changes'),stat_notice_tag=dict(existing_field='buffEvent',low_policy_bits=2,tag_shift=2,zero_means_disabled=True,maximum_tag_plus_one=256),scope='Static shared declarations and wire layout. Does not measure compiler registers, spills, physical private storage or peak GPU memory.')
(R/'research/portable-named-state-storage.json').write_text(json.dumps(x,indent=2)+'\n');print('Shared declarations and wire strides unchanged')
