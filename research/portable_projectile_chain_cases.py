"""Named handler-completion notifications and ordinary buff carriers."""
import copy
from portable_parent_fixed_cases import fixtures as parent
from world_enemy_attack_cases import field

def fixtures():
    seed=copy.deepcopy(parent()[0]);seed.update(effects=[],owners=[],duration=.35,contract={})
    for w in seed['combat']['weapons']:w.update(mode='charge',charge=10,interval=10,min_cycle=10)
    rows=[]
    def damage(stat='damage',name='source',value=100,timing='every:0.1s',**kw):return dict(name=name,source='스킬2',type='damage',stat=stat,fixed_value=value,target='target',trigger=dict(timing=[timing],condition=[]),max_trigger=1,**kw)
    def marker(name='heard',ref='source',target='self',**kw):return field('',0,target,name,'weapon_hit:'+ref,duration=-1,**kw)
    def add(kind,effects,owners=None):
        c=copy.deepcopy(seed);c.update(name='projectile-chain-'+kind,effects=[field('crit_rate',-100,'all_allies','no-crit')]+effects,owners=[0]+(owners or [0]*len(effects)),contract=dict(kind=kind));rows.append(c);return c
    add('plain',[damage(),marker()])
    add('three-packets-one-notice',[damage('damage:3'),marker()])
    add('zero-hit-count',[damage('damage:0'),marker()])
    add('negative-hit-count',[damage('damage:-1'),marker()])
    add('zero-coefficient',[damage(value=0),marker()])
    add('empty-name',[damage(name=''),marker(ref='')])
    add('attachment-factor',[field('projectile_attachment_dmg_pct',100,'self','attachment-factor'),damage('projectile_attachment_damage'),marker()])
    add('explosion-factor',[field('projectile_explosion_dmg_pct',100,'self','explosion-factor'),damage('projectile_explosion_damage'),marker()])
    c=add('matching-normal-MG-annotation',[damage('projectile_attachment_damage',damage_formula='normal_attack',weapon_type='MG'),marker()]);c['combat']['weapons'][0]['base_weapon_type']='MG'
    c=add('mismatched-normal-annotation',[damage('projectile_attachment_damage',damage_formula='normal_attack',weapon_type='RL'),marker()]);c['combat']['weapons'][0]['base_weapon_type']='MG';c['contract']['reference_model_gap']=True
    add('two-casts',[dict(damage(),max_trigger=2),marker()])
    add('exact-literal-name',[damage(name='source: 부착 '),marker(ref='source: 부착 '),marker(name='near-miss',ref='source: 부착')])
    add('other-caster-listener',[damage(),marker()],[0,1])
    add('nested-handler-order',[damage(),damage(name='child',value=50,timing='weapon_hit:source'),damage(name='grandchild',value=25,timing='weapon_hit:child'),marker(ref='grandchild')])
    add('buff-kind-self-carrier',[dict(damage(),max_trigger=2),field('buff_stack_add',1,'self','carrier','weapon_hit:source',duration=-1,max_stack=-1),damage(name='threshold',value=10,timing='stack_reach:carrier:2')])
    add('buff-kind-enemy-carrier',[dict(damage(),max_trigger=2),field('buff_stack_add',1,'target','carrier','weapon_hit:source',duration=-1,max_stack=-1),damage(name='threshold',value=10,timing='stack_reach:carrier:2')])
    add('instant-kind-stack-operation',[field('',0,'self','carrier',max_stack=5),damage(),dict(name='instant-stack',source='스킬2',type='instant',stat='buff_stack_add',target='self',target_effect='carrier',fixed_value=2,trigger=dict(timing=['weapon_hit:source'],condition=[]))])
    add('periodic-handler',[damage(timing='battle_start',tick_interval=.1,duration=.25,tick_start='immediate'),marker()])
    add('empty-accumulation-early-return',[damage('accum_split_damage',target_effect='missing'),marker()])
    add('parent-fixed-early-return',[damage('dealt_fixed_damage'),marker()])
    add('named-multiplier-zero-still-notifies',[field('dmg_scale_mag_pct',-100,'self','zero-magnitude',target_effect='source'),damage(),marker()])
    add('per-hit-child-before-completion',[damage('damage:2'),field('atk_pct',100,'self','child-atk','hit_count:source:1'),damage(name='completion-child',timing='weapon_hit:source')])
    add('instant-target-does-not-select-buff-carrier',[field('',0,'self','carrier',max_stack=5),damage(),dict(name='instant-stack',source='스킬2',type='instant',stat='buff_stack_add',target='target',target_effect='carrier',fixed_value=2,trigger=dict(timing=['weapon_hit:source'],condition=[]))])
    c=add('all-projectiles-missing-reference',[dict(damage(),target='all_projectiles'),marker()]);c['contract']['reference_model_gap']=True
    c=add('physical-hits-are-not-handler-completions',[marker()])
    c['combat']['weapons'][0].update(mode='auto',interval=.1,min_cycle=.1,post_reload_delay=0)
    c['post_fire_delays'][0]=0  # Auto weapons have no charge-release clock.
    c=add('normal-MG-attachment-factor',[field('projectile_attachment_dmg_pct',100,'self','attachment-factor'),damage('projectile_attachment_damage',damage_formula='normal_attack',weapon_type='MG'),marker()]);c['combat']['weapons'][0]['base_weapon_type']='MG'
    return rows
