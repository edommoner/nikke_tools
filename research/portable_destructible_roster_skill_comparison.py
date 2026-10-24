"""One full battle/typed packet comparator for original roster skill suites."""
import importlib.util
from pathlib import Path
from destructible_skill_shield_policy import skill
from portable_specs import LIMITS as L

spec=importlib.util.spec_from_file_location('shared_skill_weapon_comparison',Path(__file__).with_name('verify-destructible-weapon-rosters-short.py'))
prior=importlib.util.module_from_spec(spec);spec.loader.exec_module(prior)


def compare(block,domain,native):
    c,m,p,w=domain;n=native;roster=prior.roster
    actual,_,_,diff=roster.compare(block,p,(w,m),n['battle'],n['projectile_shots']);assert block[0]==0 and not diff,(c['name'],block[0],diff[:8])
    if c.get('body_lifesteal_v1'):
        # The recorded shared-body-heal calls own their recipient HP deltas.
        # These authored rosters have no sharing; do not infer other recipients
        # from the source owner when future heal_split cases are introduced.
        assert not any(r['effect'].get('stat')=='heal_split' for r in p['effects']),'Shared healing requires recipient receipts'
        healed=[0.]*5
        for receipt in n['healing']:
            who=receipt['owner'];healed[who]+=max(0.,receipt['after']-receipt['before'])
        for rows in (actual['allies'],actual['queries'][0]['allies']):
            assert [row['healing'] for row in rows]==healed,(c['name'],'body_healing',rows,healed)
    names=c['body']['squad'];case=dict(c,names=names,effects=[r['effect'] for r in p['effects']],owners=[names.index(r['owner']) for r in p['effects']])
    chars={r['name']:r for r in p['chars']};metadata=[]
    for packet,sample in zip(n['packet_samples'],n['shield_samples'],strict=True):
        source=packet['source']
        if source is None:metadata.append(None);continue
        e=p['effects'][source];plan=skill(e['effect'],chars[e['owner']]);flags=sample['family_flags']
        bits=int(flags['is_burst_damage'])|4096*int(flags['is_aoe_burst'])|8192*int(flags['is_single_burst'])
        metadata.append([1,2,plan['route'],bits,128 if plan['route']==2 else plan['count']])
    decoded=prior.prior.battle.decode(block,(case,m,()),sampled_coefficients=[r['coefficient'] for r in n['packet_samples']],sampled_rows=[r['source'] for r in n['packet_samples']],sampled_packets=[r['mode_skill'] for r in n['packet_samples']],sampled_skill_metadata=metadata)
    assert decoded==n['typed'],(c['name'],decoded,n['typed'])
    assert not any(block[L['COUNTER_CONTEXT_BASE']:L['COUNTER_CONTEXT_BASE']+1096]),'Typed counter context leaked'
    return n
