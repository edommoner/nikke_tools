"""Explicit attack groups, independent target/order quantities; no battle trace input."""
import argparse,copy,hashlib,importlib.util,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from detail_coverage import a
from calculator.buff_manager import BuffManager
from attack_group_runtime import begin,finish,seal,dispatch
from effect_runtime import publish_impact,pool,state
from impact_specs import ActorHandle,ActorKind,HitFamily,HitOutcome,Impact,impact_command
import detail_gpu as g
spec=importlib.util.spec_from_file_location('attack_group_oracles',ROOT/'scripts/verify-gauge-detail.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
E=v.effect;N=v.NAMES

def effects():
    es=[E('no critical','buff','crit_rate',-15,'all_allies'),E('first','buff','atk_pct',10,event='multi_hit:2'),
        E('second','buff','atk_pct',20,event='multi_hit:1'),E('duplicate threshold','buff','atk_pct',5,event='multi_hit:2'),
        E('ordered damage','damage','damage',100,'target',event='multi_hit:3'),E('two timings','buff','atk_pct',7,event='multi_hit:3',max_stack=10),
        E('group count','buff','',0,event='multi_hit:2',max_stack=100)]
    es[-2]['trigger']['timing'].append('multi_hit:2')
    return [(e,N[0]) for e in es]+[(E('other owner','buff','atk_pct',3,event='multi_hit:1'),N[1])]

def packet(owner,identity,kind,actor,generation=1,outcome=2,credit=1):return Impact(N[owner],ActorHandle(kind,actor,generation),HitFamily.WEAPON,outcome,10 if outcome==2 else 0,credit,identity)

def cases():
    # ('query', owner, attack, independent first six fields and target handles)
    for name in ('duplicates-policy-outcomes','generation','notification-order'):
        mask=33 if name=='duplicates-policy-outcomes' else 32
        actions=[('begin',0,7,mask,1)]
        if name=='duplicates-policy-outcomes':
            impacts=[packet(0,7,0,0)]*12+[packet(0,7,1,1),packet(1,7,5,1),packet(0,7,5,1,outcome=0,credit=0),packet(0,7,5,2,outcome=1)]
            targets=[(0,0,1),(5,2,1)];want=[42,0,1]
        elif name=='generation':impacts=[packet(0,7,5,0),packet(0,7,5,0,2)];targets=[(5,0,1),(5,0,2)];want=[42,0,1]
        else:impacts=[packet(0,7,5,i) for i in range(3)];targets=[(5,i,1) for i in range(3)];want=[49,1420,1]
        actions += [('impact',p) for p in impacts]+[('query',0,7,[1,1,len(targets),mask,1,1],targets),('finish',0,7,1),('query',0,7,[0,0,0,0,0,1],[])]
        yield name,actions,want,None
    actions=[('begin',0,7,32,1),('begin',1,7,32,2),('impact',packet(0,7,5,0)),('impact',packet(1,7,5,1)),('impact',packet(1,7,5,2)),
             ('finish',0,7,1),('query',1,7,[1,2,2,32,1,2],[(5,1,1),(5,2,1)]),('begin',0,7,32,3),('impact',packet(0,7,5,0,2)),('finish',0,7,3),('finish',1,7,2)]
    yield 'owner-and-epoch-isolation',actions,[20,0,0],3
    targets=[(5,i,1) for i in range(17)]
    actions=[('begin',0,7,32,1)]+[('impact',packet(0,7,5,i)) for i in range(17)]+[('seal',0,7,1),('begin',0,7,32,2),('impact',packet(0,7,5,99,2)),
        ('sealed_query',0,7,1,0,[1,1,17,32,1,2],targets),('sealed_query',0,7,1,1,[1,1,17,32,1,2],targets),
        ('seal',0,7,2),('dispatch',0,7,2),('sealed_query',0,7,1,0,[1,1,17,32,0,2],targets),
        ('dispatch',0,7,1),('sealed_query',0,7,1,0,[0,0,0,0,0,2],[])]
    # The child's single-stack +20 refreshes at the parent's threshold1;
    # it is not an additional +20 stack in the final quantity.
    yield 'retained-parent-child-and-pages',actions,[49,1420,1],None



if __name__=='__main__':main()
