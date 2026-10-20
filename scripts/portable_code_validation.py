"""Same declared-name and legacy-lowering wire boundaries on CUDA and Metal."""
from portable_specs import LIMITS as L
from portable_runtime import double_words
def rejection_programs(cases,compile_case):
    case=next(c for c in cases if c['name']=='enemy-code-matrix-4-3');world=L['WORLD_META_BASE'];condition=L['CONDITION_BASE'];rows=[];expected=[]
    for name,offset,value in [('world-id-range',world,257),('world-beyond-name-count',world,3),('name-count-range',world+1,257),('zero-name-count',world+1,0),('reserved-meta',world+2,1),('predicate-zero',condition+1,0),('predicate-range',condition+1,257),('predicate-beyond-name-count',condition+1,3),('legacy-folded-boolean',condition,22)]:
        words,meta=compile_case(case);words[offset]=value;rows.append((words,meta));expected.append(dict(name='wire-enemy-code-'+name,status=64))
    words,meta=compile_case(case);words[condition+2:condition+4]=double_words(1)
    rows.append((words,meta));expected.append(dict(name='wire-enemy-code-numeric-argument',status=64))
    return rows,expected
