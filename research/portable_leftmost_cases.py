"""Code/weapon candidate metadata is static; alive filtering precedes truncation."""
import copy
from portable_ammo_equivalent_cases import fixtures as ammo
from world_enemy_attack_cases import field
from portable_burst_recipient_cases import instant

def fixtures():
    seed=ammo()[0];rows=[]
    def add(label,count=1,stat='def_pct',kind='buff',target=None):
        c=copy.deepcopy(seed);c.pop('contract');c['name']='leftmost-'+label
        target=target or 'allies_code_weapon_leftmost:작열:AR:'+str(count)
        e=field(stat,10,target,'leftmost-witness','on_attack',duration=-1)
        if kind=='instant':e=instant(stat,10,target,'leftmost-witness','on_attack')
        c['effects']=[seed['effects'][0],e];c['owners']=[0,0]
        for a in c['environment']['allies']:a['base_defense']=100
        if kind=='instant':
            c['effects'].insert(1,instant('current_hp_reduce',50,'all_allies','drain','battle_start'));c['owners'].insert(1,0)
        c['contract']=dict(picked=[list(range(min(count,5)))]*3)
        rows.append(c);return c
    add('first')
    add('two',2)
    add('zero',0)
    add('five',5)
    c=add('weapon-empty',target='allies_code_weapon_leftmost:작열:SG:1');c['contract']['picked']=[[]]*3
    c=add('code-empty',target='allies_code_weapon_leftmost:전격:AR:1');c['contract']['picked']=[[]]*3
    c=add('weapon-holes',2);c['combat']['weapons'][0]['base_weapon_type']='SG';c['combat']['weapons'][2]['base_weapon_type']='RL';c['contract']['picked']=[[1,3]]*3
    def kill(c,slot,when):c.setdefault('patterns',[]).append(dict(id='kill-'+str(slot),kind='attack',delay=when,spec=dict(atk=1e12,coeff=100,target='slot:'+str(slot+1),ignore_taunt=True)))
    c=add('skip-first-dead',2);kill(c,1,0);c['contract']['picked']=[[0,2]]*3
    c=add('death-between-activations',2);kill(c,1,.05);c['contract']['picked']=[[0,1],[0,2],[0,2]]
    c=add('fewer-live-than-limit',5)
    for slot in (1,2,3,4):kill(c,slot,0)
    c['contract']['picked']=[[0]]*3
    c=add('instant-heal',2,stat='heal_hp_pct',kind='instant')
    c=add('instant-after-death',2,stat='heal_hp_pct',kind='instant');kill(c,1,.05);c['contract']['picked']=[[0,1],[0,2],[0,2]]
    c=add('named-literal-preserved',2);c['effects'][1]['trigger']['timing']=['battle_start'];c['contract']['picked']=[[0,1]]
    return rows
