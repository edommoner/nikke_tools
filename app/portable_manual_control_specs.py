"""Explicit cover/hold literals; preserve legacy controls and wire capacities."""
import copy,math,struct
from portable_charge_control_specs import normalize_static_controls,compile_policy,SEQUENCE_BASE,OWNER_BASE
BASE=919744;WORDS=80;MAGIC=0x4d435631

def normalize(chars,attacks,enemy,control_mode='solo'):
    from calculator.timeline import CharState
    lowered=copy.deepcopy(chars);actions=[]
    for char,plain,attack in zip(chars,lowered,attacks,strict=True):
        control=char.get('control') or {}
        if any(control.get(k) for k in ('cover','reload','burst')):raise ValueError('Policy cover/reload/burst requires a separate common producer')
        cs=CharState(char,attack,enemy.get('code'));rows=[]
        for action in cs._ctrl_seq:
            kind=action.get('action')
            if kind not in ('hold','cover') or set(action)-({'action','t','until'} if kind=='hold' else {'action','t','duration'}):raise ValueError('Only explicit cover/hold sequence literals are supported')
            at=action.get('t',0);literal=action.get('until' if kind=='hold' else 'duration');value=-1. if literal is None else literal
            if literal is not None and (type(literal) not in (int,float) or not math.isfinite(literal) or not 0<=literal<=180):raise ValueError('Explicit times must be nonnegative finite literals or None')
            if type(at) not in (int,float) or not math.isfinite(at) or not 0<=at<=180 or type(value) not in (int,float) or not math.isfinite(value) or value!=-1 and not 0<=value<=180:raise ValueError('Invalid explicit cover/hold time')
            rows.append(dict(action=kind,time=float(at),value=float(value)))
        if len(rows)>8:raise ValueError('Explicit sequence capacity exceeded')
        actions.append(rows)
        if 'control' in plain:plain['control']['sequence']=[a for a in control.get('sequence',[]) if a.get('action')=='hold']
    result=normalize_static_controls(lowered,attacks,enemy,control_mode)
    for owner,rows in zip(result['owners'],actions,strict=True):owner['manual_sequences']=rows
    return result

def pack(normalized,effects,names,states,static_camera):
    tag=states.get('cover',0xffffffff)
    if type(tag) is not int or not (0<=tag<256 or tag==0xffffffff):raise ValueError('Invalid cover event identity')
    words=compile_policy(normalized,effects,names,states,static_camera);words[1]=3;words[6]=tag;words[7]=MAGIC
    for who,owner in enumerate(normalized['owners']):
        rows=owner['manual_sequences'];previous=-1
        if len(rows)>8:raise ValueError('Explicit sequence capacity exceeded')
        for row in rows:
            if set(row)!={'action','time','value'} or row['action'] not in ('hold','cover'):raise ValueError('Invalid explicit action')
            at,value=row['time'],row['value']
            if type(at) not in (int,float) or not math.isfinite(at) or not 0<=at<=180 or at<previous or type(value) not in (int,float) or not math.isfinite(value) or not (value==-1 or 0<=value<=180):raise ValueError('Invalid explicit action time')
            if row['action']=='hold' and owner['weapon_input']==2:raise ValueError('DOWN_Charge cannot hold')
            previous=at
        words[OWNER_BASE+who*8+1]=len(rows)
        start=SEQUENCE_BASE+who*8*8;words[start:start+64]=[0]*64
        for i,row in enumerate(rows):
            at=start+i*8;words[at:at+5]=[*struct.unpack('<II',struct.pack('<d',row['time'])),*struct.unpack('<II',struct.pack('<d',row['value'])),int(row['action']=='cover')]
    return words

def check_layout(root=None):
    from portable_coordinate_sampled_burst_wire import HEAD,HEAD_WORDS
    from portable_coordinate_physical_specs import LAYOUT as CF
    assert HEAD+HEAD_WORDS==BASE and BASE+WORDS<=CF['END']
    return dict(base=BASE,words=WORDS,owners=5,owner_words=16,extra_runtime_bytes=0,extra_output_words=0,input_version=3,sequence_capacity=8)
