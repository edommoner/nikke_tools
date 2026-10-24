"""Literal coordinate descriptors and lifecycle commands; no scene simulation."""
import copy,math,struct
from pathlib import Path
LAYOUT=dict(ROWS=128,CAPACITY=127,ROW_WORDS=24,ROW_BASE=16,OPS=12,OP_WORDS=8,OP_BASE=3088,INPUT=3184,OUTPUT=32768,DESC=16,STATE=3088,QUERIES=4112,SNAPSHOT=1032)
MAGIC=0x434f4f31
OPS={'open':1,'close':2,'hit':3,'capture':4}
def bits(value):
    if type(value) not in (int,float) or not math.isfinite(value):raise ValueError('Finite coordinate number required')
    return list(struct.unpack('<II',struct.pack('<d',float(value))))
def layout_source():return '// Shared coordinate scene ABI, generated from portable_coordinate_scene_specs.\n'+''.join(f'static const uint C_{k}={v};\n' for k,v in LAYOUT.items())
def source_matches(root=None):return (Path(root or Path(__file__).resolve().parents[1])/'gpu/coordinate_scene_layout.slang').read_text()==layout_source()
def compile_scene(case,*,allow_core=False):
    from calculator.boss_pattern import validate
    if not source_matches():raise ValueError('Coordinate descriptor source layout drift')
    patterns=validate(copy.deepcopy(case['patterns']),coord=True)
    if not 1<=len(patterns)<=32 or any(p.kind not in (('parts','interrupt','idle','core') if allow_core else ('parts','interrupt','idle')) for p in patterns):raise ValueError('Coordinate component requires1..32 parts/interrupt/idle nodes')
    rows=[];ids={1:0,6:0}
    for p in patterns:
        for ordinal,t in enumerate(p.targets):
            kind=1 if p.kind=='parts' else 6;shape=t.shape
            rows.append(dict(kind=kind,identity=ids[kind],pattern=p.idx,ordinal=ordinal,label=t.name,shape=shape,z=t.z,hp=t.hp));ids[kind]+=1
    if len(rows)>LAYOUT['CAPACITY']:raise ValueError('Coordinate target capacity excludes the body slot')
    slots={(r['kind'],r['identity']):i+1 for i,r in enumerate(sorted(rows,key=lambda r:(r['kind'],r['identity'])))}
    words=[0]*LAYOUT['INPUT'];commands=case['commands']
    if not 1<=len(commands)<=LAYOUT['OPS']:raise ValueError('Coordinate command capacity exceeded')
    words[:5]=[MAGIC,1,len(rows),len(patterns),len(commands)]
    for i,r in enumerate(rows):
        sh=r['shape'];slot=slots[r['kind'],r['identity']];r['slot']=slot;at=LAYOUT['ROW_BASE']+i*LAYOUT['ROW_WORDS']
        words[at:at+6]=[r['kind'],r['identity'],r['pattern'],r['ordinal'],1 if sh.is_circle else 2,slot]
        words[at+6:at+22]=sum((bits(v) for v in (sh.x,sh.y,sh.r,sh.w,sh.h,sh.rot,r['z'],r['hp'])),[])
    previous=0
    for i,(op,time,index,amount) in enumerate(commands):
        if op not in OPS or type(index) is not int or index<0 or time<previous or time<0 or amount<0:raise ValueError('Invalid coordinate lifecycle command')
        if op=='capture' and (index!=0 or amount!=0) or op in ('open','close') and (index>=len(patterns) or amount!=0) or op=='hit' and index>=len(rows):raise ValueError('Coordinate command payload mismatch')
        at=LAYOUT['OP_BASE']+i*LAYOUT['OP_WORDS'];words[at:at+8]=[OPS[op],index,*bits(time),*bits(amount),0,0];previous=time
    return words,dict(rows=rows,patterns=patterns)
