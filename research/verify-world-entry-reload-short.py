"""Native entry-reload contracts through the common resident CUDA/Metal executor."""
import array,importlib.util,struct,sys
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
spec=importlib.util.spec_from_file_location('entry_reload_base',ROOT/'research/verify-world-projectile-short.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
suite,cross=base.suite,base.cross
from portable_specs import LIMITS as L
from portable_entry_reload_cases import fixtures
from world_entry_reload_native import data_context,observe
from calculator import timeline
SOURCE='gpu/world_entry_reload_resident_entry.slang'


def compile_case(case):
    with data_context(case):return suite.compile_case(case)


def prepare():
    entries=[]
    for case in fixtures():
        if case['name'].startswith('entry-reload-cover-'):
            try:compile_case(case)
            except ValueError as exc:
                if 'Non-hold sequence' not in str(exc):raise
            else:raise AssertionError('Cover controls must remain rejected until shared cover adapter exists')
            continue
        words,metadata,bindings=compile_case(case)
        entries.append((case['name'],words,(case,metadata,bindings)))
    seed=entries[0][1];at=L['MODE_BASE']+30
    for name,offset,value in [('policy3',at,3),('dynamic-nonzero-delay',at-2,1),('policy0-with-delay',at,0),('reserved',at+1,2),('nan-delay',at-1,0x7ff80000),('infinite-delay',at-1,0x7ff00000)]:
        words=list(seed);words[offset]=value
        if name=='policy0-with-delay':words[at-2:at]=list(struct.unpack('<II',struct.pack('<d',.1)))
        entries.append(('reject/'+name,words,None))
    assert len(entries)==37
    packed=array.array('I',[len(entries)])
    for _,words,_ in entries:packed.extend(words)
    if sys.byteorder!='little':packed.byteswap()
    return entries,packed.tobytes()


def native_reference(domain):
    case,_,_=domain;actors={};original=timeline.CharState._tick_weapon_change
    from world_frame_native import roster_names
    names=roster_names(case)
    def tick(actor,*args,**kw):
        actors[names.index(actor.name)]=actor
        return original(actor,*args,**kw)
    with patch.object(timeline.CharState,'_tick_weapon_change',tick):native,trace=observe(case)
    events=native.pop('entry_reload')
    return dict(battle=native,skill_trace=trace,
        entry_duration_queries=[dict(owner=q['owner'],time=q['time'],duration=q['result']) for q in events['queries']],
        mode_entry_wait_until=[actors[i]._wc_entry_reload_until if i in actors else -1. for i in range(5)])


def compare(block,domain):
    case,metadata,bindings=domain;expected=native_reference(domain)
    actual=suite.decoded(block,metadata,case,bindings)
    assert block[0]==0,case['name']
    differences=[key for key in expected['battle'] if key!='scope' and actual[key]!=expected['battle'][key]]
    assert not differences,(case['name'],differences)
    trace=suite.reload.charge.team.skill_trace(block,metadata)
    assert trace==expected['skill_trace'],(case['name'],'skill trace')
    number=lambda at:struct.unpack('<d',struct.pack('<II',*block[at:at+2]))[0]
    until=[number(L['MODE_ENTRY_STATE_BASE']+2*i) for i in range(5)]
    # No entry policy: the base output tail stays zero by contract.
    if metadata.get('mode_entry_enabled'):assert until==expected['mode_entry_wait_until'],(case['name'],'entry until',until,expected['mode_entry_wait_until'])
    head=L['MODE_ENTRY_STATE_BASE']+10;count=block[head]
    assert count<=96 and not any(block[head+1:head+8]),(case['name'],'diagnostic bounds')
    queries=[]
    for i in range(count):
        at=head+8+i*5;queries.append(dict(owner=block[at],time=number(at+1),duration=number(at+3)))
    assert queries==expected['entry_duration_queries'],(case['name'],'duration query order',queries,expected['entry_duration_queries'])
    assert not any(block[head+8+count*5:head+488]),(case['name'],'diagnostic tail')
    return expected
