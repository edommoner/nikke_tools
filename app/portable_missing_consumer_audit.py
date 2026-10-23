"""Bounded source evidence for missing target worlds and attack producers.

Historical documentation is evidence about the pinned model, not an instruction
that the current user's GPU goal may omit these effects.
"""
import ast,hashlib
from pathlib import Path

def verify(root):
    root=Path(root);up=root/'research/upstream/nikke-calc-master';timeline=up/'calculator/timeline.py';status=up/'docs/IMPL-STATUS.md';damage=up/'calculator/damage.py'
    tree=ast.parse(timeline.read_text(encoding="utf-8"));handlers=[n for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name=='_handle_damage_eff'];assert len(handlers)==1
    first=handlers[0].body[0];assert isinstance(first,ast.If) and ast.dump(first.test)==ast.dump(ast.parse('eff.get("target") == "all_projectiles"',mode='eval').body);assert len(first.body)==1 and isinstance(first.body[0],ast.Return) and first.body[0].value is None
    rows={s:next(line for line in status.read_text(encoding="utf-8").splitlines() if line.startswith('| `'+s+'` |')) for s in ('projectile_dmg_pct','shield_dmg_pct')};assert all('❌' in x for x in rows.values())
    constants={n.value for n in ast.walk(ast.parse(damage.read_text(encoding="utf-8"))) if isinstance(n,ast.Constant) and isinstance(n.value,str)};assert not constants.intersection(rows)
    producer_calls=[];sources=[timeline,status,damage,root/'app/attack_group_runtime.py']
    for p in sorted((root/'app').glob('*.py')):
        if p.name=='attack_group_runtime.py':continue
        t=ast.parse(p.read_text(encoding="utf-8"));calls=[n for n in ast.walk(t) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr in ('begin_attack_targets','finish_attack_targets')]
        if calls:producer_calls.append(str(p.relative_to(root)))
    assert not producer_calls,'New attack producer requires a fresh semantic audit'
    assert 'manager.notify(event,t,key.caster,attack_targets=sealed.result)' in (root/'app/attack_group_runtime.py').read_text(encoding="utf-8")
    impact=(root/'app/impact_runtime.py').read_text(encoding="utf-8");assert 'Impact(event.caster,actor.handle,classify_hit(event.hit_tag),HitOutcome.DAMAGING,event.damage)' in impact
    assert 'Impact(ev.caster,target,classify_hit(ev.hit_tag),HitOutcome.DAMAGING,amount)' in impact
    sources += [root/'app/attack_group_specs.py',up/'calculator/buff_manager.py',root/'app/impact_runtime.py',root/'app/impact_specs.py',root/'app/damage_query_runtime.py']
    from portable_model_gap_audit import verify as model_gaps
    remaining=model_gaps(root)
    return dict(passed=True,remaining_model_gaps=remaining,missing_target_worlds=list(rows),damage_factor_consumers=[],all_projectiles_early_return=True,multi_hit_listener_present=True,battle_attack_group_producer_calls=producer_calls,impacts_keep_default_attack_id_zero=True,historical_documents_are_not_current_instructions=True,gpu_supported=False,full_goal_complete=False,source_sha256={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources})
