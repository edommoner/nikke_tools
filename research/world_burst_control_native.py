"""Static runner config and passive native tick state; never schedule a burst."""
import copy,struct
from portable_burst_control_specs import pack

def resolve(case,names):
    from runner.spec import build_config
    cfg=copy.deepcopy(case.get('burst_config',{}))
    if type(cfg) is not dict or set(cfg)-{'burst_delay','burst_pattern','burst_sequence'}:raise ValueError('Only static burst config keys accepted')
    controls=case['controls']
    if len(controls)!=5:raise ValueError('Five controls required')
    chars=[dict(name=n,control=copy.deepcopy(c)) for n,c in zip(names,controls)]
    for char,w in zip(chars,case['combat']['weapons']):
        if w.get('explicit_burst_stage'):char['burst_stage']=str(w['stage'])
    resolved=build_config(chars,cfg)
    cfg={k:resolved[k] for k in ('burst_delay','burst_pattern','burst_sequence') if k in resolved}
    waits={c['name']:c['control']['burst']['wait_own_cooldown'] for c in chars if 'wait_own_cooldown' in (c['control'].get('burst') or {})}
    words=pack(names,delays=cfg.get('burst_delay'),waits=waits,patterns=cfg.get('burst_pattern'),sequence=cfg.get('burst_sequence'))
    return cfg,words

def snapshot(controller,t,names):
    bits=lambda x:list(struct.unpack('<II',struct.pack('<d',x)))
    phase=controller._phase
    reentry=int(phase.startswith('reenter:'))
    stage=int(phase.split(':')[1]) if ':' in phase else {'idle':0,'switching':4,'full_burst':5}[phase]
    stages=[]
    for n in names:
        occupied=[i for i in (1,2,3) if n in controller.burst_order[str(i)]]
        stages.append(4 if len(occupied)==3 else occupied[0] if occupied else 0)
    wait=sum(1<<names.index(n) for n in controller._cd_wait_candidates or [])
    words=[*bits(t),stage,reentry,*bits(controller._next_action_t),*bits(controller._stage_open_t),controller._burst_count,*stages,wait,*[v for n in names for v in bits(controller.burst_ready_at[n])]]
    assert len(words)==25
    return dict(words=words,stage_open=controller._stage_open_t,cycles=controller._burst_count,stages=stages)
