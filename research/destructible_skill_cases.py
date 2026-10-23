"""Original all_projectiles definition with declared scalar target context."""
import copy,json
from pathlib import Path
from destructible_attack_cases import fixtures as attack_cases

def fixtures():
    root=Path(__file__).resolve().parents[1]
    original=json.loads((root/'research/upstream/nikke-calc-master/data/parsed_skills.json').read_text())['스노우 화이트 : 헤비암즈'][24]
    assert original['target']=='all_projectiles' and original['stat']=='damage'
    rows=[]
    def add(name,level=10,buffs=(),**kw):
        c=copy.deepcopy(attack_cases()[0]);c.update(name='destructible-skill/'+name,level=level,full_burst=False,attack_id=321,who=0,defense=0.)
        c['effects']+=list(copy.deepcopy(buffs))+[copy.deepcopy(original)];c['skill_row']=len(c['effects'])-1;c.update(kw);rows.append(c);return c
    def buff(stat,value,duration=10):return dict(name=stat,source='스킬1',type='buff',stat=stat,fixed_value=value,target='self',duration=duration,trigger=dict(timing=['battle_start'],condition=[]))
    add('original-level1',1);c=add('original-level10')
    for b in c['bindings']:
        if b['kind']==2:b['capacity']=1000.
    add('original-full-burst',full_burst=True)
    add('explicit-defense100',defense=100.)
    add('live-attack-buff',buffs=[buff('atk_pct',37.5)])
    add('live-damage-and-critical-buffs',buffs=[buff('atk_dmg_pct',21.25),buff('crit_dmg',30),buff('crit_rate',25)])
    add('expired-buff',buffs=[buff('atk_pct',37.5,.05)])
    c=add('empty-selection');c['bindings']=copy.deepcopy(attack_cases()[5]['bindings'])
    c=add('zero-coefficient');c['effects'][-1].pop('values');c['effects'][-1]['fixed_value']=0.
    c=add('one-ulp-coefficient');c['effects'][-1].pop('values');c['effects'][-1]['fixed_value']=0.23255813953488372
    return rows
