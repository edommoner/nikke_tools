"""CPU-only cover revival witnesses for Biscuit and future GPU target support."""
import ast,hashlib,importlib.util,inspect,json,math,random,sys,textwrap
from datetime import datetime,timezone
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sp=importlib.util.spec_from_file_location('cover_revive_cpu',ROOT/'scripts/verify-survival-detail.py');v=importlib.util.module_from_spec(sp);sp.loader.exec_module(v)
N=v.N;B=v.B;E=v.E;code=v.timeline.simulate.__code__
lines,first=inspect.getsourcelines(v.timeline.simulate);tree=ast.parse(textwrap.dedent(''.join(lines)))
advance=[n for n in ast.walk(tree) if isinstance(n,ast.AugAssign) and isinstance(n.target,ast.Name) and n.target.id=='t' and isinstance(n.value,ast.Name) and n.value.id=='DT'];assert len(advance)==1
end_line=first+advance[0].lineno-1;rows=[]
for name in ('no-broken-cover','only-broken-revives','recipient-maximum','healing-cannot-revive','ordinary-heal-living-positive','repeat-revival','random-includes-caster','random-excludes-down','cover-condition-rearms'):
    b=v.v.body(1)
    random_case=name.startswith('random-')
    b['enemy']['patterns']=[] if name=='no-broken-cover' else [dict(id='break covers',kind='attack',delay=.1,until={'time':.7},spec=dict(coeff=100,atk=1000000 if name=='ordinary-heal-living-positive' else 5000000,target='all' if random_case else 'slot:1',hits=2 if name=='repeat-revival' else 1,interval=.4))]
    if name=='random-excludes-down':b['enemy']['patterns'].append(v.lethal('slot:5',at=.15))
    extra={n:[] for n in N};extra[N[0]].append(E('take cover','instant','force_reload',0,'all_allies'))
    if name=='recipient-maximum':extra[N[0]].append(B('recipient cover maximum','cover_hp_pct',50))
    if name in ('healing-cannot-revive','ordinary-heal-living-positive'):extra[N[0]].append(E('ordinary healing','instant','cover_heal_pct',100,event='every:0.3s',max_trigger=1))
    else:extra[N[0]].append(E('revive cover','instant','cover_revive',75 if name=='recipient-maximum' else 50,'allies_broken_cover_random:2' if random_case else 'all_allies',event='every:0.3s',max_trigger=2 if name=='repeat-revival' else 1))
    if name=='cover-condition-rearms':
        e=B('broken-cover power','atk_pct',50,event='passive');e['trigger']['condition']=['not_self_cover_alive'];extra[N[0]].append(e)
    frames=[];healed=[];selected=[];on_notify=v.BuffManager.notify;on_target=v.BuffManager._resolve_target
    def notify(self,event,t,caster,**kwargs):
        if event=='event:cover_healed':healed.append(dict(time=t,caster=caster))
        return on_notify(self,event,t,caster,**kwargs)
    def target(self,target,caster):
        result=on_target(self,target,caster)
        if isinstance(target,str) and target.startswith('allies_broken_cover_random:'):selected.append(dict(time=self._cur_t,caster=caster,selected=list(result),down=list(self.state.get('down',set()))))
        return result
    def trace(frame,event,arg):
        if frame.f_code is not code:return None
        if event=='line' and frame.f_lineno==end_line:
            local=frame.f_locals;state=local['state'];bm=local['bm'];t=local['t']
            frames.append(dict(time=t,cover_hp={n:state['cover_hp'][n] for n in N},cover_max_hp={n:state['cover_max_hp'][n] for n in N},source_atk_pct=bm.get_buffs(N[0],'reference-enemy',t).get('atk_pct',0)))
        return trace
    with v.v.context(name,extra),patch.object(v.BuffManager,'notify',notify),patch.object(v.BuffManager,'_resolve_target',target):
        old=sys.gettrace()
        try:sys.settrace(trace);cpu=v.v.v.a.evaluate(b)
        finally:sys.settrace(old)
    assert frames
    assert len(healed)==(1 if name=='ordinary-heal-living-positive' else 0),(name,healed)
    if name not in ('no-broken-cover','ordinary-heal-living-positive'):assert any(f['cover_hp'][N[0]]==0 for f in frames),name
    if name=='healing-cannot-revive':assert frames[-1]['cover_hp'][N[0]]==0
    if name in ('only-broken-revives','recipient-maximum','repeat-revival','cover-condition-rearms'):
        ratio=.75 if name=='recipient-maximum' else .5
        assert math.isclose(frames[-1]['cover_hp'][N[0]],frames[-1]['cover_max_hp'][N[0]]*ratio,abs_tol=1e-9),name
    if name=='no-broken-cover':assert all(f['cover_hp'][n]==f['cover_max_hp'][n] for f in frames for n in N)
    if random_case:assert selected and all(len(x['selected'])==2 and not set(x['selected'])&set(x['down']) for x in selected),selected
    if name=='random-includes-caster':assert any(N[0] in x['selected'] for x in selected),selected
    if name=='cover-condition-rearms':assert any(f['source_atk_pct']==50 for f in frames) and frames[-1]['source_atk_pct']==0
    rows.append(dict(name=name,cpu_reference_verified=True,gpu_implemented=False,total=cpu['total_damage'],frames=frames,cover_healed_events=healed,random_targets=selected,final_skill_rng=list(random.getstate()[1])));print(json.dumps(dict(name=name,passed=True,gpu_implemented=False)),flush=True)
files=['research/audit-cover-revival.py','scripts/verify-survival-detail.py','scripts/verify-incoming-detail.py','app/engine_worker.py','app/engine_compat.py','app/survival_compat.py','research/upstream/nikke-calc-master/calculator/buff_manager.py','research/upstream/nikke-calc-master/calculator/timeline.py']
r=dict(generated_at=datetime.now(timezone.utc).isoformat(),cpu_reference_verified=True,gpu_implemented=False,objective_complete=False,cases=rows,source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files})
(ROOT/'research/detail-cover-revival-cpu-reference.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
