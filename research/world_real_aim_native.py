"""Compose existing full-profile executor with target-pool and query observation."""
import hashlib,importlib.util,json
from pathlib import Path
from unittest.mock import patch
import engine_worker
from calculator import timeline
from calculator.boss_pattern import BossScript,BOSS_EVENTS
from portable_real_aim_policy import configured
from portable_interrupt_runtime import capture_interrupt_landings
from world_aimed_packet_native import capture_packet_sets
from world_actor_pool_native import summary,actor_bindings
from world_late_attack_random_native import capture_queries
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('real_aim_existing_reference',ROOT/'research/verify-world-projectile-rosters.py')
real=importlib.util.module_from_spec(spec);spec.loader.exec_module(real)


def observe(case,*,packets=True):
    names=case['body']['squad'];capture={};notices=[0]*4;deaths=[0]
    begin=BossScript.begin_frame;destroy=BossScript._destroy;retire=BossScript._retire
    execute=engine_worker.sim.execute;tick=timeline.CharState.tick
    def beginning(boss,t,enemy):
        if capture.get('frame')!=t:
            for event in boss._carry:notices[BOSS_EVENTS.index(event)]+=1
            capture.update(frame=t,boss=boss)
        return begin(boss,t,enemy)
    def destroying(boss,run,target,t):deaths[0]+=1;return destroy(boss,run,target,t)
    def retiring(boss,run,add,why,t,events,log=True):
        if why!='퇴장':deaths[0]+=1
        return retire(boss,run,add,why,t,events,log)
    def executing(run):
        result=execute(run);capture['result']=result;return result
    def ticking(actor,t,bm,enemy,cfg):
        capture['focus']=dict(aims=[bm.state.get('aim',{}).get(n,(None,''))[1] for n in names],camera=sum(1<<i for i,n in enumerate(names) if n in bm.state.get('camera',())),full_burst=bool(bm.state.get('full_burst')))
        return tick(actor,t,bm,enemy,cfg)
    from contextlib import nullcontext
    packet_context=capture_packet_sets(names) if packets else nullcontext(([],[]))
    with configured(case['body'],case['aim_policy']),capture_interrupt_landings() as receipts,packet_context as (shots,sets),capture_queries(names,with_selectors=True) as (_,queries),patch.object(BossScript,'begin_frame',beginning),patch.object(BossScript,'_destroy',destroying),patch.object(BossScript,'_retire',retiring),patch.object(engine_worker.sim,'execute',executing),patch.object(timeline.CharState,'tick',ticking):
        native=real.reference.native_reference(case['body'])
    boss=capture['boss'];result=capture['result'];body_hits=[h for h in result.hits if not (h.target or h.part)]
    target_world=dict(actor_pools=summary(boss,body_hits,notices,deaths[0]),world_nodes=[dict(blocked=r.blocked,opens=r.opens) for r in boss._runs],
        interrupt_damage=[boss.interrupt_dealt.get(n,0) for n in names],extra=[dict(identity=b.identity,generation=boss._runs[b.run].opens,extra_hits=boss._runs[b.run].targets[b.slot].extra_hits,extra_dealt=boss._runs[b.run].targets[b.slot].extra_dealt) for b in actor_bindings(boss) if int(b.kind)==6 and boss._runs[b.run].opens!=0],focus=capture['focus'])
    # Keep receipts and packet stream for CPU contracts, not bounded GPU traces.
    from dataclasses import asdict
    return dict(battle=native,physical_shots=shots,physical_packet_sets=sets,private_receipts=[asdict(row) for row in receipts],target_world=target_world,friendly_samples=queries)
