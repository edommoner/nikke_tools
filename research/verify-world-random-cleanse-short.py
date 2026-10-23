"""Shared native battles, actual ordered samples and full MT state, both GPUs."""
import array,hashlib,importlib.util,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
s=importlib.util.spec_from_file_location('random_cleanse_base',ROOT/'research/verify-world-heal-share-short.py');base=importlib.util.module_from_spec(s);s.loader.exec_module(base)
suite,cross=base.suite,base.cross
from portable_random_cleanse_cases import fixtures as basic
from portable_random_cleanse_mixed_cases import fixtures as mixed
from portable_random_cleanse_contracts import verify
from portable_random_cleanse_mixed_contracts import verify as verify_mixed
from portable_random_cleanse_budget_cases import fixtures as budget
from portable_random_cleanse_budget_contracts import verify as verify_budget
from world_random_cleanse_native import observe
from portable_runtime import decode
from portable_revival_specs import BASE,RNG,TRACE,TRACE_COUNT
from portable_specs import LIMITS as L,FIELDS as F
from portable_random_cleanse_roster_cases import fixtures as real
from world_random_cleanse_roster_native import observe as observe_real
from portable_random_cleanse_roster_contracts import verify as verify_real
s=importlib.util.spec_from_file_location('random_cleanse_roster',ROOT/'research/verify-world-projectile-rosters.py');roster=importlib.util.module_from_spec(s);s.loader.exec_module(roster)

def prepare():
    rows=[]
    for c in basic()+mixed():
        c['environment']['allied_seed']=c['seed'];w,m,p=suite.compile_case(c);rows.append((c['name'],w,(c,m,p)))
    for c in real():
        p=roster.engine_worker.evaluate(dict(c['body'],_portable_static_inputs=True));w,m=roster.compile_projectile_battle(p);rows.append((c['name'],w,(c,m,p,w)))
    for c in budget():
        c['environment']['allied_seed']=c['seed'];w,m,p=suite.compile_case(c);rows.append((c['name'],w,(c,m,p)))
    seed=rows[1][1];row=len(rows[1][2][0]['effects'])-1;at=L['RECIPIENT_BASE']+row*8;meta=L['RECIPIENT_META_BASE']
    assert seed[at]==20
    mutations=[('count',at+1,6),('mask',at+2,1),('exclude',at+3,1),('order',at+4,1),('name',at+5,1),('stat-key',at+6,256),('flags',at+7,1),('missing-tag',meta+2,0),('bad-tag',meta+2,1),('no-combat',3,0),('no-world',L['WORLD_FRAME_INPUT_BASE'],0),('wrong-kind',L['DEFINITION_BASE']+row*L['DEFINITION_WORDS']+F['KIND'],22)]
    for label,pos,value in mutations:
        w=list(seed);assert w[pos]!=value;w[pos]=value;rows.append(('reject/random-cleanse-'+label,w,None))
    packed=array.array('I',[len(rows)])
    for _,w,_ in rows:packed.extend(w)
    if sys.byteorder!='little':packed.byteswap()
    return rows,packed.tobytes()

def native_reference(domain):
    c=domain[0]
    if 'body' in c:
        n,t=observe_real(c);verify_real(c,n);recorded=n.pop('random_cleanse');assert len(recorded['seed_sha256'])==1;n['friendly_initial_sha256']=recorded['seed_sha256'][0];n['friendly_samples']=recorded['samples'];return n
    n,t=observe(c);(verify_budget if 'dispatches' in c['contract'] else verify_mixed if 'pools' in c['contract'] else verify)(c,n)
    observed=n.pop('random_cleanse')
    assert len(observed['seed_sha256'])==1
    return dict(battle=n,skill_trace=t,friendly_samples=observed['samples'],friendly_initial_sha256=observed['seed_sha256'][0],remaining=observed['calls'][-1]['after'] if observed['calls'] else c['contract']['remaining'])

def compare(block,domain):
    c,m,p=domain[:3];expected=native_reference(domain)
    if 'body' in c:
        _,_,_,diff=roster.compare(block,p,(domain[3],m),expected['battle'],expected['projectile_shots']);assert block[0]==0 and not diff,(c['name'],block[0],diff[:8])
    else:base.compare_expected(block,domain,expected)
    samples=[]
    for i in range(block[BASE+6]):
        assert i<TRACE_COUNT
        at=TRACE+i*8;flags=block[at+1]
        if block[at]!=3:continue # Revival transition records have their own battle comparator.
        assert flags&7==c['contract']['owner'] and (flags>>3)&31==20
        k=flags>>8;assert k<=5 and block[at+2]<32 and block[at+3]>>15==0
        samples.append(dict(pool=[j for j in range(5) if block[at+2]&(1<<j)],k=k,picked=[((block[at+3]>>(j*3))&7)-1 for j in range(k)],before_index=block[at+4],after_index=block[at+5]))
    keys=('pool','k','picked','before_index','after_index')
    assert samples==[{k:r[k] for k in keys} for r in expected['friendly_samples']],(c['name'],'ordered samples',samples)
    state=(3,tuple(block[RNG+8:RNG+632])+(block[RNG],),None)
    expected_state=expected['friendly_samples'][-1]['after_sha256'] if expected['friendly_samples'] else expected['friendly_initial_sha256']
    assert hashlib.sha256(json.dumps(state,separators=(',',':'),allow_nan=False).encode()).hexdigest()==expected_state,(c['name'],'full MT including zero-sample initial state')
    assert block[RNG+2]==len(samples),(c['name'],'sample count')
    if 'body' in c:return expected
    remaining={}
    for carrier in decode(block[:159744],m)['carriers']:
        if carrier['active'] and not carrier['lazy_pending']:
            remaining[c['effects'][carrier['definition']]['name']]=[j for j in range(5) if carrier['recipients']&(1<<j)]
    assert remaining==expected['remaining'],(c['name'],'resident memberships',remaining,expected['remaining'])
    return expected

def validate_rejection(block,name):assert name.startswith('reject/random-cleanse-') and block[0]==64
