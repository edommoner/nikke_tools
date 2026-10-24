"""Bounded source audit for the remaining unmodelled canonical consumers.

This is a source assertion, not a game specification or support certificate.
"""
import ast,hashlib
from pathlib import Path
MISSING_STATS=('enemy_movement_disable','force_move','effect_range_pct','effect_target_count_add','lock_on')
MODULES=('calculator/timeline.py','calculator/buff_manager.py','calculator/boss_pattern.py','calculator/damage.py')

def verify(root,overrides=None):
 root=Path(root);base='research/upstream/nikke-calc-master/';overrides=overrides or {};text={}
 for name in (*MODULES,'calculator/aim.py','docs/IMPL-STATUS.md'):
  path=base+name;text[name]=overrides.get(path,(root/path).read_text(encoding='utf-8'))
 strings={name:{n.value for n in ast.walk(ast.parse(text[name])) if isinstance(n,ast.Constant) and isinstance(n.value,str)} for name in MODULES}
 status=text['docs/IMPL-STATUS.md'].splitlines();missing={}
 for stat in MISSING_STATS:
  row=next(line for line in status if line.startswith('| `'+stat+'` |'));assert '❌' in row,'Implementation status changed: '+stat
  readers=[name for name,values in strings.items() if stat in values];assert not readers,'New canonical consumer requires review: '+stat
  missing[stat]=dict(native_consumers=readers,status_row=row,scope=list(MODULES))
 trees={name:ast.parse(text[name]) for name in MODULES}
 functions=lambda name,fn:[n for n in ast.walk(trees[name]) if isinstance(n,ast.FunctionDef) and n.name==fn]
 ranked=functions('calculator/boss_pattern.py','_ranked');assert len(ranked)==1
 assert not any(isinstance(n,ast.Constant) and n.value=='target_and_nearby' for n in ast.walk(ranked[0]))
 assert isinstance(ranked[0].body[-1],ast.Return) and isinstance(ranked[0].body[-1].value,ast.Constant) and ranked[0].body[-1].value.value is None
 helpers=functions('calculator/timeline.py','_resolve_targets');assert len(helpers)==1
 helper=ast.unparse(helpers[0]);assert 'allies = [n for n in names if n in char_states]' in helper and 'return allies' in helper
 handlers=functions('calculator/timeline.py','handle_ammo_charge_pct');assert len(handlers)==1
 body=handlers[0].body;assert any(isinstance(n,ast.For) for n in body)
 last=body[-1];assert isinstance(last,ast.If) and 'bm.notify(' in ast.unparse(last) and 'eff_name' in ast.unparse(last)
 coordinate=functions('calculator/timeline.py','_coord_skill_hits');assert len(coordinate)==1
 selector=next(n for n in coordinate[0].body if isinstance(n,ast.If) and ast.unparse(n.test)=="eff.get('hits_parts')")
 assert ast.unparse(selector.body[0])=="hit = [g for g in geom.targets if g.kind == 'parts']",'Coordinate part-kind selection changed'
 assert any(isinstance(n,ast.Assign) and ast.unparse(n)=="hit = [g for g in geom.targets if g.shape.contains(ax, ay, grow)]" for n in selector.orelse),'Coordinate distance selection changed'
 aim=ast.parse(text['calculator/aim.py'])
 math_calls=sorted({n.func.attr for n in ast.walk(aim) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and isinstance(n.func.value,ast.Name) and n.func.value.id=='math'})
 gate_path='app/portable_world_roster_input.py';gate_text=overrides.get(gate_path,(root/gate_path).read_text(encoding='utf-8'))
 gate=ast.parse(gate_text)
 coordinate_guards=[n for n in ast.walk(gate) if isinstance(n,ast.If) and ast.unparse(n.test)=="enemy.get('coord') is not None or enemy.get('part_break_interval', 0)"]
 assert len(coordinate_guards)==1 and any(isinstance(n,ast.Raise) for n in coordinate_guards[0].body),'Coordinate GPU admission changed; update port evidence'
 coordinate_port=dict(classification='gpu_port_gap',native_model_available=True,native_selector='_coord_skill_hits',part_inclusive='all live parts; excludes interrupt; independent of shape distance',ordinary_area='live shape.contains at current aim with pierce/explosion radius',native_math_calls=math_calls,native_pow_operator=any(isinstance(n,ast.BinOp) and isinstance(n.op,ast.Pow) for n in ast.walk(aim)),cpu_contract_suite='coordinate-skill',gpu_connected=False,gpu_rejection_guard_verified=True)
 result=dict(passed=True,missing_stats=missing,coordinate_world=coordinate_port,target_and_nearby=dict(explicit_ranked_branch=False,fallback='current aimed logical enemy only',nearby_spatial_world=False),enemy_ammo=dict(allied_filter=True,enemy_ammunition_state=False,named_completion_outside_target_loop=True),enemy_healing=dict(allied_heal_consumer_present='heal_received_pct' in strings['calculator/buff_manager.py'],enemy_healing_path_verified=False),historical_documents_are_not_current_instructions=True,gpu_supported=False,full_goal_complete=False,source_sha256={**{base+name:hashlib.sha256(value.encode()).hexdigest() for name,value in text.items()},gate_path:hashlib.sha256(gate_text.encode()).hexdigest()})
 return result
