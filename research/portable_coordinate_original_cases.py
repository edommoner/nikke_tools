"""Original public roster bodies plus declared coordinate worlds, no effects edits."""
import copy,importlib.util
from pathlib import Path
def fixtures():
    s=importlib.util.spec_from_file_location('coordinate_original_factory',Path(__file__).with_name('verify-world-projectile-rosters.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
    rows=[]
    for name,label in [('마르차나','Marciana'),('델타 : 닌자 시프','Delta-ninja-thief')]:
        for defender in (False,True):
            squad=m.policy.roster_for(name)
            if defender:squad[3]='노아'
            for duration in (3,30):
                body=dict(m.body_for(squad,duration),burst_gauge_mode='accumulate',seed=2301+len(rows))
                rows.append(dict(name='coordinate-original/'+label+'/'+('defender' if defender else 'control')+'/'+str(duration)+'s',body=body,coord=dict(auto_aim=[0.,0.],pierce_px=10.,explosion_scale=1.),patterns=[dict(id='original-world',kind='idle')]))
    for defender in (False,True):
        base=copy.deepcopy(next(r for r in rows if r['name']=='coordinate-original/Delta-ninja-thief/'+('defender' if defender else 'control')+'/3s'))
        base['name']+='/direct-hits'
        base['patterns'].append(dict(id='original-direct-hits',kind='attack',delay=1.,spec=dict(atk=10000,coeff=100,target='all',pierce=True,hits=3,interval=.1)))
        base['removal_witness']=True;rows.append(base)
    return rows

def prepare_case(row):
    import engine_worker
    from portable_weapon_input import normalize_static_weapon
    from calculator.timeline import _resolve_cameras,DEFAULT_CONFIG
    p=engine_worker.evaluate(dict(row['body'],_portable_static_inputs=True));world=copy.deepcopy(p)
    world['enemy'].update(coord=copy.deepcopy(row['coord']),patterns=copy.deepcopy(row['patterns']))
    chars=p['chars'];names=[c['name'] for c in chars];cfg=p['policies']['config'];cameras=_resolve_cameras(chars,{**DEFAULT_CONFIG,**cfg})
    weapons=[normalize_static_weapon(c,a,world['enemy'],camera=c['name'] in cameras) for c,a in zip(chars,p['base_atk'])]
    case=dict(name=row['name'],names=names,duration=cfg['duration'],seed=p['policies']['seed'],enemy=copy.deepcopy(world['enemy']),patterns=copy.deepcopy(row['patterns']),
        effects=[copy.deepcopy(e['effect']) for e in p['effects']],owners=[names.index(e['owner']) for e in p['effects']],base_atk=p['base_atk'],
        skill_levels=[copy.deepcopy(c['skill_levels']) for c in chars],controls=[copy.deepcopy(c.get('control',{})) for c in chars],
        combat=dict(weapons=weapons,clock='accumulated'),environment=dict(allies=p['allies']),
        sampled_vital=True,sampled_skill=True,sampled_burst=True,sampled_delivery=True,sampled_routed_delivery=True,coordinate_healing=True,observe_healing_storage=True,
        coordinate_packet_trace=False,control_mode=cfg.get('control_mode','solo'),
        observe_target_counters=True,observe_fractional_hits=True,manual_controls=True,cover_policies=True,squad_controls=True,squad_mode_state=True,burst_controls=True,sequence=[],
        removal_witness=row.get('removal_witness',False),original_run=dict(body=copy.deepcopy(row['body']),prepared=p,scalar_enemy=copy.deepcopy(p['enemy'])))
    return case,world
