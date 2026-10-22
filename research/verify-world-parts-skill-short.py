"""Part-skill native contracts on the same full battle comparator as all effects."""
import array,copy,importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
spec=importlib.util.spec_from_file_location('parts_battle_base',ROOT/'research/verify-world-heal-share-short.py');base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
suite,cross=base.suite,base.cross
from world_parts_skill_native import observe
from portable_parts_skill_contracts import verify
from portable_parts_skill_specs import verify_layout
from portable_specs import LIMITS
# Explicit remaining adapters: reject, never treat a missing extra packet as success.
DEFERRED={'parts-skill-extra-deferred-burst3-reference-gap'}
RANGE={'parts-skill-extra-'+n for n in ('pierce-parts','explosion-parts','explosion-range100','explosion-without-marker','interrupt-lifesteal-unsaturated')}
HOST_REJECT=RANGE|{'parts-skill-interrupt-only','parts-skill-parts-and-interrupt'}
def fixtures():
    from portable_parts_skill_cases import fixtures as a
    from portable_parts_skill_extra_cases import fixtures as b
    from portable_parts_skill_lifecycle_cases import fixtures as c
    rows=a()+b()+c()
    extra=copy.deepcopy(next(x for x in rows if x['name']=='parts-skill-extra-periodic-three-ticks'))
    extra['name']='parts-skill-periodic-part-counter-family'
    from target_counter_cases import marker
    counter=marker(name='dot-part-marker',threshold=1,actor=dict(kind='part',identity=0,generation=1),families=['dot'])
    counter['target']='boss';counter['trigger']['timing']=['battle_start']
    extra['effects'].insert(-1,counter);extra['owners'].insert(-1,0);rows.append(extra)
    return rows
def prepare():
    verify_layout(LIMITS);entries=[];packed=array.array('I',[26])
    for case in fixtures():
        if case['name'] in HOST_REJECT:
            try:suite.compile_case(case)
            except ValueError as error:
                if 'actor connection: interrupt' not in str(error):raise
            else:raise AssertionError('Unported interrupt adapter silently accepted')
            continue
        words,meta,bindings=suite.compile_case(case)
        rejected=case['name'] in DEFERRED|RANGE
        entries.append((('reject/' if rejected else 'native/')+case['name'],words,None if rejected else (case,meta,bindings)))
        packed.extend(words)
    assert len(entries)==26 and sum(e[2] is not None for e in entries)==25
    if sys.byteorder!='little':packed.byteswap()
    return entries,packed.tobytes()
def native_reference(domain):
    native,trace=observe(domain[0]);verify(domain[0],native)
    if domain[0]['name']=='parts-skill-periodic-part-counter-family':
        rows=native['target_counters']['completions']
        if len(rows)!=1 or rows[0]['impact']['family']!=2 or rows[0]['actor']['kind']!=1:raise AssertionError('Native DoT part counter contract')
    # Profile-only stream has no battle serializer. Retain the complete existing
    # state, target generations/extra credit, healing and named skill trace.
    for key in ('parts_skill_events','parts_skill_lifecycle','parts_skill_accounting'):native.pop(key,None)
    return dict(battle=native,skill_trace=trace)
def compare(block,domain):
    return base.compare_expected(block,domain,native_reference(domain))
def validate_rejection(block,name):
    if name.removeprefix('reject/') not in DEFERRED|RANGE or block[0]!=64:
        raise AssertionError((name,block[0]))
