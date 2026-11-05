"""Real shared resident sampled physical battles, not point-only primitives."""
import array,copy,importlib.util,sys
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
def module(name,path):
    s=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
parent=module('sampled_battle_compiler','research/verify-coordinate-group-short.py')
from portable_coordinate_sampled_battle_cases import fixtures
from portable_coordinate_sampling_contracts import verify
from world_coordinate_sampling_native import observe
from world_coordinate_aim_native import capture
from portable_coordinate_sampling_bank import LAYOUT as BANK,check_schema
from portable_enemy_target_specs import META_BASE,normalize_seed
SOURCE='gpu/world_coordinate_sampling_entry.slang';INPUT_WORDS=parent.INPUT_WORDS;OUTPUT_WORDS=parent.OUTPUT_WORDS;STRICT_WIRE_DIMENSIONS=True
suite=SimpleNamespace(INPUT=INPUT_WORDS,OUTPUT=OUTPUT_WORDS);cross=parent.cross
def compile_case(case):
    w,m,b,d=parent.compile_case(case,allow_world_nodes=True);seed=normalize_seed(case.get('seed',19))
    assert w[META_BASE]==1;w[META_BASE+1:META_BASE+3]=[seed&0xffffffff,seed>>32];m['enemy_targeting']['seed']=seed
    return w,m,b,d
def prepare():
    check_schema(ROOT);entries=[]
    for c in fixtures():
        w,m,b,d=compile_case(c);entries.append((c['name'],w,(c,m,b,d)))
    seed=entries[0][1]
    w=list(seed);w[META_BASE]=0;entries.append(('reject/sampled-battle/rng-disabled',w,None))
    bad=copy.deepcopy(fixtures()[5]);bad['effects']=[dict(name='unsupported-random-skill',source='declared',type='damage',stat='bonus_damage',fixed_value=100,target='boss',trigger=dict(timing=['battle_start'],condition=[]))];bad['owners']=[0]
    w,_,_,_=compile_case(bad);entries.append(('reject/sampled-battle/random-skill',w,None))
    bad=copy.deepcopy(fixtures()[5]);bad['enemy']['core_px']=8;bad['enemy']['coord']['auto_aim']=[float.fromhex('0x1.fffffffffffffp+1023'),0.];bad['patterns'].append(dict(id='core-overflow',kind='core',core_px=8,x=-float.fromhex('0x1.fffffffffffffp+1023'),y=0.))
    w,_,_,_=compile_case(bad);entries.append(('reject/sampled-battle/core-distance-overflow',w,None))
    raw=array.array('I',[len(entries)])
    for _,w,_ in entries:raw.extend(w)
    if sys.byteorder!='little':raw.byteswap()
    return entries,raw.tobytes()
def native_reference(domain):
    with capture(domain[0]) as aim:n,t=observe(domain[0])
    verify(domain[0],n);n['coordinate_aim']=aim;return n
def compare(block,domain):
    c,m,b,d=domain;n=native_reference(domain)
    from portable_roster_team_history import legacy_view
    view,battle=legacy_view(block[:786432],n['battle'],parent.L['WORLD_TEAM_HEAD_BASE'])
    parent.physical.codec.compare_expected(view,domain[:3],dict(battle=battle,skill_trace=n['skill_trace']))
    parent.parent.parent.compare_aim(block,domain,n['coordinate_aim'])
    names=parent.roster_names(c);by_name={r['label']:r for r in d['rows']};trace=[]
    for pellet in n['physical_pellets']:
        for p in pellet['packets']:
            target=by_name.get(p['target']);slot=target['slot'] if target else 0;kind=target['kind'] if target else 0
            trace.append([names.index(pellet['owner']),slot,kind,1,*parent.double_words(pellet['time']),*parent.double_words(p['damage']),int(p['extra']),0,0,0])
    cp=parent.physical.CP;start=cp['TRACE'];end=start+len(trace)*12
    assert block[cp['BASE']+2]==len(trace) and list(block[start:end])==sum(trace,[]),'Ordered actual sampled packets'
    assert not any(block[end:start+cp['TRACE_COUNT']*12]),'Unused packet trace'
    rng=BANK['RNG'];state=n['physical_rng'];assert block[rng]==state['index'] and list(block[rng+8:rng+632])==state['state'],'Independent physical MT state'
    contract=verify(c,n);assert block[rng+1]==contract['physical_rng_words'],'Physical MT consumption'
    return n
def validate_rejection(block,name):assert name.startswith('reject/sampled-battle/') and block[0]==64
