"""Complete skill rows in the unused weapon-only typed receipt bank.

No row is omitted: decode all pages with the existing strict skill decoder,
then provide a checked legacy prefix to comparators of all other state.
"""
import copy,importlib.util
from pathlib import Path
from portable_specs import LIMITS as L
from portable_coordinate_typed_specs import INPUT_WORDS,OUTPUT_WORDS,COORDINATE_OUTPUT_WORDS
SOURCE='gpu/world_coordinate_typed_history_entry.slang'
PREFIX=128
CAPACITY=2048
WIDTH=48
BASE=COORDINATE_OUTPUT_WORDS+3568
END=BASE+(CAPACITY-PREFIX)*WIDTH
assert END<=COORDINATE_OUTPUT_WORDS+136688

def shader_layout():
    return ('// Generated from portable_skill_history.py; weapon-only receipt ownership.\n'
        '#define PORTABLE_WORLD_SKILL_HISTORY\n'
        f'#define WORLD_SKILL_TRACE_CAPACITY {CAPACITY}U\n'
        f'#define WORLD_SKILL_TRACE_AT(s,index) ((index)<128U ? (s).resourceOutput+P_WORLD_SKILL_TRACE_BASE+(index)*48U : (s).resourceOutput+{BASE}U+((index)-128U)*48U)\n'
        '#define WORLD_SKILL_HISTORY_ADMIT(s) (commands[(s).inputBase+109968U+13U]==1U && commands[(s).inputBase+109968U+14U]==1U && commands[(s).inputBase+109968U+15U]==2U && commands[(s).inputBase+109968U+12U]==1U)\n')

def check_layout(root):
    from portable_coordinate_typed_specs import check_layout as typed
    typed(root)
    if (Path(root)/'gpu/skill_history_layout.slang').read_text()!=shader_layout():raise ValueError('Shared skill history layout differs')

def require_capacity(native,capacity=CAPACITY):
    count=len(native['skill_trace'])
    if type(capacity) is not int or capacity not in (PREFIX,CAPACITY):raise ValueError('Unregistered shared skill history capacity')
    if count>capacity:raise ValueError(f'Original catalogue requires shared skill-history capacity extension: {count} > {capacity}; complete history must be retained')

def compare_and_project(block,domain,native,indices):
    """Validate all semantic rows and unused words before the legacy projection."""
    from world_coordinate_sampled_skill_native import trace_view
    require_capacity(native)
    assert len(block)==OUTPUT_WORDS and block[0]==0,'Complete successful skill history output required'
    expected=trace_view(native['skill_trace'],indices);count=len(expected);head=L['WORLD_SKILL_HEAD_BASE'];trace=L['WORLD_SKILL_TRACE_BASE']
    assert block[head]==0x57534b31 and block[head+1]==count,'Complete skill history count'
    assert block[head+2]==max((len(row['recipients']) for row in expected),default=0),'Complete skill history target maximum'
    assert not any(block[head+4:head+8]),'Skill history header reserved words'
    spec=importlib.util.spec_from_file_location('complete_skill_history_decoder',Path(__file__).resolve().parents[1]/'research/verify-world-skills.py')
    decoder=importlib.util.module_from_spec(spec);spec.loader.exec_module(decoder)
    page=[0]*(trace+PREFIX*WIDTH);page[head]=0x57534b31
    decoded=[]
    for first in range(0,count,PREFIX):
        length=min(PREFIX,count-first);page[head+1]=length
        for j in range(length):
            index=first+j;at=trace+index*WIDTH if index<PREFIX else BASE+(index-PREFIX)*WIDTH
            page[trace+j*WIDTH:trace+(j+1)*WIDTH]=block[at:at+WIDTH]
        rows=decoder.skill_trace(page)
        for row in rows:row['row']=domain[1]['binding_source_indices'][row['row']]
        decoded.extend(rows)
    assert decoded==expected,'Every ordered skill landing row must match the native creation receipt'
    assert not any(block[trace+min(count,PREFIX)*WIDTH:trace+PREFIX*WIDTH]),'Unused skill prefix'
    assert not any(block[BASE+max(0,count-PREFIX)*WIDTH:END]),'Unused skill history continuation'
    view=list(block);view[head+1]=min(count,PREFIX);view[BASE:END]=[0]*(END-BASE)
    original=copy.copy(native);original['skill_trace']=native['skill_trace'][:PREFIX]
    return view,original,indices[:PREFIX]
