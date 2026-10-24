"""Actual scheduler and same Frame, with declared projectile factor carriers."""
import copy
from destructible_battle_cases import fixtures as old
from world_enemy_attack_cases import field

def fixtures():
    base=old();plain=next(c for c in base if c['name'].endswith('/physical-and-typed'));rows=[]
    def add(label,source=plain,stat='projectile_dmg_pct',value=50.,owner=0,target='self',duration=10):
        c=copy.deepcopy(source);c['name']='destructible-modifier-battle/'+label
        c['effects'].insert(0,field(stat,value,target,'declared-modifier',duration=duration));c['owners'].insert(0,owner)
        rows.append(c);return c
    add('physical-body-is-unmodified')
    add('shield-factor-does-not-affect-projectiles',stat='shield_dmg_pct',value=100.)
    add('expiry-before-second-skill',duration=.15)
    add('different-ally-self',owner=1)
    add('squad-gift',owner=1,target='all_allies')
    c=add('ordinary-and-target-factor-add');c['effects'].insert(1,field('atk_dmg_pct',40,'self','ordinary-factor'));c['owners'].insert(1,0)
    c=add('two-stacks');c['effects'][0]['max_stack']=2;c['effects'][0]['trigger']['timing'].append('every:0.1s')
    c=add('named-completion-keeps-body-normal',source=next(c for c in base if c['name'].endswith('/ordinary-named-child')))
    c=add('named-coefficient-is-preserved');c['effects'].insert(1,field('dmg_scale_mag_pct',50,'self','coefficient-factor',target_effect='typed-source'));c['owners'].insert(1,0)
    c=copy.deepcopy(next(c for c in base if c['name'].endswith('/counter-reentrant-frozen-damage')));c['name']='destructible-modifier-battle/reentrant-parent-child-grandchild';c['effects'][1].update(stat='projectile_dmg_pct',fixed_value=50.);rows.append(c)
    c=add('zero-factor-keeps-native-minimum',value=-100.)
    c=add('empty-world-has-no-query',source=next(c for c in base if c['name'].endswith('/empty')))
    return rows
