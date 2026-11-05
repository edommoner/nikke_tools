"""Full native battles plus ordered samples and complete MT state, both GPUs."""
import array, copy, hashlib, importlib.util, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
spec=importlib.util.spec_from_file_location('ally_random_base',ROOT/'research/verify-world-heal-share-short.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
suite,cross=base.suite,base.cross
from portable_ally_random_reference_cases import fixtures as reference_fixtures
from portable_ally_random_reference_contracts import verify
from world_ally_random_reference_native import observe
from portable_revival_specs import BASE,RNG,TRACE,TRACE_COUNT
from portable_specs import LIMITS as L


def fixtures():
    rows=reference_fixtures()
    zero=copy.deepcopy(rows[0]);zero['name']='ally-random-zero-request'
    zero['effects'][-1]['target']='allies_random:0'
    zero['contract'].update(target='allies_random:0',picked=[[]]*3,ks=[0]*3,before=[624]*3,after=[624]*3)
    limited=copy.deepcopy(rows[0]);limited['name']='ally-random-limited-trigger';limited['effects'][-1]['max_trigger']=2
    for key in ('pools','picked','ks','before','after'):limited['contract'][key]=limited['contract'][key][:2]
    return rows+[zero,limited]


def prepare():
    entries=[]
    for original in fixtures():
        case=copy.deepcopy(original)
        case['environment']['allied_seed']=case['seed']
        words,metadata,bindings=suite.compile_case(case)
        entries.append((case['name'],words,(case,metadata,bindings)))
    seed=entries[0][1];meta=L['RECIPIENT_META_BASE'];recipient=L['RECIPIENT_BASE']+8
    mutations=[('missing-tag',meta+2,0),('bad-tag',meta+2,1),('reserved',meta+5,1),
               ('no-combat',3,0),('mask',recipient+2,1),('exclude',recipient+3,1),
               ('order',recipient+4,1),('state-name',recipient+5,1),
               ('count',recipient+1,6),('debuff-selector',recipient,20)]
    for label,at,value in mutations:
        words=list(seed);words[at]=value
        entries.append(('reject/ally-random-'+label,words,None))
    packed=array.array('I',[len(entries)])
    for _,words,_ in entries:packed.extend(words)
    if sys.byteorder!='little':packed.byteswap()
    return entries,packed.tobytes()


def native_reference(domain):
    case,_,_=domain;native,trace=observe(case);verify(case,native)
    samples=native.pop('ally_random_reference')['samples']
    return dict(battle=native,skill_trace=trace,friendly_samples=samples)


def compare(block,domain):
    assert block[0]==0,(domain[0]['name'],'GPU status',block[0])
    expected=native_reference(domain)
    base.compare_expected(block,domain,expected)
    case=domain[0];target=case['contract']['target'];kind=25 if target.startswith('allies_broken') else 19
    count=block[BASE+6];assert count<=TRACE_COUNT,(case['name'],'sample trace capacity')
    samples=[]
    for i in range(count):
        at=TRACE+i*8;assert block[at]==3,(case['name'],'friendly-only trace kind')
        flags=block[at+1];pool=block[at+2];order=block[at+3]
        assert flags&7==case['contract']['caster'] and (flags>>3)&31==kind
        k=flags>>8;assert k<=5 and pool<32 and order>>15==0
        picked=[((order>>(j*3))&7)-1 for j in range(k)]
        samples.append(dict(pool=[j for j in range(5) if pool&(1<<j)],k=k,picked=picked,
                            before_index=block[at+4],after_index=block[at+5]))
    keys=('pool','k','picked','before_index','after_index')
    assert samples==[{k:r[k] for k in keys} for r in expected['friendly_samples']],(case['name'],'ordered GPU samples',samples)
    state=(3,tuple(block[RNG+8:RNG+632])+(block[RNG],),None)
    digest=hashlib.sha256(json.dumps(state,separators=(',',':'),allow_nan=False).encode()).hexdigest()
    assert digest==expected['friendly_samples'][-1]['after_sha256'],(case['name'],'complete MT state')
    assert block[RNG+2]==len(samples),(case['name'],'sample call count')
    assert block[BASE+7]==0,(case['name'],'friendly RNG must not enable revival')
    return expected


def validate_rejection(block,name):
    assert name.startswith('reject/ally-random-') and block[0]==64
