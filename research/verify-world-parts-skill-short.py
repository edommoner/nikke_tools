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
RANGE=set() # Reached skill packets are connected; physical remains closed.
HOST_REJECT=set()
PHYSICAL_REJECT='interrupt-physical-reach-not-ported'
RAW_REJECT={'interrupt-source-projectile-alias','interrupt-source-part-alias','interrupt-source-noncanonical-id'}
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
    original=next(x for x in rows if x['name']=='parts-skill-interrupt-only')
    for label in ('delayed-reopen','unbreakable','capacity127'):
        c=copy.deepcopy(original);c['name']='interrupt-source-'+label
        p=c['patterns'][0]
        if label=='delayed-reopen':p.update(delay=.05,until={'time':.05},after=['start','interrupt'],repeat=2)
        if label=='unbreakable':p['targets'][0]['hp']=0
        if label=='capacity127':p['targets']=[dict(name='stop-'+str(i),hp=1e8,reach=1) for i in range(127)]
        rows.append(c)
    c=copy.deepcopy(original);c['name']=PHYSICAL_REJECT
    c['combat']['weapons'][0].update(mode='charge',base_weapon_type='RL',interval=.1,min_cycle=.05,charge=.05)
    rows.append(c)
    from portable_interrupt_reach_cases import fixtures as interrupt_cases
    rows.extend(interrupt_cases())
    return rows
def prepare():
    verify_layout(LIMITS);entries=[];packed=array.array('I',[46])
    for case in fixtures():
        words,meta,bindings=suite.compile_case(case)
        rejected=case['name'] in DEFERRED|RANGE|{PHYSICAL_REJECT}
        entries.append((('reject/' if rejected else 'native/')+case['name'],words,None if rejected else (case,meta,bindings)))
        packed.extend(words)
    seed=next(e[1] for e in entries if e[0]=='native/parts-skill-interrupt-only');at=LIMITS['WORLD_ACTOR_BINDING_BASE']+8
    for name,offset,value in [('interrupt-source-projectile-alias',0,2),('interrupt-source-part-alias',2,1),('interrupt-source-noncanonical-id',1,1)]:
        words=list(seed);words[at+offset]=value;entries.append(('reject/'+name,words,None));packed.extend(words)
    assert len(entries)==46 and sum(e[2] is not None for e in entries)==41
    if sys.byteorder!='little':packed.byteswap()
    return entries,packed.tobytes()
def native_reference(domain):
    native,trace=observe(domain[0]);verify(domain[0],native)
    if domain[0]['name']=='parts-skill-periodic-part-counter-family':
        rows=native['target_counters']['completions']
        if len(rows)!=1 or rows[0]['impact']['family']!=2 or rows[0]['actor']['kind']!=1:raise AssertionError('Native DoT part counter contract')
    # Profile-only stream has no battle serializer. Retain the complete existing
    # state, target generations/extra credit, healing and named skill trace.
    interrupt=native.get('parts_skill_accounting') if any(p.get('kind')=='interrupt' for p in domain[0].get('patterns',[])) else None
    for key in ('parts_skill_events','parts_skill_lifecycle','parts_skill_accounting'):native.pop(key,None)
    result=dict(battle=native,skill_trace=trace)
    if interrupt is not None:result['interrupt']=interrupt
    return result
def compare(block,domain):
    expected=native_reference(domain)
    if 'interrupt' in expected:
        import struct
        def number(at):return struct.unpack('<d',struct.pack('<II',*block[at:at+2]))[0]
        extra=[]
        for slot,b in enumerate(domain[2]):
            gen=block[LIMITS['WORLD_ACTOR_POOL_STATE_BASE']+slot*16]
            if int(b.kind)!=6 or gen==0:continue
            at=LIMITS['COUNTER_LANDING_EXTRA_BASE']+slot*4
            extra.append(dict(identity=b.identity,generation=gen,extra_hits=block[at],extra_dealt=number(at+2)))
        actual=dict(interrupt_damage=[number(785424+i*2) for i in range(len(expected['interrupt']['interrupt_damage']))],extra=extra)
        assert actual==expected['interrupt'],(domain[0]['name'],'interrupt accounting',actual,expected['interrupt'])
    return base.compare_expected(block,domain,expected)
def validate_rejection(block,name):
    if name.removeprefix('reject/') not in DEFERRED|RANGE|{PHYSICAL_REJECT}|RAW_REJECT or block[0]!=64:
        raise AssertionError((name,block[0]))
