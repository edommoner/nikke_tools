"""Compose a shared consumption quantity into the existing instant dispatcher."""
import ast
from reference_rewrite import rewrite_reference
from resource_specs import consume_resource


class ConsumptionRewrite(ast.NodeTransformer):
    def __init__(self):
        self.counts = {'consumption': 0}

    def visit_If(self, node):
        self.generic_visit(node)
        expected = ast.parse('val == -1.0', mode='eval').body
        if ast.dump(node.test) == ast.dump(expected):
            # Match the complete old consumption branch, not an unrelated -1.
            names = {n.id for n in ast.walk(node) if isinstance(n, ast.Name)}
            if {'consumed', 'current', 'gauges', 'gauge_id'} <= names:
                replacement = ast.parse('gauges[gauge_id], consumed = self.consume_resource(current, val, eff.get("minimum_remaining", 0.0))').body[0]
                self.counts['consumption'] += 1
                return ast.copy_location(replacement, node)
        return node


def prepare_dispatch(manager, dispatcher):
    # The caller has already applied shared activation preparation. Preserve it
    # by composing; the dispatch wrapper still performs retirement afterward.
    result = rewrite_reference(dispatcher, ConsumptionRewrite(), {'consumption': 1}, compose=True)
    manager.consume_resource = staticmethod(consume_resource)
    return result
