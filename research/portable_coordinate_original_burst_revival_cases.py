"""Original Rapunzel's B1 revival with live and unavailable full-chain candidates."""
import importlib.util
from pathlib import Path

def fixtures():
    spec=importlib.util.spec_from_file_location('original_burst_revival_factory',Path(__file__).with_name('verify-world-projectile-rosters.py'));f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)
    rows=[]
    for label,squad,slots,revived in [('no-down',f.policy.roster_for('라푼젤'),[],[]),('only-B3-down',f.policy.roster_for('라푼젤'),[3],[]),('N102-down',f.policy.roster_for('라푼젤'),[4],[3]),('two-candidates',['라푼젤','센티','드레이크','미란다','메어리'],[4,5],[3])]:
        patterns=[dict(id='world',kind='idle'),*[dict(id='kill'+str(slot),kind='attack',delay=1.,spec=dict(atk=1e8,coeff=100,target='slot:'+str(slot),pierce=True)) for slot in slots]]
        rows.append(dict(name='coordinate-original-burst-revival/Rapunzel/'+label,body=dict(f.body_for(squad,6),burst_gauge_mode='accumulate',seed=2701),coord=dict(auto_aim=[0.,0.],pierce_px=10.,explosion_scale=1.),patterns=patterns,expected_down_owners=[slot-1 for slot in slots],expected_revived_owners=revived))
    return rows
