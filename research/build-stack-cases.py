"""Authored stack stimuli shared unchanged by CUDA and Metal."""
import copy,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def buff(**kw):
    e=dict(name='seed',source='스킬1',type='buff',stat='atk_pct',fixed_value=1,target='self',duration=2,max_stack=5,polarity='beneficial',trigger=dict(timing=['event:full_reload'],condition=[]));e.update(kw);return e

def op(stat,value=1,**kw):
    e=dict(name='operation',source='스킬1',type='buff' if stat=='buff_max_stack_add' else 'instant',stat=stat,fixed_value=value,target='self',target_effect='seed',trigger=dict(timing=['on_attack'],condition=[]));e.update(kw);return e

def notify(t,event=19,who=0):return [t,0,event,who,0,-1,0,0]
def query(t,i=0,target=0):return [t,2,0,0,target,i,0,0]
def case(name,effects,script,**kw):
    c=dict(name='stack-'+name,effects=effects,expected_queries=[dict(time=row[0]) for row in script if row[1]==2],combat=dict(weapons=[dict(enabled=False) for _ in range(5)],targets=[dict(hp=100000)]),script=script,stack_reference=True);c.update(kw);return c

def fixtures():
    rows=[]
    values=[0.,-0.,.5,-.5,1.9,-1.9,1e308,-1e308]
    for stat in ('buff_stack_add','buff_stack_remove','debuff_stack_add','debuff_stack_remove'):
        for named in ([True] if stat.startswith('buff_') else [False,True]):
            for v in values:
                effect=buff(polarity='harmful' if stat.startswith('debuff') else 'beneficial')
                operation=op(stat,v,target_effect='seed' if named else '')
                rows.append(case(stat+'-'+('named-' if named else 'generic-')+repr(v),[effect,operation],[notify(0),notify(0),notify(0),notify(1,7),query(1)]))
    for stat in ('buff_stack_add','buff_stack_remove','debuff_stack_add','debuff_stack_remove','buff_max_stack_add'):
        rows.append(case(stat+'-immune',[buff(),buff(name='immune',stat='stack_change_immune',max_stack=1,duration=-1),op(stat,2)],[notify(0),notify(1,7),query(1)]))
    for v in [0.,-0.,.5,-.5,-1.,3.9,9.]:
        rows.append(case('init-'+repr(v),[buff(trigger=dict(timing=['event:full_reload'],condition=[])),op('buff_stack_init',v)],[notify(1,7),query(1)]))
    e=buff(duration_bullets=3,max_trigger=0,trigger=dict(timing=['event:full_reload'],condition=['during_full_burst']))
    rows.append(case('init-bypasses-target-gates-and-bullet-init',[e,op('buff_stack_init',3)],[notify(1,7),query(1)]))
    rows.append(case('single-zero-normal-refresh',[buff(max_stack=1),op('debuff_stack_remove',1)],[notify(0),notify(.5,7),query(.5),notify(1),query(1,1)]))
    for target in ('self','all_allies'):
        rows.append(case('max-shared-'+target,[buff(target='all_allies'),op('buff_max_stack_add',2,target=target)],[notify(0),notify(1,7),query(1)]))
    from stack_case_extensions import cases as extended
    rows+=extended(buff,op,notify,query,case)
    from stack_case_physical import cases as physical
    rows+=physical(buff,op,notify,query,case)
    return rows
if __name__=='__main__':
    rows=fixtures();(R/'tests/fixtures/portable-stacks.json').write_text(json.dumps(dict(cases=rows),ensure_ascii=False,indent=2)+'\n');print('Authored stack cases',len(rows))
