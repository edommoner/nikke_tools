"""Policy literals feed the shared anchor/manual runtime on both GPU backends."""
import array,copy,importlib.util,struct,sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
s=importlib.util.spec_from_file_location('policy_parent',ROOT/'research/verify-coordinate-manual-short.py');parent=importlib.util.module_from_spec(s);s.loader.exec_module(parent)
from portable_cover_policy_specs import SOURCE,INPUT_BASE,INPUT_WORDS as EXTRA_INPUT,OUTPUT_BASE,OUTPUT_WORDS as EXTRA_OUTPUT,MAGIC,normalize,pack,empty
INPUT_WORDS=INPUT_BASE+EXTRA_INPUT;OUTPUT_WORDS=OUTPUT_BASE+EXTRA_OUTPUT;suite=SimpleNamespace(INPUT=INPUT_WORDS,OUTPUT=OUTPUT_WORDS);STRICT_WIRE_DIMENSIONS=True;cross=parent.cross
from portable_coordinate_policy_cases import fixtures

def compile_case(case):
    if not case.get('cover_policies'):
        w,m,b,d=parent.compile_case(case);return w+empty(),m,b,d
    from calculator import timeline
    from world_frame_native import roster_names,authored_metadata
    from world_authored_roster import skill_levels
    names=roster_names(case);metadata=authored_metadata(case)
    for name,weapon in zip(names,case['combat']['weapons'],strict=True):
        if weapon.get('cooldown',40.)!=metadata[name].get('burst_cooldown',40.):raise ValueError('Policy cooldown literal conflicts with canonical static metadata')
    chars=[dict(name=n,skill_levels=lv,control=copy.deepcopy(c)) for n,lv,c in zip(names,skill_levels(case),case['controls'],strict=True)]
    with patch.dict(timeline._NIKKE,metadata):owners=normalize(chars,case['base_atk'],case['enemy'])
    lowered=copy.deepcopy(case)
    for control in lowered['controls']:
        for key in ('cover','reload'):control.pop(key,None)
    w,m,b,d=parent.compile_case(lowered);return w+pack(owners,names,m['states']),m,b,d

def prepare():
    old,_=parent.prepare();rows=[(name,w+empty(),domain) for name,w,domain in old]
    for c in fixtures():
        w,m,b,d=compile_case(c);rows.append((c['name'],w,(c,m,b,d)))
    seed=rows[-1][1];base=INPUT_BASE
    for label,at,value in [('magic',base,0),('mask',base+2,32),('row-size',base+4,23),('history',base+6,17),('priority',base+9,100),('anchor',base+12,6),('reserved',base+8+16,1)]:
        w=list(seed);w[at]=value;rows.append(('reject/policy/'+label,w,None))
    raw=array.array('I',[len(rows)])
    for _,w,_ in rows:raw.extend(w)
    if sys.byteorder!='little':raw.byteswap()
    return rows,raw.tobytes()

def native_reference(domain):return parent.native_reference(domain)
def compare(block,domain):
    n=parent.compare(block[:OUTPUT_BASE],domain)
    if not domain[0].get('cover_policies'):assert not any(block[OUTPUT_BASE:]);return n
    h=OUTPUT_BASE;w=compile_case(domain[0])[0];mask=w[INPUT_BASE+2]
    assert list(block[h:h+4])==[MAGIC,1,mask,5] and not any(block[h+4:h+16])
    for who,row in enumerate(n['cover_policy_state']):
        a=h+16+who*64;num=lambda at:struct.unpack('<d',struct.pack('<II',*block[at:at+2]))[0]
        assert num(a)==row['cover_anchor'] and num(a+2)==row['reload_anchor'],'Consumed policy anchors'
        assert block[a+4]=={'':0,'hold':0,'cover':1,'reload':2}[row['kind']] and num(a+6)==row['value'],'Current anchor identity'
        history=[];assert block[a+5]<=16
        for i in range(block[a+5]):
            kind=block[a+8+i*3];assert kind in (1,2);history.append([('cover','reload')[kind-1],num(a+9+i*3)])
        assert sorted(history)==row['reentry'],'Each policy anchor may be restored only once'
        assert not any(block[a+8+len(history)*3:a+64])
    assert not any(block[h+336:]);return n

def validate_rejection(block,name):
    if name.startswith('reject/policy/'):assert block[0]==64
    else:parent.validate_rejection(block[:OUTPUT_BASE],name)
