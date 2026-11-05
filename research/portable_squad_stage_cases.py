"""Caster-owned stage notifications, distinct from ally-burst broadcasts."""
import copy
from portable_ally_burst_cases import fixtures as ally_fixtures
from portable_burst_recipient_cases import instant
from world_enemy_attack_cases import field


def fixtures():
    seed=ally_fixtures()[0];rows=[]
    def add(label,listeners=(),casts=3,hp=None,activations=()):
        c=copy.deepcopy(seed);c['name']='squad-stage-'+label
        for owner,stage,target in listeners:
            c['effects'].append(instant('heal_hp_pct',1,target,'listener-'+str(owner)+'-'+str(stage),'squad_burst_cast:'+str(stage)));c['owners'].append(owner)
        c['contract']=dict(casts=casts,hp=hp or [5000]*5,listener_activations=list(activations));rows.append(c);return c
    add('own-stages',[(owner,stage,'self') for stage in (1,2,3) for owner in range(5)],hp=[5100,5000,5100,5100,5000],activations=[0,2,3])
    add('other-owner',[(4,1,'self')])
    for label,owner,stage in [('stage1',0,1),('stage2',2,2),('stage3',3,3)]:
        hp=[5000]*5;hp[owner]=5100;add(label,[(owner,stage,'self')],hp=hp,activations=[owner])
    add('wrong-stage',[(0,2,'self')])
    add('all-recipients',[(0,1,'all_allies')],hp=[5100]*5,activations=[0])
    c=add('duplicate-descriptor',[(0,1,'self')],hp=[5200,5000,5000,5000,5000],activations=[0,0]);c['effects'][-1]['trigger']['timing']*=2
    c=add('budget-reentry',[(0,1,'self')],casts=4,hp=[5100,5000,5000,5000,5000],activations=[0]);c['effects'][-1]['max_trigger']=1
    c['effects'].append(instant('burst_reentry',1,'self','reenter','burst_cast'));c['owners'].append(0)
    c['effects'].append(instant('burst_cooldown_reduce',1000,'self','ready-for-reentry','burst_cast'));c['owners'].append(0)
    c=add('reentry-via-stage',[(0,1,'self'),(1,1,'self')],casts=4,hp=[5100,5100,5000,5000,5000],activations=[0,1]);c['effects'].append(instant('burst_reentry',1,'self','reenter','squad_burst_cast:1'));c['owners'].append(0)
    c=add('same-caster-reentry',[(0,1,'self')],casts=4,hp=[5200,5000,5000,5000,5000],activations=[0,0]);c['effects'].extend([instant('burst_cooldown_reduce',1000,'self','ready-for-reentry','squad_burst_cast:1'),instant('burst_reentry',1,'self','reenter','squad_burst_cast:1')]);c['owners'].extend([0,0])
    c=add('after-own-burst',[(0,1,'self')],hp=[5100,5000,5000,5000,5000],activations=[0]);c['effects'][-1]['trigger']['condition']=['self_state:own-witness']
    c['effects'].append(field('atk_pct',0,'self','own-witness',timing='burst_cast'));c['owners'].append(0)
    c=add('before-ally-burst',[(0,1,'self')],hp=[5100,5000,5000,5000,5300],activations=[0,4,4,4])
    c['effects'].append(field('atk_pct',0,'all_allies','stage-witness',timing='squad_burst_cast:1'));c['owners'].append(0)
    e=instant('heal_hp_pct',1,'self','listener-ally','event:ally_burst_cast');e['trigger']['condition']=['self_state:stage-witness'];c['effects'].append(e);c['owners'].append(4)
    c=add('cast-mask-before-stage',[(0,1,'self')]);c['effects'][-1]['trigger']['condition']=['burst_not_casted']
    c=add('cooldown-after-ready',[(0,1,'self')],hp=[5100,5000,5000,5000,5000],activations=[0]);c['effects'].append(instant('burst_cooldown_reduce',20,'self','reduce-ready','squad_burst_cast:1'));c['owners'].append(0)
    c=add('no-casts',[(0,1,'self')],casts=0);c['effects']=c['effects'][1:];c['owners']=c['owners'][1:]
    for w in c['combat']['weapons']:w['gauge']=0
    return rows
