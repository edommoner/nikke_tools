"""Small paired audit of intrinsic HP transforms after attributed aggregation.

Observes original effective_max_hp return values and scalar ancestor locals;
never calls a reference getter again. Audit only; not used to tune L2.
"""
import argparse, collections, json, pathlib, subprocess, sys, time
from unittest.mock import patch
import bucket_log as b
from profile_s18 import ProfileLog, KEYS, factors


class AuditLog(ProfileLog):
    def __init__(self,target,duration):
        super().__init__(target,duration);self.hp={};self.corrected=[];self.transforms=collections.Counter()
    def __enter__(self):
        super().__enter__()
        from calculator.buff_manager import BuffManager
        original=BuffManager.effective_max_hp
        def observe(manager,name,*a,**kw):
            value=original(manager,name,*a,**kw);self.hp[name]=value;return value
        self.stack.enter_context(patch.object(BuffManager,'effective_max_hp',observe));return self
    def scalar(self,frame,result):
        super().scalar(frame,result);r=self.scalars[-1];loc=frame.f_locals
        pair=self.buff_cache.get(id(loc['buffs']))
        parts=pair[1] if pair and pair[0] is loc['buffs'] else self.latest.get(r['attacker'],(None,{}))[1]
        from calculator.buff_manager import _BUFFS_ZERO
        attributed={k:_BUFFS_ZERO.get(k,0.)+sum(v.get(k,0.) for v in parts.values()) for k in KEYS}
        attributed['crit_rate']+=.15;attributed['crit_rate_skill']+=.15
        attributed['is_element_match']=loc['buffs'].get('is_element_match',False)
        caller=frame.f_back;scalings=[];pct=0.
        for _ in range(24):
            if caller is None:break
            v=caller.f_locals
            if '_scalings' in v:
                scalings=v['_scalings'];pct=float(v.get('eff',{}).get('scaling_hp_pct',0.));break
            caller=caller.f_back
        if 'max_hp_replacement' in scalings:
            attributed['atk_pct']=0.;attributed['atk_flat']=0.;self.transforms['max_hp_replacement']+=1
        if 'max_hp_additive' in scalings:
            attributed['atk_flat']+=self.hp[r['attacker']]*pct/100.;self.transforms['max_hp_additive']+=1
        conv=loc['buffs'].get('charge_speed_overflow_conversion_pct',0.)
        overflow=max(0.,loc['buffs'].get('charge_speed_pct',0.)-100.)
        if conv>0 and overflow>0:
            attributed['charge_dmg_pct']+=overflow*conv/100.
            self.transforms['charge_speed_overflow_conversion']+=1
        formed=factors(loc['base_atk'],attributed,loc['weapon'],loc['hit_type'],loc['enemy_def'])
        self.corrected.append([abs(x-y)/max(abs(x),1e-12) for x,y in zip(r['factors'],formed)])


def worker(request):
    import engine_worker
    body=request['body'];start=time.perf_counter()
    with AuditLog(request['target'],body['duration']) as observer:payload=engine_worker.evaluate(body)
    return dict(payload=payload,payload_digest=b.digest(payload),seconds=time.perf_counter()-start,
        corrected_max_residual=[max((r[i] for r in observer.corrected),default=0.) for i in range(7)],
        transforms=dict(observer.transforms),scalars=len(observer.scalars))


def run(out,character=None,selection_id=None):
    selection=json.loads((out/'selection.json').read_text())['selected'];shared=json.loads((out/'body.json').read_text());rows=[]
    for name in ([character] if character else ('킬로','메이든 : 아이스 로즈','2B')):
        row=next(r for r in selection if (r['id']==selection_id if selection_id is not None else r['target']==name))
        if name not in row['members']:raise ValueError('Audit target absent')
        body=dict(shared,squad=row['members'],duration=10.)
        request=dict(target=name,body=body,logged=False)
        plain=subprocess.run([sys.executable,'-B',str(b.ROOT/'research/team-search/profile_s18.py')],input=json.dumps(request),text=True,capture_output=True,check=True)
        plain=json.loads(plain.stdout)
        logged=subprocess.run([sys.executable,'-B',__file__,'--worker'],input=json.dumps(request),text=True,capture_output=True,check=True)
        logged=json.loads(logged.stdout)
        if logged['payload']!=plain['payload']:raise AssertionError('Non-interference')
        logged.pop('payload');rows.append(dict(target=name,standard_squad=row['members'],duration=10,
            non_interference=True,baseline_digest=plain['payload_digest'],baseline_seconds=plain['seconds'],**logged))
    (out/('overflow-audit.json' if character else 'hp-transform-audit.json')).write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(rows,ensure_ascii=False))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--worker',action='store_true');p.add_argument('--out',type=pathlib.Path);p.add_argument('--character');p.add_argument('--selection-id',type=int);a=p.parse_args()
    if a.worker:print(json.dumps(worker(json.load(sys.stdin)),ensure_ascii=False))
    else:run(a.out,a.character,a.selection_id)
