"""Cast/landing witnesses using the existing full-native pending world fixture."""
import copy
from world_pending_cases import fixtures as pending
from world_enemy_attack_cases import field
from portable_burst_recipient_cases import instant

def fixtures():
    seed=copy.deepcopy(pending()[0]);rows=[]
    def add(label,stat='sequential_damage:3',enabled=True,stage=3,extra=None):
        c=copy.deepcopy(seed);c['name']='full-burst-landing-'+label;c['effects']=c['effects'][:1];c['owners']=[0]
        if stage==2:
            c['combat']['weapons'][0]['stage']=2;c['combat']['weapons'][2]['stage']=3
        marker=field('',0,'self','cast-count',max_stack=9);marker['trigger']['timing']=['battle_start','full_burst_start']
        effects=[marker,field('',0,'self','cast-gate'),field('atk_pct',10,'self','earlier-atk','burst_cast'),dict(name='landing',source='스킬3',type='damage',stat=stat,fixed_value=100,target='boss',land_in_full_burst=enabled,max_trigger=1,trigger=dict(timing=['burst_cast'],condition=['self_state:cast-gate'])),dict(instant('remove_named_buff',0,'self','consume-gate','burst_cast'),target_effect='cast-gate'),field('atk_pct',200,'self','later-atk','burst_cast'),field('atk_pct',100,'self','entry-atk','full_burst_start')]
        if extra=='legacy':effects.insert(4,dict(name='legacy-bonus',source='스킬3',type='damage',stat='bonus_damage',fixed_value=50,target='boss',trigger=dict(timing=['burst_cast'],condition=[])))
        if extra in ('magnitude-before','magnitude-after'):
            change=field('dmg_scale_mag_pct',100,'self','magnitude','burst_cast',target_effect='landing');idx=next(i for i,e in enumerate(effects) if e['name']=='landing');effects.insert(idx+(extra.endswith('after')),change)
        if extra=='child':effects.extend([dict(name='child',source='스킬1',type='damage',stat='bonus_damage',fixed_value=20,target='boss',trigger=dict(timing=['hit_count:landing:1'],condition=[])),field('atk_pct',20,'self','child-atk','hit_count:landing:1',max_stack=20)])
        c['effects'].extend(effects);c['owners'].extend([0]*len(effects))
        delayed=enabled and stage==3
        count=1 if stat.endswith(':cast-count') else 0 if stat.endswith(':missing') else max(0,int(stat.partition(':')[2] or 1))
        c['contract']=dict(delayed=delayed,hits=count,reference=stat.endswith(':cast-count'),missing=stat.endswith(':missing'),extra=extra,stage=stage,latched_count=(1 if stat.endswith(':cast-count') else 0 if stat.endswith(':missing') else int(stat.partition(':')[2] or 1)),excludes=['later-atk']+(['magnitude'] if extra=='magnitude-after' else []) if delayed else [])
        rows.append(c);return c
    add('one-hit','damage');add('three-hits');add('thirteen-hits','sequential_damage:13');add('zero','sequential_damage:0');add('negative','sequential_damage:-2');add('latched-reference','sequential_damage:cast-count');add('missing-reference','sequential_damage:missing');add('disabled',enabled=False);add('stage2-immediate',stage=2);add('legacy-coexists',extra='legacy');add('magnitude-before',extra='magnitude-before');add('magnitude-after',extra='magnitude-after');add('children-after-entry',extra='child')
    return rows
