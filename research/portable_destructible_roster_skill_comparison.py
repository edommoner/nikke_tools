"""One full battle/typed packet comparator for original roster skill suites."""
import importlib.util
from pathlib import Path
from destructible_skill_shield_policy import skill
from portable_specs import LIMITS as L

spec=importlib.util.spec_from_file_location('shared_skill_weapon_comparison',Path(__file__).with_name('verify-destructible-weapon-rosters-short.py'))
prior=importlib.util.module_from_spec(spec);spec.loader.exec_module(prior)


def compare(block,domain,native,*,sample_key='shield_samples'):
    c,m,p,w=domain;n=native;roster=prior.roster
    actual,_,_,diff=roster.compare(block,p,(w,m),n['battle'],n['projectile_shots']);assert block[0]==0 and not diff,(c['name'],block[0],diff[:8])
    # The reference's end-of-battle query owns these final HP quantities too.
    # The generic battle comparator only checks the explicit query response.
    for got,wanted in zip(actual['allies'],n['battle']['query']['allies'],strict=True):
        assert {key:got[key] for key in ('hp','max_hp','hp_pct','defense')}==wanted,(c['name'],'final_body_health',got,wanted)
    if c.get('body_lifesteal_v1'):
        # Sharing uses actual recipient clamp returns, never the source owner's
        # HP delta. Preserve historical source receipts for non-sharing rosters.
        sharing=c.get('body_heal_sharing_v1') is True
        assert sharing or not any(r['effect'].get('stat')=='heal_split' for r in p['effects']),'Shared healing requires recipient receipts'
        healed=[0.]*5
        for receipt in n['healing_recipients'] if sharing else n['healing']:
            who=receipt['owner'];healed[who]+=max(0.,receipt['after']-receipt['before'])
        for rows in (actual['allies'],actual['queries'][0]['allies']):
            assert [row['healing'] for row in rows]==healed,(c['name'],'body_healing',rows,healed)
    names=c['body']['squad'];case=dict(c,names=names,effects=[r['effect'] for r in p['effects']],owners=[names.index(r['owner']) for r in p['effects']])
    chars={r['name']:r for r in p['chars']};metadata=[]
    for packet,sample in zip(n['packet_samples'],n[sample_key],strict=True):
        source=packet['source']
        if source is None:metadata.append(None);continue
        e=p['effects'][source]
        if c.get('declared_projectile_probe'):
            from destructible_skill_specs import coefficient
            assert source==c['probe_source'] and e['effect']['target']==('all_projectiles' if c.get('probe_kind',2)==2 else 'boss'),'Only the explicit declared probe may use the plain Frame metadata'
            coefficient(dict(e['effect'],target='all_projectiles'),chars[e['owner']]);metadata.append([0]*5);continue
        if packet.get('quantity_only'):
            from destructible_skill_shield_policy import accumulation_skill
            plan=accumulation_skill(e['effect']);metadata.append([1,3,plan['route'],16,128 if plan['route']==2 else plan['count']]);continue
        plan=skill(e['effect'],chars[e['owner']],allow_split=c.get('body_accumulation_v1',False));flags=sample['family_flags']
        bits=int(flags['is_burst_damage'])|4096*int(flags['is_aoe_burst'])|8192*int(flags['is_single_burst'])
        metadata.append([1,2,plan['route'],bits,128 if plan['route']==2 else plan['count']])
    decoded=prior.prior.battle.decode(block,(case,m,()),sampled_coefficients=[r['coefficient'] for r in n['packet_samples']],sampled_rows=[r['source'] for r in n['packet_samples']],sampled_packets=[r['mode_skill'] for r in n['packet_samples']],sampled_skill_metadata=metadata)
    assert decoded==n['typed'],(c['name'],decoded,n['typed'])
    assert not any(block[L['COUNTER_CONTEXT_BASE']:L['COUNTER_CONTEXT_BASE']+1096]),'Typed counter context leaked'
    return n

def compare_body_consumers(block,domain,native):
    """One battle/landing audit, plus the existing pool audit when declared."""
    result=compare(block,domain,native)
    if domain[0].get('body_accumulation_v1'):
        from portable_damage_accum_observation import compare_final
        compare_final(block,domain[1],native['damage_accumulation'])
    return result
