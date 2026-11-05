"""Pin the reviewed native handler; metadata acceptance must not hide an override."""
import ast,hashlib
from pathlib import Path
HANDLER_SHA256='9966c24a71c080dde253d5531c3578a6f3a16260430dc608e2f237b5e57d1941'

def verify(root,source=None):
    path=Path(root)/'research/upstream/nikke-calc-master/calculator/timeline.py'
    text=path.read_text() if source is None else source
    handlers=[n for n in ast.walk(ast.parse(text)) if isinstance(n,ast.FunctionDef) and n.name=='_handle_damage_eff']
    if len(handlers)!=1:raise ValueError('Native skill damage handler missing or ambiguous')
    h=hashlib.sha256(ast.get_source_segment(text,handlers[0]).encode()).hexdigest()
    if h!=HANDLER_SHA256:raise ValueError('Native skill weapon contract requires review after handler changes')
    readers=[]
    for n in ast.walk(handlers[0]):
        if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='get' and n.args and isinstance(n.args[0],ast.Constant) and n.args[0].value=='weapon_type':readers.append(ast.unparse(n.func.value))
        if isinstance(n,ast.Subscript) and isinstance(n.slice,ast.Constant) and n.slice.value=='weapon_type':readers.append(ast.unparse(n.value))
    if readers!=['cs.weapon']:raise ValueError('Native skill weapon reader changed')
    return dict(verified=True,handler_source_sha256=h,source_sha256=hashlib.sha256(text.encode()).hexdigest(),weapon_type_readers=readers,effect_local_weapon_override=False,gpu_calls=0,scope='Pinned native handler and observed fixtures; no in-game override semantics established')
