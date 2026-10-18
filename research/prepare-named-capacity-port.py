"""Archive v29, then move named-extension masks to a full NE-bit region."""
import shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
files=['app/detail_gpu.py','app/detail_effects.cu','app/detail_effects.ptx','app/detail_effects-build.json','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','scripts/build-combat.py','scripts/build-detail-native.py','tests/test_detail_named.py','scripts/verify-normal-detail.py','research/detail-normal-acceptance.json','research/detail-capacity-checkpoint.json','research/detail-named-capacity-before.json']
for name in files:
    dst=ROOT/'research/ports/v29'/name
    assert not dst.exists(),dst
    dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,dst)
def edit(name,changes):
    p=ROOT/name;t=p.read_text(encoding='utf-8')
    for old,new in changes:
        assert old in t,(name,old);t=t.replace(old,new)
    p.write_text(t,encoding='utf-8')
edit('app/detail_gpu.py',[
 ('NE,EW,CW,OW=256,286,168,48','NE,EW,CW,OW=256,294,168,48'),
 ('B3_MASK,REDUCER_MASK=270,278','B3_MASK,REDUCER_MASK,EXTEND_MASK=270,278,286'),
 ('detail_capacity_v29','detail_named_capacity_v30'),('detail_state_bytes_v29','detail_state_bytes_v30'),
 ('words=[0]*4','words=[0]*MASK_WORDS'),
 ('for slot,word in zip((36,47,142,143),words):q[slot]=word','q[EXTEND_MASK:EXTEND_MASK+MASK_WORDS]=words'),
])
edit('app/detail_effects.cu',[
 ('#define EW 286','#define EW 294\n#define EXTEND_MASK 286'),
 ('detail_capacity_v29','detail_named_capacity_v30'),('detail_state_bytes_v29','detail_state_bytes_v30'),
 ('int name=(int)effect(e,s,k)[3],word=name/32,slot=word==0?36:word==1?47:word==2?142:143;','int name=(int)effect(e,s,k)[3],slot=EXTEND_MASK+name/32;'),
])
for name in ['scripts/build-combat.py','scripts/build-detail-native.py']:
    edit(name,[('detail_capacity_v29','detail_named_capacity_v30')])
edit('tests/test_detail_named.py',[
 ('from detail_gpu import compile_effects,UnsupportedDetail','from detail_gpu import compile_effects,UnsupportedDetail,EXTEND_MASK,MASK_WORDS'),
 ('words=[int(q[i]) for i in (36,47,142,143)]','words=[int(q[i]) for i in range(EXTEND_MASK,EXTEND_MASK+MASK_WORDS)]'),
])
print('Prepared named-state capacity v30')
