"""Pinned native producers; never reinterpret a buff carrier as an instant op."""
import ast,hashlib
from pathlib import Path
from portable_skill_weapon_contract import verify as verify_weapon_reader

def verify(root):
    root=Path(root);weapon=verify_weapon_reader(root);timeline=root/'research/upstream/nikke-calc-master/calculator/timeline.py';bm=root/'research/upstream/nikke-calc-master/calculator/buff_manager.py'
    tree=ast.parse(timeline.read_text());handler=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='_handle_damage_eff')
    notify=[n for n in ast.walk(handler) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='notify' and n.args and isinstance(n.args[0],ast.JoinedStr) and any(isinstance(v,ast.Constant) and v.value=='weapon_hit:' for v in n.args[0].values)]
    assert len(notify)==1 and any(isinstance(n,ast.Expr) and n.value is notify[0] for n in ast.walk(handler))
    btree=ast.parse(bm.read_text());functions={n.name:n for n in ast.walk(btree) if isinstance(n,ast.FunctionDef) and n.name in ('_activate','_dispatch_instant')};assert set(functions)=={'_activate','_dispatch_instant'}
    literals=lambda n:{v.value for v in ast.walk(n) if isinstance(v,ast.Constant) and isinstance(v.value,str)}
    assert 'buff_stack_add' in literals(functions['_dispatch_instant']) and 'buff_stack_add' not in literals(functions['_activate'])
    return dict(verified=True,handler_sha256=weapon['handler_source_sha256'],weapon_hit_producers=1,weapon_hit_is_handler_completion_not_per_packet=True,effect_local_weapon_override=False,buff_kind_uses_regular_activation=True,instant_kind_uses_stack_mutation=True,source_sha256={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (timeline,bm)},gpu_calls=0)
