"""Target predicates use the immutable event target before current aiming.

An already launched impact or captured counter completion cannot be relabelled
because aiming changes or the same public actor ID respawns during a child.
"""
import ast
from effect_runtime import state
from impact_specs import ActorKind
from reference_rewrite import rewrite_reference


def target_is_add(manager,caster):
    frames=state(manager).event_stack
    target=frames[-1].target if frames else None
    if target is not None:
        if target.kind==ActorKind.ADD:return True
        if target.kind in (ActorKind.BODY,ActorKind.PART):return False
        raise ValueError('Logical target predicate requires an explicit actor policy')
    # Notifications with no target retain the evaluator's selected-aim model.
    return manager._resolve_enemies('target',caster)[0]!='__enemy__'


def target_is_stunned(manager,caster):
    from enemy_recipient_runtime import dynamic_registry,current_label
    return manager.is_stunned(current_label(manager) if dynamic_registry(manager) is not None else '__enemy__')


class TargetPredicate(ast.NodeTransformer):
    def __init__(self):self.counts=dict(target_predicate=0,stunned_predicate=0)
    def visit_Call(self,node):
        self.generic_visit(node)
        if isinstance(node.func,ast.Attribute) and node.func.attr=='is_stunned' and len(node.args)==1 and isinstance(node.args[0],ast.Constant) and node.args[0].value=='__enemy__':
            self.counts['stunned_predicate']+=1
            return ast.copy_location(ast.parse('self.context_target_is_stunned(caster)',mode='eval').body,node)
        return node
    def visit_Compare(self,node):
        left=node.left
        if (len(node.ops)==1 and isinstance(node.ops[0],ast.NotEq) and
            len(node.comparators)==1 and isinstance(node.comparators[0],ast.Constant) and node.comparators[0].value=='__enemy__' and
            isinstance(left,ast.Subscript) and isinstance(left.value,ast.Call) and isinstance(left.value.func,ast.Attribute) and left.value.func.attr=='_resolve_enemies'):
            assert ast.unparse(left)=="self._resolve_enemies('target', caster)[0]"
            self.counts['target_predicate']+=1
            return ast.copy_location(ast.parse('self.context_target_is_add(caster)',mode='eval').body,node)
        return self.generic_visit(node)


def install():
    from calculator.buff_manager import BuffManager
    if getattr(BuffManager,'_nikke_target_context_predicates',False):return
    BuffManager.context_target_is_add=target_is_add
    BuffManager.context_target_is_stunned=target_is_stunned
    BuffManager._condition_ok=rewrite_reference(BuffManager._condition_ok,TargetPredicate(),dict(target_predicate=1,stunned_predicate=1))
    BuffManager._nikke_target_context_predicates=True
