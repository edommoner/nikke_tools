"""Authored cover/camera stimuli before shared lowering; no native schedules."""
import copy
from portable_ammo_equivalent_cases import fixtures as ammo_fixtures
from portable_burst_recipient_cases import instant
from world_enemy_attack_cases import field
from world_frame_native import roster_names


def fixtures():
    base=copy.deepcopy(ammo_fixtures()[0]);base.pop('contract');rows=[]
    def add(label,condition,*,timing='on_attack',duration=10,camera=(),results=(True,True,True),damage=(6000,6600,7200),stack=3,owner=0):
        c=copy.deepcopy(base);c['name']='state-predicate-'+label
        if owner!=0:
            c['combat']['weapons'][0].update(mode='charge',charge=10,interval=10,min_cycle=10)
            c['combat']['weapons'][owner].update(mode='auto',interval=.1,min_cycle=.1,capacity=10)
        names=roster_names(c);c.update(camera=[names[i] for i in camera],camera_mode='shared' if len(camera)>1 else 'single')
        c['effects']=[field('crit_rate',-100,'self','no-crit'),field('atk_pct',10,'self','state-witness',timing=timing,duration=duration,max_stack=128,condition=[condition])];c['owners']=[owner,owner]
        c['contract']=dict(owner=owner,condition=condition,results=None if results is None else list(results),damage=list(damage),stack=stack,ammo=7,cover_query_owners=None)
        rows.append(c);return c
    add('cover-intact','no_broken_cover_ally')
    add('cover-last-owner','no_broken_cover_ally',owner=4)
    def attack(c,slot,atk=2000,when=.05,pierce=False):
        c['patterns']=[dict(id='authored-hit',kind='attack',delay=when,spec=dict(atk=atk,coeff=100,target='slot:'+str(slot+1),ignore_taunt=True,pierce=pierce))]
    def reload(c,owner=4):
        c['effects'].insert(1,instant('force_reload',1,roster_names(c)[owner],'authored-reload'));c['owners'].insert(1,owner);c['combat']['weapons'][owner]['reload']=1
    c=add('cover-ally-breaks','no_broken_cover_ally',results=(True,False,False),damage=(6000,6600,6600),stack=1);reload(c);attack(c,4)
    c=add('cover-first-ally-breaks','no_broken_cover_ally',results=(True,False,False),damage=(6000,6600,6600),stack=1);reload(c,1);attack(c,1)
    c=add('cover-broken-then-revived','no_broken_cover_ally',results=(True,False,True),damage=(6000,6600,6600),stack=2);reload(c);attack(c,4);c['effects'].append(instant('cover_revive',100,roster_names(c)[4],'authored-revive','on_attack_count:2'));c['owners'].append(0)
    c=add('cover-broken-then-dead','no_broken_cover_ally',results=(True,False,True),damage=(6000,6600,6600),stack=2);reload(c);attack(c,4);c['patterns'].append(dict(id='authored-lethal',kind='attack',delay=.15,spec=dict(atk=1e12,coeff=100,target='slot:5',ignore_taunt=True)))
    c=add('cover-dead-with-intact-cover','no_broken_cover_ally');attack(c,4,1e12)
    c=add('cover-piercing-break','no_broken_cover_ally',results=(True,False,False),damage=(6000,6600,6600),stack=1);reload(c);attack(c,4,1500,pierce=True)
    c=add('cover-finite-witness','no_broken_cover_ally',results=(True,False,False),damage=(6000,)*3,stack=0,duration=.05);reload(c);attack(c,4)
    c=add('cover-permanent-snapshot','no_broken_cover_ally',results=(True,False,False),damage=(6000,6600,6600),stack=1,duration=-1);reload(c);attack(c,4)
    c=add('cover-condition-first-false','no_broken_cover_ally',results=(False,)*3,damage=(6000,)*3,stack=0);c['effects'][-1]['trigger']['condition'].insert(0,'self_hp_below:1')
    c=add('cover-condition-last-false','no_broken_cover_ally',results=(False,)*3,damage=(6000,)*3,stack=0);c['effects'][-1]['trigger']['condition'].append('self_hp_below:1')
    c=add('cover-double-condition','no_broken_cover_ally');c['effects'][-1]['trigger']['condition'].append('no_broken_cover_ally')
    add('focus-passive-self','focusing',timing='passive',duration=-1,camera=(0,),results=(True,),damage=(6600,)*3,stack=1)
    add('focus-passive-other','focusing',timing='passive',duration=-1,camera=(4,),results=(True,),damage=(6000,)*3,stack=1)
    add('focus-passive-empty','focusing',timing='passive',duration=-1,results=(True,),damage=(6000,)*3,stack=1)
    add('focus-passive-shared','focusing',timing='passive',duration=-1,camera=(0,4),results=(True,),damage=(6600,)*3,stack=1)
    add('focus-passive-last-owner','focusing',timing='passive',duration=-1,camera=(4,),results=(True,),damage=(6600,)*3,stack=1,owner=4)
    add('focus-discrete-finite-self','focusing',camera=(0,))
    add('focus-discrete-finite-other','focusing',camera=(4,))
    add('focus-discrete-permanent-self','focusing',duration=-1,camera=(0,))
    add('focus-discrete-permanent-other','focusing',duration=-1,camera=(4,),damage=(6000,)*3)
    add('focus-start-finite-other','focusing',timing='battle_start',camera=(4,),results=(True,),damage=(6600,)*3,stack=1)
    add('focus-passive-finite-other','focusing',timing='passive',duration=.1,camera=(4,),results=(True,)*17,damage=(6600,)*3,stack=1)
    c=add('focus-dynamic-owner','focusing',timing='passive',duration=-1,camera=(0,),results=(True,),damage=(6600,6000,6600),stack=1)
    c['weapon_metadata']['input_type']='UP'
    c['controls'][4]=dict(sequence=[dict(action='hold',t=0,until=.1)]);c['controls'][1]=dict(sequence=[dict(action='hold',t=.1,until=.2)])
    c=add('cover-own-broken','no_broken_cover_ally',timing='every:0.1s',results=(False,)*3,damage=(),stack=0);c['duration']=.35;c['contract']['ammo']=10;reload(c,0);attack(c,0)
    c=add('cover-partial-damage','no_broken_cover_ally');reload(c);attack(c,4,500)
    c=add('focus-all-allies-caster','focusing',timing='passive',duration=-1,camera=(0,),results=(True,),damage=(6600,)*3,stack=1);c['effects'][-1]['target']='all_allies'
    c=add('focus-all-allies-recipient-only','focusing',timing='passive',duration=-1,camera=(4,),results=(True,),damage=(6000,)*3,stack=1);c['effects'][-1]['target']='all_allies'
    add('focus-passive-finite-self','focusing',timing='passive',duration=.1,camera=(0,),results=(True,)*17,damage=(6600,)*3,stack=1)
    intact=list(range(5));all_true=[True]*5
    for c in rows:
        e=c['contract'];label=c['name'].removeprefix('state-predicate-')
        owners=[intact[:] for _ in e['results']] if e['condition']=='no_broken_cover_ally' else [[] for _ in e['results']]
        values=[all_true[:] for _ in e['results']] if e['condition']=='no_broken_cover_ally' else [[] for _ in e['results']]
        if label in ('cover-ally-breaks','cover-piercing-break','cover-finite-witness','cover-permanent-snapshot'):
            values[1:]=[[True]*4+[False]]*2
        elif label=='cover-first-ally-breaks':owners[1:]=[[0,1]]*2;values[1:]=[[True,False]]*2
        elif label=='cover-broken-then-revived':values[1]=[True]*4+[False]
        elif label=='cover-broken-then-dead':values[1]=[True]*4+[False];owners[2]=list(range(4));values[2]=[True]*4
        elif label=='cover-dead-with-intact-cover':owners[1:]=[list(range(4))]*2;values[1:]=[[True]*4]*2
        elif label=='cover-condition-first-false':owners=[[]]*3;values=[[]]*3
        elif label=='cover-double-condition':owners=[intact*2]*3;values=[all_true*2]*3
        elif label=='cover-own-broken':owners=[[0]]*3;values=[[False]]*3
        e['cover_query_owners']=owners;e['cover_query_values']=values
        runtime_count=0;transitions=[]
        if label in ('focus-passive-self','focus-passive-other','focus-passive-empty','focus-passive-shared','focus-passive-last-owner','focus-dynamic-owner'):
            runtime_count=18
        elif label.startswith('focus-discrete-permanent-'):runtime_count=19
        elif label.startswith('focus-all-allies-'):runtime_count=90
        if runtime_count:
            mask=sum(1<<roster_names(c).index(n) for n in c['camera']);transitions=[[mask,bool(mask&(1<<e['owner']))]]
        if label=='focus-dynamic-owner':transitions=[[1,True],[16,False],[2,False],[1,True]]
        e['runtime_count']=runtime_count;e['runtime_transitions']=transitions
    return rows
