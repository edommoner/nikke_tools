"""Static staged-DoT descriptors shared by CUDA/Metal; no CPU clock input."""
from staged_dot_specs import specification

def descriptors(effects):return [specification(effect,owner,effects) for effect,owner in effects]

def pack(words,index,spec,L,keys,double_words,parent):
    if spec is None:return
    at=L['STAGED_DEFINITION_BASE']+index*8
    count=spec.count if isinstance(spec.count,int) else 256+keys[spec.count]
    words[at:at+8]=[1,count,*double_words(spec.gap),*double_words(spec.post_delay),0 if spec.damage_stack is None else spec.damage_stack+1,parent+1]

def pack_index(words,specs,L):
    rows=[row for row,spec in enumerate(specs) if spec is not None]
    at=L['STAGED_INDEX_BASE'];words[at:at+1+len(rows)]=[len(rows),*rows]
