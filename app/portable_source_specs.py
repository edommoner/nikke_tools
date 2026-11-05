"""Pack explicit shared periodic-source descriptors, never runtime populations."""
from periodic_source_specs import specification,MAX_SOURCES

def validate_sources(effects):
    keys={(owner,spec.name) for effect,owner in effects if (spec:=specification(effect)) is not None}
    if len(keys)>MAX_SOURCES:raise ValueError('Periodic source capacity exceeded')

def pack(words,index,row,L,effect,double_words):
    spec=specification(effect)
    if spec is None:return
    at=L['SOURCE_DEFINITION_BASE']+index*L['SOURCE_DEFINITION_WORDS']
    words[at:at+8]=[int(row[304]),len(spec.lifetimes),int(spec.legacy),0,*double_words(spec.base),*double_words(spec.reduction)]
    for slot,lifetime in enumerate(spec.lifetimes):words[at+8+slot*2:at+10+slot*2]=double_words(lifetime)
