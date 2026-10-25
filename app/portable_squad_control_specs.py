"""Authored squad operations: GPU chooses the live owner and cover recipients."""
import math,struct
INPUT_BASE=109656
INPUT_WORDS=136
HEADER=8
ROWS=16
ROW_WORDS=8
MAGIC=0x53515631
SOURCE='gpu/world_coordinate_squad_entry.slang'

def number(value,*,duration=False):
    if duration and value is None:return list(struct.unpack('<II',struct.pack('<d',-1.)))
    if type(value) not in (int,float) or not math.isfinite(value) or not 0<=value<=180:raise ValueError('Finite bounded squad literal required')
    return list(struct.unpack('<II',struct.pack('<d',value)))

def normalize(sequence,names):
    if not isinstance(sequence,list) or len(sequence)>ROWS or len(names)!=5 or len(set(names))!=5:raise ValueError('Squad sequence capacity or roster invalid')
    normalized=[]
    for action in sequence:
        if not isinstance(action,dict):raise ValueError('Squad action must be an object')
        kind=action.get('action')
        allowed={'t','action','target'} if kind=='focus' else {'t','action','duration'} if kind=='cover_all' else set()
        if not allowed or set(action)-allowed:raise ValueError('Unknown squad action or field')
        t=action.get('t',0);number(t)
        if kind=='focus':
            name=action.get('target') or ''
            if name not in ['',*names]:raise ValueError('Unknown squad focus target')
            normalized.append(dict(t=t,kind=1,target=names.index(name)+1 if name else 0,duration=0))
        else:
            duration=action.get('duration');number(duration,duration=True)
            normalized.append(dict(t=t,kind=2,target=0,duration=duration))
    # Python's stable sort matches canonical _check_squad_seq, including equal time.
    return sorted(normalized,key=lambda a:a['t'])

def pack(sequence,names):
    actions=normalize(sequence,names);words=[MAGIC,1,len(actions),ROWS,ROW_WORDS,0,0,0]+[0]*(ROWS*ROW_WORDS)
    for i,a in enumerate(actions):
        at=HEADER+i*ROW_WORDS
        words[at:at+ROW_WORDS]=[*number(a['t']),a['kind'],a['target'],*number(a['duration'],duration=True),0,0]
    return words

def empty():return pack([],['0','1','2','3','4'])
