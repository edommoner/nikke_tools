"""Immutable per-attack source exclusions; never alter resident buff carriers.

Authored later cast effects cannot contribute to that delayed parent. Nested
hit callbacks create their own scope and see ordinary live effects.
"""
import ast
from dataclasses import dataclass
from reference_rewrite import rewrite_reference


@dataclass(frozen=True)
class DamageQueryScope:
    owner: str
    excluded_names: frozenset[str] = frozenset()

    def __post_init__(self):
        object.__setattr__(self, 'excluded_names', frozenset(self.excluded_names))

    def excludes(self, carrier):
        return carrier.caster == self.owner and carrier.effect.get('name') in self.excluded_names


def scope(self, owner, names=()):
    return DamageQueryScope(owner, frozenset(names))


class AttackQueries(ast.NodeTransformer):
    def __init__(self):
        self.stack = []
        self.counts = dict(scope=0, magnitude=0, hp_basis=0, buffs=0)

    def visit_FunctionDef(self, node):
        self.stack.append(node.name)
        self.generic_visit(node)
        self.stack.pop()
        if node.name == '_handle_damage_eff':
            statement = ast.parse('_damage_scope = bm.damage_query_scope(caster, eff.get("_exclude_buffs", ()))').body[0]
            node.body.insert(0, ast.copy_location(statement, node.body[0]))
            self.counts['scope'] += 1
        return node

    def visit_For(self, node):
        self.generic_visit(node)
        if self.stack[-1] == '_handle_damage_eff' and isinstance(node.target, ast.Name) and node.target.id == 'ab':
            if any(isinstance(n, ast.Constant) and n.value == 'dmg_scale_mag_pct' for n in ast.walk(node)):
                statement = ast.parse('if _damage_scope.excludes(ab):\n continue').body[0]
                node.body.insert(0, ast.copy_location(statement, node.body[0]))
                self.counts['magnitude'] += 1
        return node

    def visit_Call(self, node):
        self.generic_visit(node)
        if self.stack[-1] != '_handle_damage_eff' or not isinstance(node.func, ast.Attribute):
            return node
        if node.func.attr == 'effective_max_hp':
            assert not node.keywords
            node.keywords.append(ast.keyword(arg='query_scope', value=ast.Name(id='_damage_scope', ctx=ast.Load())))
            self.counts['hp_basis'] += 1
        elif node.func.attr == 'get_buffs' and any(k.arg == 'exclude_names' for k in node.keywords):
            keyword = next(k for k in node.keywords if k.arg == 'exclude_names')
            keyword.value = ast.parse('_damage_scope.excluded_names', mode='eval').body
            self.counts['buffs'] += 1
        return node


class MaximumHPQuery(ast.NodeTransformer):
    def __init__(self):
        self.counts = dict(argument=0, filter=0)

    def visit_FunctionDef(self, node):
        assert node.name == 'effective_max_hp' and not node.args.kwonlyargs
        node.args.kwonlyargs.append(ast.arg(arg='query_scope'))
        node.args.kw_defaults.append(ast.Constant(None))
        self.counts['argument'] += 1
        return self.generic_visit(node)

    def visit_For(self, node):
        self.generic_visit(node)
        if isinstance(node.iter, ast.Attribute) and node.iter.attr == '_active':
            assert isinstance(node.target, ast.Name) and node.target.id == 'ab'
            statement = ast.parse('if query_scope is not None and query_scope.excludes(ab):\n continue').body[0]
            node.body.insert(0, ast.copy_location(statement, node.body[0]))
            self.counts['filter'] += 1
        return node


def install():
    from calculator import timeline, buff_manager
    from runner import sim
    manager = buff_manager.BuffManager
    if getattr(manager, '_nikke_damage_queries', False):
        return
    assert timeline.simulate is sim.simulate
    assert getattr(manager, '_nikke_heal_sharing', False)
    # Compose onto retained final trees: storage/sharing and hp_copy edits
    # remain present; no reconstruction transformer is replayed twice.
    simulate = rewrite_reference(timeline.simulate, AttackQueries(),
        dict(scope=1, magnitude=1, hp_basis=2, buffs=1), compose=True)
    maximum_hp = rewrite_reference(manager.effective_max_hp, MaximumHPQuery(),
        dict(argument=1, filter=1), compose=True)
    manager.damage_query_scope = scope
    manager.effective_max_hp = maximum_hp
    timeline.simulate = sim.simulate = simulate
    manager._nikke_damage_queries = True
