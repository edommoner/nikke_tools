"""Archive verified v28 artifacts, then migrate effect-index bitmaps to 256 bits."""
from pathlib import Path
import shutil
ROOT=Path(__file__).resolve().parents[1]
files=['app/detail_gpu.py','app/detail_effects.cu','app/detail_effects.ptx','app/detail_effects-build.json','app/detail_effects-sm86.cubin','app/detail_effects-sm86.json','scripts/build-combat.py','scripts/build-detail-native.py','research/detail-normal-acceptance.json','research/detail-capacity-cpu-audit.json','research/detail-team-hits-checkpoint.json']
archive=ROOT/'research/ports/v28'
for name in files:
    target=archive/name
    if target.exists():
        assert target.read_bytes()==(ROOT/name).read_bytes(),name
    else:
        target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,target)
def edit(name,changes):
    path=ROOT/name;text=path.read_text(encoding='utf-8')
    for old,new in changes:
        assert old in text,(name,old)
        text=text.replace(old,new)
    path.write_text(text,encoding='utf-8')
edit('app/detail_gpu.py',[
 ('NE,EW,CW,OW=128,270,168,48','NE,EW,CW,OW=256,286,168,48\nMASK_WORDS=(NE+31)//32\nB3_MASK,REDUCER_MASK=270,278'),
 ('detail_team_hits_v28','detail_capacity_v29'),('detail_state_bytes_v28','detail_state_bytes_v29'),
 ('q[245+k//32]','q[REDUCER_MASK+k//32]'),
 ("'more than 128 named states'","f'more than {NE} named states'"),
 ("'more than 128 effects'","f'more than {NE} effects'"),
 ('row[52+bound_index//32]','row[B3_MASK+bound_index//32]'),
])
edit('app/detail_effects.cu',[
 ('#define NE 128','#define NE 256\n#define MASK_WORDS ((NE+31)/32)\n#define B3_MASK 270\n#define REDUCER_MASK 278'),
 ('#define EW 270','#define EW 286'),
 ('detail_team_hits_v28','detail_capacity_v29'),('detail_state_bytes_v28','detail_state_bytes_v29'),
 ('excluded[4]','excluded[MASK_WORDS]'),('listener[245+id/32]','listener[REDUCER_MASK+id/32]'),
 ('if(listener[245]==0&&listener[246]==0&&listener[247]==0&&listener[248]==0)return n<1?1:n;', 'bool any_reducer=false;for(int k=0;k<MASK_WORDS;k++)if(listener[REDUCER_MASK+k]!=0){any_reducer=true;break;}\n if(!any_reducer)return n<1?1:n;'),
 ('for(int k=0;k<4;k++)s->excluded[k]=(unsigned int)q[52+k]','for(int k=0;k<MASK_WORDS;k++)s->excluded[k]=(unsigned int)q[B3_MASK+k]'),
 ('for(int k=0;k<4;k++)s->excluded[k]=0','for(int k=0;k<MASK_WORDS;k++)s->excluded[k]=0'),
 ('for(int j=0;j<4;j++)s->excluded[j]=0','for(int j=0;j<MASK_WORDS;j++)s->excluded[j]=0'),
])
for name in ['scripts/build-combat.py','scripts/build-detail-native.py']:
    edit(name,[('detail_team_hits_v28','detail_capacity_v29')])
print('Archived v28 and prepared capacity v29 sources')
