"""Use one session initializer for regular and reload-completion mode entry."""
import ast
from reference_rewrite import rewrite_reference

def begin_session(actor):
    actor._in_weapon_change=True
    actor._wc_shots=0
    actor._wc_new_session=True
    actor._wc_ammo_full=None
    actor._wc_ammo_restored=False

class ModeSessionEntry(ast.NodeTransformer):
    def __init__(self):self.counts=dict(regular=0,reload=0)
    def visit_If(self,node):
        if ast.dump(node.test)==ast.dump(ast.parse('not self._in_weapon_change',mode='eval').body):
            expected=ast.parse('self._in_weapon_change=True\nself._wc_shots=0\nself._wc_new_session=True\nself._wc_ammo_full=None\nself._wc_ammo_restored=False').body
            if [ast.dump(s) for s in node.body]!=[ast.dump(s) for s in expected]:raise AssertionError('Unexpected regular mode entry')
            self.counts['regular']+=1;node.body=[ast.copy_location(ast.parse('self.begin_weapon_session()').body[0],node.body[0])]
        return self.generic_visit(node)
    def visit_Assign(self,node):
        if ast.dump(node)==ast.dump(ast.parse('self._in_weapon_change=True').body[0]):
            self.counts['reload']+=1;return ast.copy_location(ast.parse('self.begin_weapon_session()').body[0],node)
        return node

def install():
    from calculator.timeline import CharState
    if getattr(CharState,'_nikke_mode_session_entry',False):return
    CharState.begin_weapon_session=begin_session
    CharState.tick=rewrite_reference(CharState.tick,ModeSessionEntry(),dict(regular=1,reload=1))
    CharState._nikke_mode_session_entry=True
