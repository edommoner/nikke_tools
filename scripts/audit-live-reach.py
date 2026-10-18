"""CPU references for future live-part GPU state; no GPU support claim."""
import copy,hashlib,json,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app')]
import engine_worker
from calculator.boss_pattern import BossScript,validate,PART_REACH_KEY,INTERRUPT_REACH_KEY
from calculator.sim_result import HitEvent

def audit():
    cases=[]
    for kind,maximum,key in [('parts',5,PART_REACH_KEY),('interrupt',4,INTERRUPT_REACH_KEY)]:
        for reach in range(6):
            for hp in (0,5,25):
                for aimed in ['']+[f'target-{k}' for k in range(1,maximum+1)]:
                    pattern={'id':'authored-targets','kind':kind,'until':{'time':1} if hp==0 else {'targets_cleared':True},
                        'targets':[{'name':f'target-{k}','hp':hp,'reach':k,'emit_on_destroy':['event:part_destroy' if kind=='parts' else 'event:projectile_destroy']} for k in range(1,maximum+1)]}
                    enemy={'def':31784,'code':'수냉','core_px':0,'has_parts':False,'optimal_range_weapons':[]}
                    boss=BossScript(validate([copy.deepcopy(pattern)]),enemy,lambda caster,code:False)
                    frames=[];expected_total=0
                    for frame in range(6):
                        t=frame/60;events=boss.begin_frame(t,enemy);minimum=enemy[key]
                        hit=HitEvent(t=t,caster='authored-shooter',damage=100,is_crit=False,hit_tag='normal',aimed=aimed,
                            reach=reach if kind=='parts' else 0,part_damage=10 if kind=='parts' else 0,
                            interrupt_reach=reach if kind=='interrupt' else 0,interrupt_damage=10 if kind=='interrupt' else 0)
                        assert boss.gate(hit)
                        got=boss.part_hits(hit,t) if kind=='parts' else boss.interrupt_hits(hit,t)
                        want=[f'target-{k}' for k in range(1,min(reach,maximum)+1)
                              if f'target-{k}'!=aimed and (hp==0 or frame<(1 if hp==5 else 3))]
                        assert got==want,(kind,reach,hp,aimed,frame,got,want)
                        expected_total+=len(want)*10
                        targets=[dict(name=x.spec.name,destroyed=x.destroyed,dealt=x.dealt,extra_dealt=x.extra_dealt,extra_hits=x.extra_hits) for run in boss._runs for x in run.targets]
                        frames.append(dict(t=t,events=events,minimum_reach=minimum,hit_names=got,targets=targets))
                    if kind=='interrupt':assert boss.interrupt_dealt.get('authored-shooter',0)==expected_total
                    actual=sum(x['extra_dealt'] for x in frames[-1]['targets']);assert actual==expected_total
                    # A fatal hit earns its full 10, even if the target had 5 HP.
                    if hp==5 and expected_total:assert actual%10==0
                    destroyed={x['name'] for x in frames[-1]['targets'] if x['destroyed']}
                    emitted=sum(len(f['events']) for f in frames)
                    assert emitted==len(destroyed),(kind,reach,hp,aimed,emitted,destroyed)
                    assert not frames[0]['events'],'Destruction notifications must wait for the next frame'
                    cases.append(dict(input=dict(pattern=pattern,reach=reach,aimed=aimed,frames=6,damage_per_extra_target=10),expected_frames=frames,
                                      expected_extra_damage=expected_total,interrupt_damage_is_outside_total=kind=='interrupt'))
    files=['scripts/audit-live-reach.py','research/upstream/nikke-calc-master/calculator/boss_pattern.py','research/upstream/nikke-calc-master/calculator/sim_result.py']
    return dict(generated_at=datetime.now(timezone.utc).isoformat(),cpu_reference_only=True,gpu_implemented=False,combat_integrated=False,
        passed=True,cases=cases,scope='Authored per-target hit stimuli, cumulative reach, aimed-target exclusion, unbreakable HP-zero targets, overkill and next-frame destruction events. No GPU or full battle claim.',
        source_sha256={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in files})

if __name__=='__main__':
    report=audit();(ROOT/'research/detail-live-reach-cpu-references.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(passed=report['passed'],cases=len(report['cases']),gpu_implemented=False)))
