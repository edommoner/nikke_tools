"""Observe canonical final-shot/retirement order, without a scheduler rewrite."""
import copy,hashlib


def fixtures():
    rows=[]
    for name,hits,interval,frames in [('single',1,0.,[0.,1/60]),('three-spaced',3,.2,[0.,.2,.4,.5]),('three-coincident',3,0.,[0.,1/60]),('catchup',3,.2,[0.,.6,.7])]:
        rows.append(dict(name='add-self-destruct/'+name,hits=hits,frames=frames,patterns=[dict(id='wave',kind='summon',spec=dict(count=1,hp=1000.,attack=dict(atk=100.,coeff=100.,hits=hits,interval=interval,target='all'),self_destruct=True))]))
    return rows


def observe(case):
    import engine_worker  # Install the pinned canonical calculator import path.
    from calculator.boss_pattern import validate,BossScript
    enemy=dict(patterns=copy.deepcopy(case['patterns']),defense=0)
    boss=BossScript(validate(copy.deepcopy(case['patterns']),squad_size=5,coord=True),enemy,lambda *_:False)
    frames=[]
    for t in case['frames']:
        events=boss.begin_frame(t,enemy);add=boss._runs[0].adds[0]
        frames.append(dict(time=t,events=list(events),enemy_count=boss.enemy_count,alive=add.alive,gone=add.gone,fired=add.fired,queued=[dict(index=h.index,source=h.source,pattern=h.pattern) for h in boss.attacks]))
        boss.attacks.clear()
    native=dict(frames=frames,canonical_methods={k:hashlib.sha256(getattr(BossScript,k).__code__.co_code).hexdigest() for k in ('begin_frame','_add_attacks','_retire')},full_battle_validation=False,gpu_supported=False)
    return native,[]


def verify(case,native):
    frames=native['frames'];shots=[h for r in frames for h in r['queued']]
    assert [h['index'] for h in shots]==list(range(case['hits'])),'Every original queued shot must survive, in order'
    assert len({(h['source'],h['pattern']) for h in shots})==1
    deaths=[r for r in frames if 'enemy_death' in r['events']]
    assert len(deaths)==1 and sum(r['events'].count('enemy_death') for r in frames)==1
    final=deaths[0]
    assert final['queued'] and final['queued'][-1]['index']==case['hits']-1,'Retirement must keep the final queued shot'
    assert not final['alive'] and final['enemy_count']==1 and final['gone']=='자폭'
    assert final['fired']==case['hits']
    assert all(not r['alive'] and not r['queued'] and not r['events'] and r['enemy_count']==1 for r in frames if r['time']>final['time'])
    return dict(verified=True,reference_model_gap=False,queued_shots=len(shots),retirement_time=final['time'],final_shots_queued_after_source_retirement=True,scope='Canonical BossScript component only; no full battle or GPU admission')
