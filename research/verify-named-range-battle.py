"""Complete original battles use shared comparers plus checked radial records."""
import array,importlib.util,sys,struct
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
s=importlib.util.spec_from_file_location('named_range_complete_base',ROOT/'research/verify-logical-actor-geometry.py');base=importlib.util.module_from_spec(s);s.loader.exec_module(base)
from portable_named_range_battle_wire import SOURCE,BASE,HEADER,INPUT,OUTPUT,OUT,OUT_HEADER,CASTS,CAST_WORDS,END,MAGIC,check_schema
from portable_named_range_battle_cases import fixtures
from world_named_range_battle_full_native import prepare_case,observe
from portable_skill_history import require_capacity
from portable_specs import LIMITS as L,FIELDS as F
suite=SimpleNamespace(INPUT=INPUT,OUTPUT=OUTPUT);STRICT_WIRE_DIMENSIONS=True;cross=base.cross;NATIVE_COMPARISON_CONTEXT=base.NATIVE_COMPARISON_CONTEXT

def prepare():
    check_schema(ROOT);rows=[]
    for case in fixtures():
        words,domain=prepare_case(case);rows.append((case['name'],words,domain))
    seed=rows[0][1]
    for label,at,value in [('magic',BASE,0),('version',BASE+1,2),('reserved',BASE+4,1),('missing-owner-rule',BASE+HEADER,0),('base-count',BASE+HEADER+1,129),('radius-nan',BASE+HEADER+3,0x7ff80000),('body-kind',BASE+HEADER+4,5),('unused-rule',BASE+HEADER+32,1)]:
        w=list(seed);w[at]=value;rows.append(('reject/named-range-battle/'+label,w,None))
    # Exercise descriptor ownership when the original roster also enables
    # stack operations. The common named-enemy validator must still reject
    # every malformed operand admitted through the stack metadata bank.
    named=[L['MODE_BASE']+r*L['MODE_WORDS']+24 for r in range(seed[1]) if seed[L['MODE_BASE']+r*L['MODE_WORDS']+24]==0x4e455231]
    assert named,'Original named-enemy consumer required'
    at=named[0]
    for label,offset,value in [('named-tag',0,0),('named-symbol',1,257),('named-flags',2,4),('named-reserved',3,1)]:
        w=list(seed);w[at+offset]=value;rows.append(('reject/named-range-battle/'+label,w,None))
    raw=array.array('I',[len(rows)])
    for _,w,_ in rows:raw.extend(w)
    if sys.byteorder!='little':raw.byteswap()
    return rows,raw.tobytes()

def native_reference(domain):
    n=observe(domain);require_capacity(n)
    assert n['original_input_identity']['definitions']==87 and n['original_input_identity']['chars_config_seed_weapon_verified']
    data=n['named_range_battle'];assert len(data['casts'])==len(data['landings'])==54
    assert any(c['percent']==500 and c['capacity']==3 for c in data['casts'])
    assert all(p['kind']=='summon' for p in domain[0]['patterns'])
    assert not any(row['kind']=='_coord_skill_hits' for row in n['sampled_skill_damage']),'Additional coordinate target calculations need their own selection contract'
    return n

def words(value):return list(struct.unpack('<II',struct.pack('<d',float(value))))

def compare_observed(block,domain,n,indices):
    assert len(block)==OUTPUT and block[0]==0,'Complete successful named range battle output required'
    c,m,bindings,_=domain;casts=n['named_range_battle']['casts'];count=len(casts);head=list(block[OUT:OUT+OUT_HEADER])
    assert head==[MAGIC,1,count]+[0]*(OUT_HEADER-3),'Named radial cast header'
    by_label={b.label:i for i,b in enumerate(bindings)};names=c['names'];bound={r['effect']:r for r in m['named_range_battle']['bindings']}
    cast_keys={}
    for i,record in enumerate(casts):
        row=bound[record['effect']]['row'];body=next((j+1 for j,a in enumerate(record['recipients']) if a['handle'][0]==0),0)
        adds=[a for a in record['recipients'] if a['handle'][0]==5]
        expected=[0]*CAST_WORDS;expected[:2]=[row,names.index(record['owner'])]
        for at,key in [(2,'time'),(4,'base_radius'),(6,'percent'),(8,'factor'),(10,'radius'),(14,'additional_targets')]:expected[at:at+2]=words(record[key])
        expected[12:14]=[record['base_count'],record['capacity']];expected[16:18]=[body,len(adds)]
        expected[18:20]=words(record['aim'][0]);expected[20:22]=words(record['aim'][1])
        actual=list(block[OUT+OUT_HEADER+i*CAST_WORDS:OUT+OUT_HEADER+(i+1)*CAST_WORDS])
        assert actual==expected,('Named radial cast record',i,actual,expected)
        key=(row,record['time']);assert key not in cast_keys;cast_keys[key]=adds
    assert not any(block[OUT+OUT_HEADER+count*CAST_WORDS:END]),'Unused radial cast records'
    # In these original worlds all ordinary coordinate extras are empty. The
    # new ADD cast keys are compared explicitly; no native trace is removed.
    from portable_arena_specs import coordinate_layout
    cp=coordinate_layout(1048576)
    selection=[]
    for trace in n['skill_trace']:
        row=m['binding_source_indices'].index(trace['row']);adds=cast_keys.get((row,trace['created']),[])
        # Legacy B3 pending packets do not own a coordinate cast snapshot.
        selection.extend([row,trace['hit'],len(adds),0])
        for actor in adds:
            slot=by_label[actor['label']];kind,identity,generation=actor['handle'];selection.extend([slot,kind,identity,generation])
    used=block[cp['BASE']+3]
    assert block[cp['BASE']+4]==len(n['skill_trace']) and used==len(selection),('All cast selections',block[cp['BASE']+4],len(n['skill_trace']),used,len(selection))
    assert list(block[cp['SELECTION']:cp['SELECTION']+used])==selection,'Every frozen coordinate/radial selection'
    assert not any(block[cp['SELECTION']+used:cp['END']]),'Unused coordinate selection words'
    view=list(block);view[OUT:END]=[0]*(END-OUT)
    return base.compare_observed(view,domain,n,indices)

def compare(block,domain):
    from world_coordinate_sampled_skill_native import creation_indices
    with creation_indices(domain[0]) as indices:n=native_reference(domain)
    return compare_observed(block,domain,n,indices)

def validate_rejection(block,name):assert name.startswith('reject/named-range-battle/') and block[0]==64
