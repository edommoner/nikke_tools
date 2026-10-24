"""Bounded source evidence for missing target worlds and attack producers.

Historical documentation is evidence about the pinned model, not an instruction
that the current user's GPU goal may omit these effects.
"""
import ast,hashlib
from pathlib import Path

def source_name(path,root):
    """Repository identities use POSIX separators on every execution host."""
    return path.relative_to(root).as_posix()

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
        if calls:producer_calls.append(source_name(p,root))
    scoped=root/'app/battle_attack_group_runtime.py'
    assert producer_calls==['app/battle_attack_group_runtime.py'],'Unreviewed attack producer requires a fresh semantic audit'
    scoped_tree=ast.parse(scoped.read_text());scope=next(n for n in scoped_tree.body if isinstance(n,ast.FunctionDef) and n.name=='battle_attack_groups')
    assert [a.arg for a in scope.args.kwonlyargs]==['routing'] and scope.args.kw_defaults==[None]
    assert any(isinstance(n,ast.If) and ast.unparse(n.test)=="routing not in ('native', 'all-logical-enemies')" and len(n.body)==1 and isinstance(n.body[0],ast.Raise) for n in scope.body)
    # Only the declared scene model may override the canonical route. Native
    # mode must forward the original event, including per-pellet reselection.
    boss=next(n for n in scope.body if isinstance(n,ast.ClassDef) and n.name=='Boss')
    route=next(n for n in boss.body if isinstance(n,ast.FunctionDef) and n.name=='route')
    rewrites=[n for n in ast.walk(route) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='replace']
    assert len(rewrites)==1 and ast.unparse(rewrites[0])=="replace(event, rule='all_enemies')"
    override=next(n for n in route.body if isinstance(n,ast.If) and rewrites[0] in list(ast.walk(n)))
    assert ast.unparse(override.test)=="routing == 'all-logical-enemies' and current and (current[1] is not None) and (current[2] is event)"
    assert ast.unparse(route.body[-1])=='return super().route(event, has_state)'
    assert not any(isinstance(n,(ast.Expr,ast.Assign,ast.With)) and any(isinstance(c,ast.Call) and isinstance(c.func,ast.Name) and c.func.id=='battle_attack_groups' for c in ast.walk(n)) for n in scoped_tree.body)
    for name in ('engine_compat.py','engine_worker.py'):
        assert 'battle_attack_group_runtime' not in (root/'app'/name).read_text(),'Default installation requires a separate admission audit'
    sources.append(scoped)
    assert 'manager.notify(event,t,key.caster,attack_targets=sealed.result)' in (root/'app/attack_group_runtime.py').read_text(encoding="utf-8")
    impact=(root/'app/impact_runtime.py').read_text(encoding="utf-8");assert 'Impact(event.caster,actor.handle,classify_hit(event.hit_tag),HitOutcome.DAMAGING,event.damage)' in impact
    assert 'Impact(ev.caster,target,classify_hit(ev.hit_tag),HitOutcome.DAMAGING,amount)' in impact
    sources += [root/'app/attack_group_specs.py',up/'calculator/buff_manager.py',root/'app/impact_runtime.py',root/'app/impact_specs.py',root/'app/damage_query_runtime.py']
    from portable_model_gap_audit import verify as model_gaps
    remaining=model_gaps(root)
    return dict(passed=True,remaining_model_gaps=remaining,missing_target_worlds=list(rows),damage_factor_consumers=[],all_projectiles_early_return=True,multi_hit_listener_present=True,battle_attack_group_producer_calls=producer_calls,default_battle_attack_group_producer_calls=[],opt_in_producer_policy='native or all-logical-enemies; body/add only; normal physical shot returns',native_router_override=False,impacts_keep_default_attack_id_zero=True,historical_documents_are_not_current_instructions=True,gpu_supported=False,full_goal_complete=False,source_sha256={source_name(p,root):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources})
