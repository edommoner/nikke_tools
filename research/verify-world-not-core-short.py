"""Shared non-core context/accumulator, complete native battles and real rosters."""
import array,copy,importlib.util,math,struct,sys
from unittest.mock import patch
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
def module(name,file):
    s=importlib.util.spec_from_file_location(name,ROOT/'research'/file);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
base=module('not_core_base','verify-world-partial-charge-short.py');roster=module('not_core_roster','verify-world-projectile-rosters.py')
suite,cross=base.suite,base.cross
storage=module('not_core_storage','verify-world-healing-storage-short.py')
from portable_not_core_cases import fixtures
from portable_not_core_contracts import verify
from world_not_core_native import observe
from portable_not_core_specs import address
from portable_specs import LIMITS as L


def prepare():
    rows=[]
    for c in fixtures():
        if 'body' in c:
            prepared=roster.engine_worker.evaluate(dict(c['body'],_portable_static_inputs=True));w,m=roster.compile_projectile_battle(prepared);domain=(c,m,prepared,w)
        else:
            from calculator import timeline
            from world_frame_native import authored_metadata,roster_names
            metadata=authored_metadata(c);literal=[]
            with patch.dict(timeline._NIKKE,metadata):
                for who,name in enumerate(roster_names(c)):
                    actor=timeline.CharState(dict(name=name,skill_levels={'1':10,'2':10,'3':10}),c['base_atk'][who],None)
                    literal.append(dict(spread_start=actor.spread_start,spread_end=actor.spread_end,spread_shots=actor._spread_shots_needed))
            authored=dict(c,literal_weapon_geometry=literal);w,m,b=suite.compile_case(authored);domain=(c,m,b,w)
        rows.append((c['name'],w,domain))
    seed=rows[0][1];at=L['CONDITION_BASE']+L['CONDITION_WORDS'];assert seed[at]==27
    for label,changes in [('name',[(at+1,1)]),('argument',[(at+3,0x3ff00000)]),('nan',[(at+3,0x7ff80000)]),('no-world',[(L['WORLD_FRAME_INPUT_BASE'],0)]),('no-combat',[(3,0)])]:
        w=list(seed)
        for index,value in changes:w[index]=value
        rows.append(('reject/not-core-'+label,w,None))
    data=array.array('I',[len(rows)])
    for _,w,_ in rows:data.extend(w)
    if sys.byteorder!='little':data.byteswap()
    return rows,data.tobytes()


def native_reference(domain):
    c=domain[0];n,t=observe(c);verify(c,n);state=n.pop('not_core_condition')
    return dict(battle=n,skill_trace=t,not_core=state)


def states(block):
    rows=[]
    for definition in range(256):
        for owner in range(5):
            at,seen,bit=address(definition,owner);value=struct.unpack('<d',struct.pack('<II',*block[at:at+2]))[0]
            assert math.isfinite(value) and 0<=value<1
            if block[seen]&bit:rows.append(dict(definition=definition,owner=owner,value=value))
            else:assert value==0,'Unseen non-core accumulator changed'
    return rows


def compare(block,domain):
    c,m,p,words=domain;expected=native_reference(domain)
    assert block[0]==0,(c['name'],block[0])
    if 'body' in c:
        original=expected['battle'];_,_,_,diff=roster.compare(block,p,(words,m),original['battle'],original['projectile_shots']);assert not diff,(c['name'],diff[:8])
    else:
        actual=suite.decoded(block,m,c,p)
        if c.get('observe_healing_storage'):actual['healing_storage']=storage.decoded_storage(block,m,c)
        changed=[k for k in expected['battle'] if k!='scope' and actual[k]!=expected['battle'][k]];assert not changed,(c['name'],changed)
        assert suite.reload.charge.team.skill_trace(block,m)==expected['skill_trace'],(c['name'],'skill trace')
    assert states(block)==expected['not_core']['states'],(c['name'],'not-core state',states(block),expected['not_core']['states'])
    return expected


def validate_rejection(block,name):assert name.startswith('reject/not-core-') and block[0]==64
