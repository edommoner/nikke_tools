"""Squad actions are authored literals; all recipient decisions stay on GPU."""
import array,copy,importlib.util,struct,sys
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
s=importlib.util.spec_from_file_location('squad_parent',ROOT/'research/verify-coordinate-policy-short.py');parent=importlib.util.module_from_spec(s);s.loader.exec_module(parent)
from portable_squad_control_specs import INPUT_BASE,INPUT_WORDS as EXTRA_INPUT,SOURCE,MAGIC,pack,empty
from portable_coordinate_squad_cases import fixtures
from world_frame_native import roster_names
INPUT_WORDS=INPUT_BASE+EXTRA_INPUT;OUTPUT_WORDS=parent.OUTPUT_WORDS;STRICT_WIRE_DIMENSIONS=True;suite=SimpleNamespace(INPUT=INPUT_WORDS,OUTPUT=OUTPUT_WORDS);cross=parent.cross
SQUAD_BASE=1769808

def compile_case(case):
    if not case.get('squad_controls'):
        w,m,b,d=parent.compile_case(case);return w+empty(),m,b,d
    lower=copy.deepcopy(case);lower['sequence']=[]
    w,m,b,d=parent.compile_case(lower);return w+pack(case.get('sequence',[]),roster_names(case)),m,b,d

def prepare():
    old,_=parent.prepare();rows=[(name,w+empty(),domain) for name,w,domain in old]
    for c in fixtures():
        w,m,b,d=compile_case(c);rows.append((c['name'],w,(c,m,b,d)))
    seed=rows[-1][1];base=INPUT_BASE
    for label,at,value in [('magic',base,0),('count',base+2,17),('rows',base+3,15),('reserved',base+5,1),('kind',base+10,3),('recipient',base+11,1),('row-reserved',base+14,1),('unused',base+8+8,1)]:
        w=list(seed);w[at]=value;rows.append(('reject/squad/'+label,w,None))
    raw=array.array('I',[len(rows)])
    for _,w,_ in rows:raw.extend(w)
    if sys.byteorder!='little':raw.byteswap()
    return rows,raw.tobytes()

def native_reference(domain):return parent.native_reference(domain)
def compare(block,domain):
    if not domain[0].get('squad_controls'):return parent.compare(block,domain)
    # Padding ownership is explicit: compare policy/manual without the squad bank,
    # then compare every squad word below, including all reserved words.
    clean=list(block);clean[SQUAD_BASE:]=[0]*(OUTPUT_WORDS-SQUAD_BASE)
    n=parent.parent.compare(clean[:1769472],domain)
    parent.compare_policy_state(clean,n,compile_case(domain[0])[0][109530])
    return compare_state(block,n,len(domain[0].get('sequence',[])))
def compare_state(block,n,count):
    h=SQUAD_BASE;assert list(block[h:h+4])==[MAGIC,1,n['squad_control']['sequence_index'],count]
    # Forced focus or the previous live owner is observed at the last cover event.
    # The per-frame arbitration/aim fingerprints independently check its effects.
    flags=[int(row['cover_all']) for row in n['manual_actions']['characters']]
    assert list(block[h+8:h+13])==flags,'Squad posture never becomes a camera request'
    assert block[h+4]==n['squad_control']['last_keep'] and block[919840+14]==n['squad_control']['forced_owner']
    assert not any(block[h+5:h+8]) and not any(block[h+13:])
    return n

def validate_rejection(block,name):
    if name.startswith('reject/squad/'):assert block[0]==64
    else:parent.validate_rejection(block,name)
