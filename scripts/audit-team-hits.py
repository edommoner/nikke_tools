"""Pinned CPU team-hit attribution references; deliberately no GPU support claim."""
import copy,hashlib,json,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
import engine_worker as a
from calculator.buff_manager import BuffManager
names=['D : 킬러 와이프','앨리스','모더니아','리타','크라운']
chars=[dict(name=n,skill_levels={'1':i+1,'2':i+1,'3':10 if i==0 else i},_weapon=a.META[n]) for i,n in enumerate(names)]
stats={n:{'atk':100000+i*10000,'hp':1000000,'def':1000} for i,n in enumerate(names)}
attacks=[1,2,1,4,2,3]
rows=[]
for event,prefix in [('squad_part_hit','part_hit_count'),('squad_body_hit','body_hit_count')]:
    for threshold in (1,3):
        for gated in (False,True):
            effects=[(dict(source='스킬3',name='team probe',type='buff',stat='atk_caster_based_pct',target='self',values={str(i):10*i for i in range(1,11)},duration=1,trigger=dict(timing=[f'{prefix}:{threshold}'],condition=['self_state:owner gate'])),names[0])]
            if gated:effects.insert(0,(dict(source='스킬1',name='owner gate',type='buff',stat='',target='self',fixed_value=0,duration=-1,trigger=dict(timing=['battle_start'],condition=[])),names[0]))
            class BM(BuffManager):
                def _register_all(self):
                    self._effects=copy.deepcopy(effects);self._build_notify_index()
            bm=BM(copy.deepcopy(chars),state=dict(base_stats=copy.deepcopy(stats),enemy={},full_burst=False,rng_expected=True,rng_acc={}))
            for name in names:bm.notify('battle_start',0,name)
            snapshots=[]
            for step,attacker in enumerate(attacks,1):
                t=step/10;bm.tick(t);bm.notify_team_hit(event,t,names[attacker])
                active=[ab for ab in bm._active if ab.effect.get('name')=='team probe']
                if not gated:assert not active
                if gated and step%threshold==0:
                    assert any(ab.caster==names[attacker] for ab in active)
                snapshots.append(dict(time=t,attacker=names[attacker],team_count=bm._event_counts['__squad__'][event],
                    active=[dict(caster=ab.caster,targets=ab.target_chars,stack=ab.stack,value=bm._get_value(ab.effect,ab,ab.caster)) for ab in active],
                    atk_flat={n:bm.get_buffs(n,'__enemy__',t).get('atk_flat',0) for n in names}))
            assert snapshots[-1]['team_count']==len(attacks)
            bm.tick(2)
            assert not any(ab.effect.get('name')=='team probe' for ab in bm._active)
            rows.append(dict(event=event,threshold=threshold,owner_gate=gated,chars=chars,base_stats=stats,effects=effects,snapshots=snapshots))
files=['scripts/audit-team-hits.py','research/upstream/nikke-calc-master/calculator/buff_manager.py','research/upstream/nikke-calc-master/calculator/timeline.py']
report=dict(generated_at=datetime.now(timezone.utc).isoformat(),passed=True,cpu_reference_only=True,gpu_implemented=False,
    scope='Global count across attackers; condition owner versus activation attacker; caster-based ATK, skill values, target self and expiry. Authored stimuli, no GPU result claim.',cases=rows,
    source_sha256={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in files})
(ROOT/'research/detail-team-hits-cpu-references.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(passed=True,cases=len(rows),gpu_implemented=False)))
