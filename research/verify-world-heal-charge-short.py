"""Received-healing scalar pools: one native/CUDA/Metal input and observer table."""
import array,importlib.util,sys,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
s=importlib.util.spec_from_file_location('heal_charge_parent',ROOT/'research/verify-world-max-ammo-scaling-short.py');prior=importlib.util.module_from_spec(s);s.loader.exec_module(prior)
suite,cross=prior.suite,prior.cross
from portable_heal_charge_cases import fixtures
from portable_heal_charge_contracts import verify
from world_heal_charge_native import observe
from portable_heal_charge_specs import TRACE_BASE,TRACE_MAGIC,TRACE_COUNT,TRACE_WORDS
from portable_specs import LIMITS as L,FIELDS as F

def prepare():
    rows=[]
    for c in fixtures():
        w,m,b=suite.compile_case(c);rows.append((c['name'],w,(c,m,b)))
    seed=rows[0][1];row=1;at=L['DEFINITION_BASE']+row*L['DEFINITION_WORDS']
    changes=[('missing-policy',L['PROTECTION_DEFINITION_BASE']+row,0),('wrong-stat',at+F['STAT'],5),('wrong-kind',at+F['KIND'],4),('nonfinite',at+F['VALUE']+1,0x7ff80000),('periodic',at+F['INTERVAL']+1,0x3ff00000),('missing-world',L['WORLD_FRAME_INPUT_BASE'],0),('invalid-policy',L['PROTECTION_DEFINITION_BASE']+row,266),('missing-discharge-name',L['DEFINITION_BASE']+2*L['DEFINITION_WORDS']+F['TARGET_NAME'],0xffffffff)]
    for label,offset,value in changes:
        w=list(seed);assert w[offset]!=value;w[offset]=value;rows.append(('reject/heal-charge-'+label,w,None))
    packed=array.array('I',[len(rows)])
    for _,w,_ in rows:packed.extend(w)
    if sys.byteorder!='little':packed.byteswap()
    return rows,packed.tobytes()

def native_reference(domain):
    n,t=observe(domain[0]);verify(domain[0],n);return dict(battle=n,skill_trace=t)

def expected_trace(events):
    output=[]
    for index,e in enumerate(events):
        if e['kind']=='snapshot':
            pool=next(p for p in e['after'] if p['active'] and p['row']==e['row'] and p['owner']==e['owner'])
            output.append((e['returned_sequence'],(1,e['row'],e['owner'],e['time'],0.,0.,pool['base'],pool['base'])))
        elif e['kind']=='collect':
            for j in range(index+1,e['returned_sequence']):
                cap=events[j]
                if cap['kind']!='capacity':continue
                before=next(p for p in cap['before'] if p['active'] and not p['done'] and p['row']==cap['row'])
                after=next(p for p in e['after'] if p['active'] and p['row']==cap['row'] and p['owner']==before['owner'])
                output.append((j+1,(2,cap['row'],e['owner'],e['time'],before['current'],after['current'],cap['value'],e['amount'])))
        elif e['kind']=='take':output.append((e['returned_sequence'],(3,e['row'],e['owner'],e['time'],e['value'],0.,0.,e['value'])))
    return [row for _,row in sorted(output,key=lambda x:x[0])]

def trace_words(row):
    result=list(row[:3])
    for value in row[3:]:result.extend(struct.unpack('<II',struct.pack('<d',value)))
    return result+[0]*(TRACE_WORDS-len(result))

def compare_trace(block,events):
    from portable_heal_charge_history import verify as verify_history
    return verify_history(block,[trace_words(row) for row in expected_trace(events)])

def compare_expected(block,domain,expected):
    events=expected['battle']['healing_charge']['events']
    battle=dict(expected['battle']);battle.pop('healing_charge')
    prior.prior.prior.landing.base.compare_expected(block,domain,dict(expected,battle=battle))
    compare_trace(block,events)
    return expected

def compare(block,domain):return compare_expected(block,domain,native_reference(domain))

def validate_rejection(block,name):assert name.startswith('reject/heal-charge-') and block[0]==64,(name,block[0])
