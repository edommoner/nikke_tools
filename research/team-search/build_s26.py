"""Mechanics-only v4 metadata. No truth or fitted coefficients are read."""
import argparse
import copy
import json
from pathlib import Path

SHIELD_STATS={'shield_from_max_hp_pct','shared_shield_from_max_hp_pct'}


def needs_shield(effect):
    trigger=effect.get('trigger',{})
    timings=trigger.get('timing',[])
    return ('during_shield' in trigger.get('condition',[]) or
            bool(timings) and all(t=='event:shield_applied' for t in timings))


def prerequisite(effect,effects):
    """Only structural single-state implications, including negated states.

    A marker maintained at battle_start/full_burst_end by one structural
    predicate has that same predicate at full-burst-start supply queries.
    Unknown, temporary, compound, or cyclic implications remain unmodelled.
    """
    terms=effect.get('trigger',{}).get('condition',[])
    codes={'no_burst1_ally':1,'has_burst1_ally':2,'squad_ally_exists':3}
    if len(terms)!=1:return 0
    term=terms[0]
    if term in codes:return codes[term]
    prefix=next((s for s in ('self_state:','not_self_state:') if term.startswith(s)),None)
    if prefix is None:return 0
    name=term[len(prefix):]
    markers=[e for e in effects if e.get('name')==name and e.get('type')=='buff'
             and e.get('target')=='self' and e.get('duration')==-1
             and e.get('trigger',{}).get('timing')==['battle_start','full_burst_end']]
    if len(markers)!=1:return 0
    conditions=markers[0].get('trigger',{}).get('condition',[])
    if len(conditions)!=1 or conditions[0] not in codes:return 0
    # Require the complementary removal path too: an enabling predicate alone
    # does not prove an absent state when the predicate later becomes false.
    code=codes[conditions[0]]
    if code not in (1,2):return 0
    complement='has_burst1_ally' if code==1 else 'no_burst1_ally'
    if not any(e.get('stat')=='remove_named_buff' and e.get('target_effect')==name
               and e.get('target')=='self' and e.get('trigger',{}).get('timing')==['battle_start','full_burst_end']
               and e.get('trigger',{}).get('condition')==[complement] for e in effects):return 0
    return code if prefix=='self_state:' else (2 if code==1 else 1)


def build(profiles,switches):
    p=copy.deepcopy(profiles)
    p['s26']=dict(version=4,switches=switches,no_truth_fitting=True,
        rules={'1':'If the entire squad has no shield-creating effect, shield-applied and during-shield observed supplies are impossible; remove only those supplies, including observed own contribution.',
               '2':'Observed enemy-code received-damage supply on the fixed single-BODY scenario affects all squad attacks, following _resolve_enemies; lower only matching code selectors with matching target_code conditions.',
               '4':'Structural prerequisites also remove explicitly observed own supply. Invert a permanent battle_start/full_burst_end self-state only with its exact complementary removal path; do not invent unobserved alternate effects.'},
        limitations=['Presence is conservative: a shield provider may have unavailable triggers or different recipients; no new target rule or shield uptime is inferred.'])
    enemy=p['settings'].get('enemy',{})
    plain=not any(enemy.get(k) for k in ('patterns','has_parts','part_break_interval','coord')) and not p['settings'].get('boss_preset')
    for c in p['characters'].values():
        c['shield_provider_s26']=any(e.get('stat') in SHIELD_STATS for e in c['effects'])
        c['stage_uncertain_s26']=(str(c['metadata'].get('burst_stage'))=='A' or
            any(e.get('stat','').startswith('burst_stage_override:') and 'reenter' not in e['stat'] for e in c['effects']))
        for q in c['buffs']:
            d=q['effect'];q['needs_shield_s26']=needs_shield(d)
            q['prerequisite_s26']=prerequisite(d,c['effects'])
            target=d.get('target','');terms=target.split(':') if isinstance(target,str) else []
            conditions=d.get('trigger',{}).get('condition',[])
            # The reference resolves these to the single enemy sentinel and
            # checks target_code separately. Preserve both facts; do not
            # generalize to dynamic enemies, states, random or spatial rules.
            if (plain and terms and terms[0] in ('enemies_code','enemies_lowest_hp_code')
                and len(terms)==(2 if terms[0]=='enemies_code' else 3)
                and (len(terms)==2 or terms[2].isdigit() and int(terms[2])>0)
                and conditions==['target_code:'+terms[1]]
                and (not enemy.get('code') or enemy['code']==terms[1])
                and d.get('stat')=='received_dmg_pct'):
                q['target_s26']='all_allies'
    return p


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--profiles',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--switches',type=int,required=True)
    a=p.parse_args()
    with a.out.open('x') as f:json.dump(build(json.loads(a.profiles.read_text()),a.switches),f,ensure_ascii=False,separators=(',',':'));f.write('\n')
