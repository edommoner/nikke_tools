"""Authorized enemy DoT clock correction; pinned upstream stays byte-identical.

Keep a live carrier's exhausted schedule until refresh or retirement. Otherwise
the next frame re-creates its first tick. All damage/expiry ordering is native.
"""
import ast
from reference_rewrite import rewrite_reference


class BossDotClock(ast.NodeTransformer):
    def __init__(self):
        self.counts = dict(retirement=0)

    def visit_FunctionDef(self, node):
        if node.name != '_boss_dots':
            return self.generic_visit(node)
        for statement in ast.walk(node):
            if not isinstance(statement, ast.If):
                continue
            if ast.unparse(statement.test) != 'next_t > expires + 1e-09':
                continue
            if (len(statement.body) != 1 or
                    ast.unparse(statement.body[0]) != 'del _dot_sched[uid]' or
                    len(statement.orelse) != 1 or
                    ast.unparse(statement.orelse[0]) != '_dot_sched[uid][1] = next_t'):
                raise AssertionError('Enemy DoT retirement changed')
            statement.test = ast.copy_location(ast.BoolOp(op=ast.And(), values=[
                ast.parse('uid not in live', mode='eval').body, statement.test]), statement.test)
            self.counts['retirement'] += 1
        return node


def install():
    from calculator import timeline
    from runner import sim
    original = timeline.simulate
    if getattr(original, '_nikke_boss_dot_clock', False):
        return
    if sim.simulate is not original:
        raise AssertionError('Simulation aliases differ')
    corrected = rewrite_reference(original, BossDotClock(), dict(retirement=1), compose=True)
    corrected._nikke_boss_dot_clock = True
    timeline.simulate = sim.simulate = corrected
