"""Shared HP skill witnesses through the existing whole-battle comparator."""
import array,copy,importlib.util,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
spec=importlib.util.spec_from_file_location('skill_hp_basis_base',ROOT/'research/verify-world-heal-share-short.py');base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
suite,cross=base.suite,base.cross
from portable_skill_hp_basis_cases import fixtures
from portable_skill_hp_basis_contracts import verify
from world_skill_hp_basis_native import observe
from portable_skill_hp_basis_specs import MAGIC,OFFSET
from portable_specs import LIMITS as L

def prepare():
    entries=[]
    for case in fixtures():
        if case['contract'].get('reference_model_gap'):continue
        words,metadata,bindings=suite.compile_case(case);entries.append((case['name'],words,(case,metadata,bindings)))
    case,_,_=entries[1][2];seed=entries[1][1];row=len(case['effects'])-1
    at=L['MODE_BASE']+row*L['MODE_WORDS']+OFFSET
    def number(value):return list(struct.unpack('<II',struct.pack('<d',value)))
    mutations=[('no-combat',3,[0]),('unknown-tag',at,[MAGIC^1]),('zero-mode',at+1,[0]),('unknown-mode',at+1,[3]),('negative',at+2,number(-1)),('nan',at+2,number(float('nan'))),('infinite',at+2,number(float('inf'))),('too-large',at+2,number(1000001))]
    for label,offset,values in mutations:
        words=list(seed);words[offset:offset+len(values)]=values;entries.append(('reject/skill-hp-basis-'+label,words,None))
    words=list(seed);buff=L['MODE_BASE']+OFFSET;words[buff:buff+4]=words[at:at+4];entries.append(('reject/skill-hp-basis-wrong-kind',words,None))
    for gap in fixtures():
        if not gap['contract'].get('reference_model_gap'):continue
        try:suite.compile_case(gap)
        except ValueError as error:
            if 'reference_model_gap' not in str(error):raise
        else:raise AssertionError('Deferred HP basis must fail host admission')
        ordinary=copy.deepcopy(gap);hit=ordinary['effects'][-1];mode=1 if hit['scaling']=='max_hp_additive' else 2;pct=hit.pop('scaling_hp_pct');hit.pop('scaling')
        words,_,_=suite.compile_case(ordinary);offset=L['MODE_BASE']+(len(gap['effects'])-1)*L['MODE_WORDS']+OFFSET
        words[offset:offset+4]=[MAGIC,mode,*number(pct)];entries.append(('reject/'+gap['name'],words,None))
    packed=array.array('I',[len(entries)])
    for _,words,_ in entries:packed.extend(words)
    if sys.byteorder!='little':packed.byteswap()
    return entries,packed.tobytes()

def native_reference(domain):
    case,_,_=domain;native,trace=observe(case);verify(case,native);native.pop('skill_hp_basis_queries');native.pop('parts_skill_events')
    return dict(battle=native,skill_trace=trace)

def compare(block,domain):
    return base.compare_expected(block,domain,native_reference(domain))

def validate_rejection(block,name):
    assert name.startswith('reject/skill-hp-basis-') and block[0]==64
