"""Actual burst notification, canonical budgets, and synchronous named children."""
import copy
from destructible_skill_cases import fixtures as skill_cases

def fixtures():
    rows=copy.deepcopy(skill_cases())
    for c in rows:c.update(name=c['name'].replace('destructible-skill/','destructible-frame/'),roots=1,event='burst_cast')
    c=copy.deepcopy(rows[1]);c.update(name='destructible-frame/trigger-not-due',event='on_attack');rows.append(c)
    c=copy.deepcopy(rows[1]);c.update(name='destructible-frame/two-root-attacks',roots=2);rows.append(c)
    c=copy.deepcopy(rows[1]);c.update(name='destructible-frame/manager-budget-once',roots=2);c['effects'][c['skill_row']]['max_trigger']=1;rows.append(c)
    c=copy.deepcopy(rows[7]);c.update(name='destructible-frame/empty-does-not-consume-budget',roots=2);c['effects'][c['skill_row']]['max_trigger']=1;rows.append(c)
    c=copy.deepcopy(rows[1]);c.update(name='destructible-frame/named-hit-child-after-counter',roots=2)
    name=c['effects'][c['skill_row']]['name']
    c['effects'].append(dict(name='named-hit-reward',source='스킬1',type='buff',stat='atk_pct',fixed_value=21.,target='self',duration=10,trigger=dict(timing=['hit_count:'+name+':1'],condition=[])));rows.append(c)
    from destructible_attack_cases import fixtures as attack_cases
    high=next(c for c in attack_cases() if c['name'].endswith('/high-slot128'))
    c=copy.deepcopy(rows[1]);c.update(name='destructible-frame/high-slot128',bindings=high['bindings']);c['effects'][0]['target_counter']['actor']['identity']=1127;rows.append(c)
    from destructible_counter_cases import fixtures as counter_cases
    siblings=next(c for c in counter_cases() if c['name'].endswith('/siblings-latched-before-refresh-and-break'))
    c=copy.deepcopy(rows[0]);skill=c['effects'][c['skill_row']];c.update(name='destructible-frame/siblings-refresh-before-death',effects=copy.deepcopy(siblings['effects'])+[skill],skill_row=len(siblings['effects']));rows.append(c)
    return rows
