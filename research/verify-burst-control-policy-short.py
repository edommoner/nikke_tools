"""Isolated shared policy proof against pinned BurstController methods.

Snapshots are probe inputs only, never an input path for the battle executor.
"""
import array
import copy
import itertools
import math
import random
import struct
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
import engine_worker
from calculator.timeline import BurstController
from portable_burst_control_specs import pack, MAGIC
import importlib.util
spec=importlib.util.spec_from_file_location('burst_policy_cross',ROOT/'research/summarize-portable-cross-gpu.py')
cross=importlib.util.module_from_spec(spec);spec.loader.exec_module(cross)
SOURCE='gpu/burst_control_policy_probe.slang'
INPUT_WORDS=224;OUTPUT_WORDS=32;STRICT_WIRE_DIMENSIONS=True
suite=SimpleNamespace(INPUT=INPUT_WORDS,OUTPUT=OUTPUT_WORDS)
NAMES=['one','two','three','four','five']

def bits(x):return list(struct.unpack('<II',struct.pack('<d',x)))

def base(**kw):
    d=dict(delays={},waits={},patterns={},sequence=None,stage=1,cycle=0,reentry=0,
           unavailable=0,explicit=0,stages=[1,1,2,3,4],when=1.,opened=0.,action=0.,ready=[0.]*5)
    d.update(kw);return d

def fixtures():
    rows=[]
    def add(label,**kw):rows.append((label,base(**kw)))
    add('automatic-reserves-first',ready=[8.,0.,0.,0.,0.])
    add('explicit-stage-allows-fallback',ready=[8.,0.,0.,0.,0.],explicit=2)
    add('reentry-allows-fallback',ready=[8.,0.,0.,0.,0.],reentry=1)
    add('empty-pattern-demotes',patterns={'one':[]})
    add('null-pattern-presence-allows-fallback',patterns={'one':None},ready=[8.,0.,0.,0.,0.])
    add('pattern-fallback-still-eligible',patterns={'one':[2],'two':[2],'five':[2]},ready=[0.,8.,0.,0.,8.])
    add('pattern-ignores-rank-in-prediction',patterns={'one':[2],'two':[1]},delays={'two':2.})
    add('delay-blocks-ready-alternative',patterns={'one':[1]},delays={'one':2.})
    add('delay-after-cooldown',patterns={'one':[1]},delays={'one':2.},when=3.,opened=0.,ready=[3.,0.,0.,0.,0.])
    add('delay-after-stage-open',delays={'one':2.},when=3.,opened=3.)
    add('wait-blocks-ready-alternative',patterns={'one':[1]},waits={'one':.5},ready=[1.5,0.,0.,0.,0.])
    add('wait-down-skipped',patterns={'one':[1]},waits={'one':.5},ready=[1.5,0.,0.,0.,0.],unavailable=1)
    add('all-unavailable-retains-action',unavailable=31,action=4.,ready=[2.,3.,4.,5.,6.],explicit=1)
    add('infinite-action-remains',unavailable=31,action=math.inf,explicit=1)
    add('missing-stage-blocks',stages=[2,2,3,3,0])
    add('explicit-empty-cycle-blocks',sequence=[{}])
    add('explicit-order-ignores-pattern',sequence=[{'1':['two','one'],'2':['three'],'3':['four']}],patterns={'one':[1]})
    add('explicit-omitted-stage-blocks',sequence=[{'2':['three']}])
    add('explicit-expired-automatic',sequence=[{}],cycle=1)
    add('explicit-A-owner',sequence=[{'1':['five'],'2':['five'],'3':['five']}])
    add('A-automatic-each-stage',stages=[4,0,0,0,0])
    add('empty-roster-prediction',stages=[1,1,1,1,1])
    add('last-explicit-pattern-bit',cycle=511,patterns={'one':[512],'two':[1]})
    add('past-explicit-pattern-bit',cycle=512,patterns={'one':[512],'two':[]})
    add('largest-every',cycle=0xfffffffd,patterns={'one':'every:4294967295'})
    add('null-pattern-keeps-stable-rank',patterns={'one':None,'two':None},explicit=1)
    # Numerical equality uses each canonical operation in its original order.
    for kind,threshold in [('ready',2.-1e-9),('delay',3.-1e-9),('wait',.5+1e-9)]:
        for direction,x in [('below',math.nextafter(threshold,-math.inf)),('exact',threshold),('above',math.nextafter(threshold,math.inf))]:
            kw=dict(patterns={'one':[1]})
            if kind=='ready':kw.update(when=x,ready=[2.,0.,0.,0.,0.])
            elif kind=='delay':kw.update(when=x,delays={'one':3.})
            else:kw.update(when=0.,ready=[x,0.,0.,0.,0.],waits={'one':.5})
            add(kind+'-'+direction,**kw)
    # All owner priorities and stage overrides, not just the first physical slot.
    for i,order in enumerate(itertools.permutations(NAMES)):
        add('explicit-permutation/'+str(i),stage=3,sequence=[{'1':list(order),'2':list(reversed(order)),'3':list(order)}],unavailable=i%32,ready=[0.,2.,0.,3.,0.])
    rng=random.Random(0x4255525354)
    pats=[None,[],[1,3,5],[2,32,33,512],'every:2','every:3']
    for i in range(192):
        add('mixed/'+str(i),stage=rng.randrange(1,4),cycle=rng.choice([0,1,2,31,32,511,512]),reentry=rng.randrange(2),
            patterns={n:rng.choice(pats) for n in NAMES if rng.randrange(2)},
            delays={n:rng.choice([0.,.1,.5,2.]) for n in NAMES},waits={n:rng.choice([False,.5,1.,3.]) for n in NAMES},
            stages=[rng.randrange(5) for _ in NAMES],ready=[rng.choice([0.,1.,1.5,2.,3.,8.]) for _ in NAMES],
            when=rng.choice([0.,1.,2.,3.]),opened=rng.choice([-1.,0.,1.,2.]),action=rng.choice([0.,1.,3.,math.inf]),
            unavailable=rng.randrange(32),explicit=rng.randrange(32))
    return rows

def compile_case(d):
    w=pack(NAMES,delays=d['delays'],waits=d['waits'],patterns=d['patterns'],sequence=d['sequence'])
    w += [0x42535031,d['stage'],d['cycle'],d['reentry'],d['unavailable'],d['explicit'],*d['stages'],0,
          *bits(d['when']),*bits(d['opened']),*bits(d['action']),*[v for x in d['ready'] for v in bits(x)],*([0]*20)]
    assert len(w)==INPUT_WORDS
    return w

def prepare():
    rows=[('burst-control-policy/'+name,compile_case(d),d) for name,d in fixtures()]
    seed=next(w for name,w,d in rows if name.endswith('/delay-blocks-ready-alternative'))
    for label,at,value in [('magic',0,0),('version',1,2),('disabled',2,0),('sequence-capacity',3,17),('owners',4,4),('row-size',5,23),('mask-size',6,15),('reserved',7,1),
        ('negative-delay',9,0xbff00000),('nan-delay',9,0x7ff80000),('wait-too-small',11,0x3fd00000),('wait-too-large',11,0x40100000),('pattern-kind',12,3),('empty-every',12,1),('unused-period',13,1),
        ('unused-pattern-mask',38,1),('presence',30,2),('row-reserved',31,1),('unused-sequence',128,1),('snapshot-magic',176,0),('stage',177,0),('cycle-overflow',178,0xffffffff),
        ('reentry',179,2),('unavailable',180,32),('explicit-mask',181,32),('stage-code',182,5),('snapshot-reserved',187,1),('nan-clock',189,0x7ff80000),('negative-ready',195,0xbff00000),('tail',223,1)]:
        w=list(seed);w[at]=value;rows.append(('reject/burst-control-policy/'+label,w,None))
    # Explicit-list holes, duplicates, invalid owner and high unused bits.
    for label,word in [('hole',1|(2<<6)),('duplicate',1|(1<<3)),('owner',6),('high-bit',1<<15)]:
        w=list(seed);w[3]=1;w[128]=word;rows.append(('reject/burst-control-policy/'+label,w,None))
    raw=array.array('I',[len(rows)])
    for _,w,_ in rows:raw.extend(w)
    if sys.byteorder!='little':raw.byteswap()
    return rows,raw.tobytes()

def native_reference(d):
    # Use original candidate/selection/prediction methods; only the effectful
    # cast and reentry callback are replaced, to expose the policy decision.
    c=object.__new__(BurstController)
    c._burst_pattern=copy.deepcopy(d['patterns']);c._explicit_burst_stage={n for i,n in enumerate(NAMES) if d['explicit']&(1<<i)}
    c._burst_sequence=copy.deepcopy(d['sequence']);c._burst_count=d['cycle'];c._burst_delay=d['delays'];c._wait_own_cooldown=d['waits']
    c.burst_order={str(stage):[n for i,n in enumerate(NAMES) if d['stages'][i] in (stage,4)] for stage in (1,2,3)}
    c._phase=('reenter:' if d['reentry'] else 'stage:')+str(d['stage'])
    c._stage_open_t=d['opened'];c._next_action_t=d['action'];c.burst_ready_at=dict(zip(NAMES,d['ready']));c._cd_wait_candidates=None
    picked=[]
    c._cast_burst=lambda name,*args:(picked.append(name) or [])
    c._check_reenter=lambda *args:None
    bm=SimpleNamespace(is_stunned=lambda name:bool(d['unavailable']&(1<<NAMES.index(name))),is_down=lambda name:False)
    if c._burst_sequence is not None and c._burst_count<len(c._burst_sequence):order=c._burst_sequence[c._burst_count].get(str(d['stage']),[])
    else:order=sorted(c._automatic_candidates(str(d['stage']),reenter_slot=bool(d['reentry'])),key=lambda name:c._pattern_rank(name,c._burst_count+1))
    c._try_use_stage(str(d['stage']),d['when'],bm,{},reenter_slot=bool(d['reentry']))
    result=dict(owner=NAMES.index(picked[0]) if picked else 5,wait_mask=sum(1<<NAMES.index(n) for n in c._cd_wait_candidates or []),action=bits(c._next_action_t),order=[NAMES.index(n)+1 for n in order])
    c._phase='idle';c._max_burst_count=None;c._gauge_mode='accumulate';c.config={}
    result['prediction']=bits(c._predict_next_fb_start(d['when']))
    return result

def expected(n):
    w=[0]*OUTPUT_WORDS;w[:7]=[0,MAGIC,n['owner'],n['wait_mask'],*n['action'],len(n['order'])];w[7:7+len(n['order'])]=n['order'];w[12:14]=n['prediction'];return w

def compare(block,domain):
    n=native_reference(domain)
    assert list(block)==expected(n),('burst control policy',n,list(block))
    return n

def validate_rejection(block,name):assert name.startswith('reject/burst-control-policy/') and list(block)==[64]+[0]*(OUTPUT_WORDS-1)
