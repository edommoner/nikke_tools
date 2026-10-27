"""Full original effects with literal cover operations and 15-target saturation."""
import array,importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts','tests')]
s=importlib.util.spec_from_file_location('original_controls_parent',ROOT/'research/verify-original-lock-composition.py');parent=importlib.util.module_from_spec(s);s.loader.exec_module(parent)
from portable_heavyarms_original_composition import prepare_case
from portable_charge_control_specs import SEQUENCE_BASE
SOURCE=parent.SOURCE;suite=parent.suite;cross=parent.cross
compile_case=parent.compile_case

def verify_contract(c,n):
    if c.get('declared_manual_sequences'):
        owner=next(i for i,name in enumerate(c['names']) if name in c['declared_manual_sequences'])
        rows=[e for e in n['manual_actions']['events'] if e['kind']=='_enter_cover' and e['owner']==owner]
        if len(rows)!=1:raise AssertionError('Declared cover must enter exactly once through the real manual producer')
        if owner==0 and rows[0]['time'] not in n['lock_clears']:raise AssertionError('Owner cover must clear live lock membership')
    if c['name']=='original-heavyarms/30s/16adds':
        counts=[len(shot['handles']) for shot in n['lock_shots']]
        if counts.count(15)!=2 or not any(value==5 for value in counts[counts.index(15)+2:]):raise AssertionError('Original burst must saturate at 15 twice, then restore the base quota')
        if max(p['receipt'][1] for p in n['lock_pulses'])!=15:raise AssertionError('Actual acquisition must reach 15 distinct handles')
    return n

def native_reference(domain,**kwargs):return verify_contract(domain[0],parent.native_reference(domain,**kwargs))
def compare(block,domain):return verify_contract(domain[0],parent.compare(block,domain))

def fixtures():
    rows=parent.fixtures()
    rows.extend(prepare_case(3,adds,cover=cover)[0] for adds,cover in [(0,(0,.35,.25)),(3,(0,.35,.25)),(3,(0,0.,.25)),(3,(1,.35,.25))])
    rows.append(prepare_case(30,16)[0])
    return rows

def prepare():
    entries,_=parent.prepare(cases=fixtures())
    seed=next(words for _,words,domain in entries if domain is not None and domain[0].get('declared_manual_sequences'))
    base=parent.L['WORLD_CONTROL_INPUT_BASE']
    for name,at,value in [('version',base+1,4),('action',base+SEQUENCE_BASE+4,2),('reserved',base+SEQUENCE_BASE+5,1),('capacity',base+17,9)]:
        words=list(seed);words[at]=value;entries.append(('reject/original-controls/'+name,words,None))
    raw=array.array('I',[len(entries)])
    for _,words,_ in entries:raw.extend(words)
    if sys.byteorder!='little':raw.byteswap()
    return entries,raw.tobytes()
