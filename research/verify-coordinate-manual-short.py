"""Manual sequence input adapter; shared native/Metal/CUDA implementation."""
import array,importlib.util,struct,sys
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
s=importlib.util.spec_from_file_location('manual_parent',ROOT/'research/verify-coordinate-sampled-delivery-short.py');parent=importlib.util.module_from_spec(s);s.loader.exec_module(parent)
from portable_manual_control_specs import normalize,pack,check_layout
from portable_coordinate_manual_cases import fixtures
SOURCE='gpu/world_coordinate_manual_entry.slang';INPUT_WORDS=parent.INPUT_WORDS;OUTPUT_WORDS=parent.OUTPUT_WORDS;STRICT_WIRE_DIMENSIONS=True
suite=parent.suite;cross=parent.cross

def control_adapter():
    groups=parent.compile_case.__globals__['parent']
    core=groups.core
    codec=core.parent.parent.parent.area.parent.parent
    adapter=codec.parent.suite.reload.charge
    if Path(adapter.__file__).resolve()!=ROOT/'research/verify-world-charge-control.py':raise ValueError('Unexpected shared control compiler')
    return adapter

def compile_case(case):
    if not case.get('manual_controls'):return parent.compile_case(case)
    from world_frame_native import authored_metadata,roster_names
    metadata=authored_metadata(case)
    for name,weapon in zip(roster_names(case),case['combat']['weapons'],strict=True):
        spec=metadata[name];cycle=1/spec['fire_rate'] if weapon.get('mode')=='charge' and spec['input_type']=='DOWN_Charge' and spec['fire_rate'] else 0.
        if weapon.get('min_cycle',0)!=cycle:raise ValueError('Weapon minimum cycle conflicts with canonical static input type')
    check_layout(ROOT);adapter=control_adapter()
    with patch.object(adapter,'normalize_static_controls',normalize),patch.object(adapter,'compile_policy',pack):return parent.compile_case(case)

def prepare():
    rows,_=parent.prepare()
    for c in fixtures():
        w,m,b,d=compile_case(c);rows.append((c['name'],w,(c,m,b,d)))
    from portable_specs import LIMITS as L
    from portable_charge_control_specs import SEQUENCE_BASE
    seed=rows[-1][1];base=L['WORLD_CONTROL_INPUT_BASE']
    for label,at,value in [('version',base+1,4),('magic',base+7,0),('reserved',base+8,1),('tag',base+6,256),('unassociated',base+6,255),('action',base+SEQUENCE_BASE+4,2),('row-reserved',base+SEQUENCE_BASE+5,1),('capacity',base+17,9)]:
        bad=list(seed);bad[at]=value;rows.append(('reject/manual/'+label,bad,None))
    raw=array.array('I',[len(rows)])
    for _,w,_ in rows:raw.extend(w)
    if sys.byteorder!='little':raw.byteswap()
    return rows,raw.tobytes()

def native_reference(domain):
    if not domain[0].get('manual_controls'):return parent.native_reference(domain)
    from world_coordinate_manual_native import observe
    from world_coordinate_aim_native import capture
    with capture(domain[0]) as aim:n,t=observe(domain[0])
    n['coordinate_aim']=aim;return n

def compare_manual(block,n,*,base=None):
    from portable_manual_control_specs import BASE,MAGIC
    if base is not None:BASE=base
    data=n['manual_actions'];events=data['events']
    for who,row in enumerate(data['characters']):
        at=BASE+who*16;entered=[e for e in events if e['owner']==who and e['kind']=='_enter_cover'];exited=[e for e in events if e['owner']==who and e['kind']=='_exit_cover']
        flags=2 if row['until_reload'] else int(row['until']>=0)
        assert list(block[at:at+2])==[flags,int(row['cancel_after_clip'])],'Manual posture/cancellation'
        assert list(block[at+2:at+4])==list(struct.unpack('<II',struct.pack('<d',row['until']))),'Exact cover deadline'
        last=entered[-1]['time'] if entered else 0.
        assert list(block[at+4:at+6])==list(struct.unpack('<II',struct.pack('<d',last))),'Actual last entry time'
        assert list(block[at+6:at+9])==[0,len(entered),len(exited)],'Frame consumed and actual entry/exit counts'
        transitions=[e for e in events if e['owner']==who and e['kind'] in ('_enter_cover','_charge_start','_reset_action')]
        hidden=int(bool(transitions) and transitions[-1]['kind']=='_enter_cover')
        assert block[at+9]==hidden,'Charging visibility follows actual cover/start transitions'
        assert not any(block[at+10:at+15]) and block[at+15]==MAGIC,'Manual reserved/magic'

def compare(block,domain):
    if not domain[0].get('manual_controls'):return parent.compare(block,domain)
    from world_coordinate_sampled_skill_native import creation_indices
    with creation_indices(domain[0]) as indices:n=native_reference(domain)
    parent.parent.parent.compare_observed(block,domain,n,indices,manual=True)
    compare_manual(block,n);return n

def validate_rejection(block,name):
    if name.startswith('reject/manual/'):assert block[0]==64
    else:parent.validate_rejection(block,name)
