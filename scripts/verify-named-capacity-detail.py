"""All 256-bit duration-mask boundaries against independent CPU state/combat."""
import argparse,copy,hashlib,importlib.util,json,math,random,sys
from contextlib import nullcontext
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
v=load('named_capacity_oracle','scripts/verify-named-detail.py')
t=load('named_capacity_team','scripts/verify-team-hits-detail.py')
ctrl=load('named_capacity_control','scripts/verify-control-detail.py')
import detail_gpu as g
E=v.effect
def primitives():
    for desired in (31,32,63,64,95,96,127,128,159,160,191,192,223,224,254,255):
        for amount in (1,-.75):
            es=[E('padding '+str(i),'buff','crit_dmg',0,event='inactive') for i in range(desired-2)]
            es[0]['trigger']['condition']=['gauge_above:unregistered0:1','gauge_above:unregistered1:1']
            es += [E('mode','buff','atk_pct',10,duration=1),E('padding 1','buff','atk_pct',40,duration=1),E('padding 0','instant','named_buff_duration_extend',amount,event='burst_cast',target_effect='mode')]
            p=v.oracle.program(v.oracle.characters(v.NAMES),[(e,v.NAMES[0]) for e in es])
            assert p['states']['mode']==desired and len(p['states'])<=g.NE and len(p['effects'])<=g.NE
            mask=p['effects'][-1][g.EXTEND_MASK:g.EXTEND_MASK+g.MASK_WORDS]
            assert sum(int(word).bit_count() for word in mask)==1
            assert int(mask[desired//32])&(1<<(desired%32))
            script=[[0,0,0,i,0,-1,0,0] for i in range(5)]+[[.49,2,0,0,-1,0,0,0],[.5,0,3,0,0,-1,0,0],[1.1,2,0,0,-1,1,0,0],[2,2,0,0,-1,2,0,0]]
            yield 'extension-id-'+str(desired)+'-'+str(amount),p,script,[50,10 if amount>0 else 0,0]
def battles(long=False):
    names=t.p.NAMES
    for kind in (() if long else ('buff','dot')):
        for amount in (2,-.75):
            body=t.body_for(names,180 if long else 12,True)
            body.update(seed=12345,burst_policy='auto',shooting_policy='character',burst_gauge_mode='accumulate',_debug_random_state=True)
            padding=[E('battle padding '+str(i),'buff','crit_dmg',0,event='inactive') for i in range(129)]
            target='self' if kind=='buff' else 'target'
            subject=E('high '+kind,'buff' if kind=='buff' else 'damage','atk_pct' if kind=='buff' else 'dot_damage',90 if kind=='buff' else 100,target,duration=1,**({} if kind=='buff' else {'tick_interval':.25}))
            extension=E('high extension','instant','named_buff_duration_extend',amount,target,event='every:0.5s',max_trigger=1,target_effect='high '+kind)
            yield kind+'-'+str(amount),body,{names[0]:padding+[subject,extension]}
    for operation in ('tap','hold'):
        names=['리타','크러스트','크라운','앨리스','모더니아']
        body=t.body_for(names,180 if long else 35,True)
        body.update(seed=12345,burst_policy='auto',shooting_policy='character',burst_gauge_mode='accumulate',_debug_random_state=True)
        body['_named_controls']={'크러스트':{'tap_fire':{'rate':3.6,'release':.03,'full_charge_interval':5.5}} if operation=='tap' else {'sequence':[{'t':start,'action':'hold','until':start+3.3} for start in (0,4,8)]}}
        padding=[E('battle padding '+str(i),'buff','crit_dmg',0,event='inactive') for i in range(129)]
        yield 'real-Crust-'+operation,body,{names[0]:padding}
