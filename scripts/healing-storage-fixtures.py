"""Actual CPU simulations exercise the new buffer, never a GPU parity claim."""
import hashlib,importlib.util,json,sys
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
    sp=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
sys.path.insert(0,str(ROOT/'app'))
import engine_worker
import detail_gpu as g
v=load('storage_cpu_squad_oracle','scripts/verify-survival-scaling.py');N=v.N;B=v.B;E=v.E;BM=v.BuffManager
def fixtures():
    for case in ('empty','overflow','damage','drain','expiry','stacked','refresh','shield-before-storage'):
        b=v.body(1.2);x={n:[] for n in N};kw={}
        if case=='expiry':kw['duration']=.35
        if case=='stacked':kw.update(event='every:0.1s',max_stack=3)
        if case=='refresh':kw.update(event='every:0.4s')
        x[N[0]].append(B('stored recovery','heal_overcharge_store',5,**kw))
        if case!='empty':x[N[1]].append(E('heal body','instant','heal_hp_pct',20,N[0],event='every:0.3s' if case=='refresh' else 'every:0.2s',max_trigger=3 if case=='refresh' else 1))
        if case in ('damage','shield-before-storage'):b['enemy']['patterns']=[dict(id='storage hit',kind='attack',delay=.3,until={'time':.7},spec=dict(coeff=100,atk=100000,target='slot:1',hits=2,interval=.2,pierce=False))]
        if case=='shield-before-storage':x[N[0]].append(B('outer shield','shield_from_max_hp_pct',20))
        if case=='drain':x[N[0]].append(E('body drain','instant','current_hp_reduce',2,event='every:0.3s',max_trigger=1))
        yield 'storage-'+case,b,x
    for subject,favorite in [('앵커 : 이노센트 메이드',0),('센티',0),('센티',3),('소라',0),('마르차나',0)]:
        names=[subject,'라푼젤' if subject=='센티' else '프리카','리타','앨리스','모더니아'];b=v.body(30,True,names);b['burst_gauge_mode']='accumulate'
        b['enemy']['patterns']=[dict(id='small incoming',kind='attack',delay=.2,until={'time':30},spec=dict(coeff=100,atk=60000,target='all',hits=50,interval=.5,pierce=True))]
        if favorite:b['profile']['chars'][subject].update(favorite_stage=favorite,collection_stage='SR15')
        x={}
        if subject=='소라':
            b['enemy']['parts']=[dict(name='storage-trigger-part'+str(i),hp=5,reach=(i%5)+1) for i in range(6)]
            x={'리타':[E('authored part-destruction stimulus','damage','damage',100,'all_enemies',event='every:0.5s',max_trigger=1,hits_parts=True)]}
        yield 'raw-storage-'+subject+('-favorite3' if favorite else ''),b,x
