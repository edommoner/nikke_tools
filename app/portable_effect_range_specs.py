"""Append-only literal radial-selection wire on the common event executor."""
import copy,math,struct
from effect_range_policy import MODEL,validate_effect
from portable_specs import LIMITS as L,FIELDS as F
SOURCE='gpu/effect_range_entry.slang'
BASE=L['INPUT_WORDS'];HEADER=32;TARGETS=8;ROW=16;INPUT=BASE+HEADER+TARGETS*ROW
OUTPUT=L['OUTPUT_WORDS'];OUTPUT_BASE=L['QUERY_BASE']+63*L['QUERY_WORDS'];MAGIC=0x45524731

def words(value):return list(struct.unpack('<II',struct.pack('<d',float(value))))
def number(row,at):return struct.unpack('<d',struct.pack('<II',*row[at:at+2]))[0]
def compile_program(chars,effects,script,base_atk,selection,*,model):
    from portable_runtime import compile_program as base
    if model!=MODEL or type(selection) is not dict or set(selection)!={'who','marker','time','base_radius','aim','targets'}:raise ValueError('Explicit named radial selection required')
    q=copy.deepcopy(selection);who=q['who'];targets=q['targets'];aim=q['aim']
    finite=lambda x:type(x) in (int,float) and math.isfinite(x)
    if (type(who) is not int or not 0<=who<5 or type(q['marker']) is not str or not q['marker'] or not finite(q['time']) or q['time']<0
        or not finite(q['base_radius']) or q['base_radius']<0 or type(aim) is not list or len(aim)!=2 or not all(map(finite,aim))
        or type(targets) is not list or not 1<=len(targets)<=TARGETS):raise ValueError('Invalid finite radial-selection context')
    effects=copy.deepcopy(list(effects));indices=[];lowered=[]
    for i,(e,owner) in enumerate(effects):
        if validate_effect(e):indices.append(i);lowered.append((dict(e,stat=''),owner))
        else:lowered.append((e,owner))
    if not indices:raise ValueError('Named range definitions required')
    if not script or any(type(c) not in (list,tuple) or len(c)!=8 or c[1]!=0 or c[0]>q['time'] for c in script):raise ValueError('External events before the final selection only')
    commands=copy.deepcopy(list(script))+[[q['time'],2,0,who,-1,0,0,0]]
    w,m=base(chars,lowered,commands,base_atk)
    if q['marker'] not in m['states']:
        if len(m['states'])>=L['DEFINITIONS']:raise ValueError('Range name symbol limit')
        m['states'][q['marker']]=len(m['states'])
    for i in indices:
        marker=effects[i][0]['target_effect']
        if marker not in m['states']:
            if len(m['states'])>=L['DEFINITIONS']:raise ValueError('Range name symbol limit')
            m['states'][marker]=len(m['states'])
        w[L['DEFINITION_BASE']+i*L['DEFINITION_WORDS']+F['KIND']]=0
        w[L['DEFINITION_BASE']+i*L['DEFINITION_WORDS']+F['TARGET_NAME']]=m['states'][marker]
    tail=[0]*(HEADER+TARGETS*ROW);tail[:5]=[MAGIC,1,who,m['states'][q['marker']],len(targets)]
    for i in indices:tail[16+i//32]|=1<<(i%32)
    for at,key in [(8,'time'),(10,'base_radius')]:tail[at:at+2]=words(q[key])
    tail[12:14]=words(aim[0]);tail[14:16]=words(aim[1])
    for i,shape in enumerate(targets):
        if type(shape) not in (list,tuple) or len(shape)!=7:raise ValueError('Literal shape kind/x/y/r/w/h/rotation required')
        kind,x,y,r,wid,h,rot=shape
        if type(kind) is not int or kind not in (1,2) or not all(map(finite,shape[1:])) or not (kind==1 and r>0 and wid==h==0 or kind==2 and r==0 and wid>0 and h>0):raise ValueError('Invalid radial collider')
        at=HEADER+i*ROW;tail[at]=kind
        for j,value in enumerate(shape[1:]):tail[at+2+j*2:at+4+j*2]=words(value)
    m['named_range_selection']=dict(selection=q,definitions=indices,model=MODEL)
    return w+tail,m

def decode(output,meta):
    row=list(output[OUTPUT_BASE:OUTPUT_BASE+32]);q=meta['named_range_selection']['selection']
    if row[:4]!=[MAGIC,q['who'],meta['states'][q['marker']],len(q['targets'])] or row[15]!=1 or number(row,12)!=q['time']:raise AssertionError('Named range output context differs')
    if row[14]>>len(q['targets']) or any(row[16+2*len(q['targets']):]):raise AssertionError('Unexpected radial-selection output padding')
    return dict(percent=number(row,4),factor=number(row,6),base_radius=number(row,8),radius=number(row,10),selected=[i for i in range(len(q['targets'])) if row[14]&(1<<i)],distances=[number(row,16+2*i) for i in range(len(q['targets']))])
