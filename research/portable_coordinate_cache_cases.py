"""Authored cache key collisions and Geometry replacement lifetimes."""
import copy
from portable_coordinate_core_cases import fixtures as cores
from world_enemy_attack_cases import field

def fixtures():
    source={c['name'].split('/')[-1]:c for c in cores()};rows=[]
    def add(label,base='pierce-under-part'):
        c=copy.deepcopy(source[base]);c['name']='coordinate-core/cache-'+label;c['duration']=.45
        c['weapon_metadata'].update(spread_start=14.,spread_end=14.,spread_change_pershot=0.)
        c['literal_weapon_geometry']=[dict(spread_start=14.,spread_end=14.,spread_shots=0.) for _ in range(5)]
        c['base_atk']=[1e12]*5
        for pattern in c['patterns']:
            for target in pattern.get('targets',[]):target['hp']=1e30
        rows.append(c);return c
    add('same-key')
    c=add('radius-collision');c['effects'].append(field('accuracy_pct',.000001,'self','tiny-accuracy','every:0.1s',max_stack=128));c['owners'].append(0)
    c=add('cross-owner-first-value');c['combat']['weapons'][3]=copy.deepcopy(c['combat']['weapons'][0]);c['effects'].append(field('accuracy_pct',.000001,'self','other-accuracy'));c['owners'].append(3);next(e for e in c['effects'] if e.get('stat')=='pierce_enabled')['target']='all_allies'
    c=add('zero-to-positive-grow');c['effects']=[e for e in c['effects'] if e.get('stat')!='pierce_enabled'];c['owners']=c['owners'][:-1]
    c['enemy']['coord']['pierce_px']=1e-8;c['effects'].append(field('pierce_enabled',1,'self','late-pierce','every:0.1s',max_trigger=1));c['owners'].append(0)
    c=add('core-motion-same-rounded-key','off-center-default-auto');c['patterns'][-1].update(x=0,y=0);c['patterns'].append(dict(id='tiny-core-motion',kind='core',core_px=4,x=1e-8,y=0,delay=.2))
    c=add('equal-core-no-new-geometry','off-center-default-auto');c['patterns'][-1].update(x=-0.,y=0);c['patterns'].append(dict(id='equal-newest',kind='core',core_px=4,x=0.,y=0,delay=.2))
    c=add('same-target-new-generation');c['patterns'][0].update(after=['start','parts'],repeat=0,until=dict(targets_cleared=True))
    for t in c['patterns'][0]['targets']:t['hp']=1
    c=add('same-target-set-new-order');a,b=c['patterns'][0]['targets'];a['z']=b['z']=0
    c['patterns']=[dict(id='first',kind='parts',targets=[a],after=['start','first'],repeat=0,until=dict(time=.2)),dict(id='second',kind='parts',targets=[b]),c['patterns'][-1]]
    c=add('scatter-shared-keys');c['combat']['weapons'][0].update(pellets=7,muzzles=2)
    c=add('cache-empty-geometry-gap','reopen');c['duration']=.45
    c=add('closed-negative-zero-base','base-core');c['enemy']['core_px']=-0.0
    c=overflow_case();c['name']='coordinate-core/cache-near-capacity';c['duration']=20.;rows.append(c)
    return rows

def overflow_case():
    source=next(c for c in cores() if c['name'].endswith('/127-targets'));c=copy.deepcopy(source)
    c['name']='coordinate-core/cache-capacity';c['duration']=30.
    c['weapon_metadata'].update(spread_start=14.,spread_end=13.,spread_change_pershot=.001)
    c['literal_weapon_geometry']=[dict(spread_start=14.,spread_end=13.,spread_shots=1000.) for _ in range(5)]
    for weapon in c['combat']['weapons'][1:]:weapon.update(mode='charge',charge=180,interval=180,min_cycle=180)
    return c
