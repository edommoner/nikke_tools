"""Literal pre-rounding target-kind contract; no new gameplay claim."""
import copy

def fixtures():
    rows=[]
    def buff(stat,value,**kw):
        return dict(name=kw.pop('name',stat),source='스킬1',type='buff',stat=stat,fixed_value=value,target='self',duration=10,trigger=dict(timing=['battle_start'],condition=[]),**kw)
    def add(name,*,kind=2,effects=(),expected=900.,factor=1.,owner=0,attacker=0,when=.1,base_attack=1000.,coefficient=100.):
        c=dict(name='destructible-modifier/'+name,kind=kind,effects=[buff('crit_rate',-100),*copy.deepcopy(effects)],owners=[attacker]+[owner]*len(effects),attacker=attacker,when=when,base_attack=base_attack,defense=100.,coefficient=coefficient,expected=expected,factor=factor)
        rows.append(c);return c
    add('baseline')
    add('projectile',effects=[buff('projectile_dmg_pct',50)],expected=1350.,factor=1.5)
    add('hp-shield',kind=3,effects=[buff('shield_dmg_pct',50)],expected=1350.,factor=1.5)
    add('body-excludes-both',kind=0,effects=[buff('projectile_dmg_pct',50),buff('shield_dmg_pct',100)])
    add('projectile-excludes-shield',effects=[buff('shield_dmg_pct',100)])
    add('hp-shield-excludes-projectile',kind=3,effects=[buff('projectile_dmg_pct',100)])
    add('not-intercept',effects=[buff('intercept_dmg_pct',100)])
    add('not-part',effects=[buff('part_dmg_pct',100)])
    add('not-attachment',effects=[buff('projectile_attachment_dmg_pct',100)])
    add('not-explosion',effects=[buff('projectile_explosion_dmg_pct',100)])
    add('additive-not-product',effects=[buff('atk_dmg_pct',40),buff('projectile_dmg_pct',50)],expected=1710.,factor=1.9)
    add('two-sources',effects=[buff('projectile_dmg_pct',20,name='first'),buff('projectile_dmg_pct',30,name='second')],expected=1350.,factor=1.5)
    add('negative',effects=[buff('projectile_dmg_pct',-50)],expected=450.,factor=.5)
    add('minimum-one',effects=[buff('projectile_dmg_pct',-100)],expected=1.,factor=0.)
    c=add('expired',effects=[buff('projectile_dmg_pct',50)],when=.2);c['effects'][-1]['duration']=.2
    add('not-other-ally',effects=[buff('projectile_dmg_pct',50)],owner=1)
    c=add('squad-gift',effects=[buff('projectile_dmg_pct',50)],owner=1,expected=1350.,factor=1.5);c['effects'][-1]['target']='all_allies'
    c=add('runtime-condition-false',effects=[buff('projectile_dmg_pct',50)]);c['effects'][-1]['trigger']['condition']=['during_full_burst']
    c=add('stacked',effects=[buff('projectile_dmg_pct',25,max_stack=2)],expected=1350.,factor=1.5);c['activations']=2
    c=add('before-final-round',effects=[buff('projectile_dmg_pct',50)],base_attack=3.,coefficient=50.,expected=2.,factor=1.5);c['defense']=0.
    return rows
