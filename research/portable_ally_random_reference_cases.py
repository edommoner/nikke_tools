"""Authored friendly selection stimuli, independent of boss RNG consumption."""
import copy
from portable_ammo_equivalent_cases import fixtures as ammo_fixtures
from portable_burst_recipient_cases import instant
from world_enemy_attack_cases import field
from world_frame_native import roster_names


def fixtures():
    base=copy.deepcopy(ammo_fixtures()[0]);base.pop('contract');rows=[]
    def add(label,target='allies_random:1',owner=0,timing='on_attack'):
        c=copy.deepcopy(base);c['name']='ally-random-'+label;c['seed']=19
        if owner!=0:
            c['combat']['weapons'][0].update(mode='charge',charge=10,interval=10,min_cycle=10)
            c['combat']['weapons'][owner].update(mode='auto',interval=.1,min_cycle=.1,capacity=10)
        c['effects']=[field('crit_rate',-100,'self','no-crit'),field('def_pct',10,target,'selection-witness',timing=timing,duration=.05,max_stack=128)];c['owners']=[owner,owner]
        rows.append(c);return c
    add('one')
    add('two',target='allies_random:2')
    add('saturated',target='allies_random:5')
    add('last-caster',owner=4)
    c=add('seed-zero');c['seed']=0
    for label,targets in [('singleton',(2,3,4)),('empty',(2,3,4,5))]:
        c=add(label);c['patterns']=[dict(id='lethal-'+str(slot),kind='attack',delay=0,spec=dict(atk=1e12,coeff=100,target='slot:'+str(slot),ignore_taunt=True)) for slot in targets]
    c=add('boss-random-independent');c['patterns']=[dict(id='enemy-random',kind='attack',delay=.05,spec=dict(atk=1,coeff=100,target='random:1',hits=3,interval=.05))]
    add('broken-empty',target='allies_broken_cover_random:2')
    def reload(c,who):c['effects'].insert(1,instant('force_reload',1,roster_names(c)[who],'reload-'+str(who)));c['owners'].insert(1,0);c['combat']['weapons'][who]['reload']=1
    hit=lambda slot,when=.05,atk=2000:dict(id='hit-'+str(slot)+'-'+str(when),kind='attack',delay=when,spec=dict(atk=atk,coeff=100,target='slot:'+str(slot+1),ignore_taunt=True))
    c=add('broken-singleton',target='allies_broken_cover_random:2');reload(c,4);c['patterns']=[hit(4)]
    c=add('broken-includes-caster',target='allies_broken_cover_random:2',timing='every:0.1s');c['duration']=.35;reload(c,0);reload(c,4);c['patterns']=[hit(0),hit(4)]
    c=add('broken-then-dead',target='allies_broken_cover_random:2');reload(c,4);c['patterns']=[hit(4),hit(4,.15,1e12)]
    for label,source in [('bundle-shares','스킬1'),('bundle-cross-source-shares','스킬2')]:
        c=add(label,target='allies_random:2',timing='battle_start');c['effects'][1]['duration']=-1
        c['effects'].append(field('accuracy_pct',10,'allies_random:2','bundle-second',duration=-1));c['effects'][-1]['source']=source;c['owners'].append(0)
    c=add('instant-broken-empty',target='allies_broken_cover_random:2');c['effects'][1]=instant('cover_revive',100,'allies_broken_cover_random:2','selection-witness','on_attack')
    c=add('instant-broken-singleton',target='allies_broken_cover_random:2');c['effects'][1]=instant('cover_revive',100,'allies_broken_cover_random:2','selection-witness','on_attack');reload(c,4);c['patterns']=[hit(4)]
    c=add('instant-broken-includes-caster',target='allies_broken_cover_random:2');c['effects'][1]=instant('cover_revive',100,'allies_broken_cover_random:2','selection-witness','every:0.1s');c['duration']=.35;reload(c,0);reload(c,4);c['patterns']=[hit(0),hit(4)]
    c=add('instant-random-ammo');c['effects'][1]=instant('ammo_charge_pct',10,'allies_random:1','selection-witness','on_attack')
    contracts={
        'one':([[1,2,3,4]]*3,[[1],[1],[2]],[1]*3,[624,2,6],[2,6,8]),
        'two':([[1,2,3,4]]*3,[[1,3],[1,3],[2,4]],[2]*3,[624,5,7],[5,7,9]),
        'saturated':([[1,2,3,4]]*3,[[1,3,4,2],[4,2,3,1],[3,1,2,4]],[4]*3,[624,8,15],[8,15,20]),
        'last-caster':([[0,1,2,3]]*3,[[0],[0],[1]],[1]*3,[624,2,6],[2,6,8]),
        'seed-zero':([[1,2,3,4]]*3,[[4],[4],[1]],[1]*3,[624,2,5],[2,5,6]),
        'singleton':([[4]]*3,[[4]]*3,[1]*3,[624,2,6],[2,6,8]),
        'empty':([[]]*3,[[]]*3,[0]*3,[624]*3,[624]*3),
        'broken-empty':([[]]*3,[[]]*3,[0]*3,[624]*3,[624]*3),
        'broken-singleton':([[],[4],[4]],[[],[4],[4]],[0,1,1],[624,624,2],[624,2,6]),
        'broken-includes-caster':([[0,4]]*3,[[0,4],[0,4],[4,0]],[2]*3,[624,6,9],[6,9,13]),
        'broken-then-dead':([[],[4],[]],[[],[4],[]],[0,1,0],[624,624,2],[624,2,2]),
        'bundle-shares':([[1,2,3,4]],[[1,3]],[2],[624],[5]),
        'bundle-cross-source-shares':([[1,2,3,4]],[[1,3]],[2],[624],[5]),
    }
    contracts['boss-random-independent']=contracts['one']
    contracts['instant-broken-empty']=contracts['broken-empty']
    contracts['instant-broken-singleton']=contracts['broken-then-dead']
    contracts['instant-broken-includes-caster']=([[0,4],[],[]],[[0,4],[],[]],[2,0,0],[624,6,6],[6,6,6])
    contracts['instant-random-ammo']=contracts['one']
    for c in rows:
        key=c['name'].removeprefix('ally-random-');pools,picked,ks,before,after=contracts[key]
        target=c['effects'][-1]['target'];owner=c['owners'][-1]
        c['contract']=dict(pools=pools,picked=picked,ks=ks,before=before,after=after,target=target,caster=owner,boss_draws=6 if key=='boss-random-independent' else 0)
    return rows
