"""Source evidence for removed share inputs versus supported split routing."""
import ast,hashlib
from pathlib import Path

def verify(root,overrides=None):
    root=Path(root);overrides=overrides or {};name='research/upstream/nikke-calc-master/calculator/boss_pattern.py';text=overrides.get(name,(root/name).read_text());tree=ast.parse(text)
    for function in ('_target','_summon'):
        f=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==function)
        guards=[n for n in f.body if isinstance(n,ast.If) and ast.unparse(n.test)=="'share' in raw"]
        assert len(guards)==1 and len(guards[0].body)==1 and isinstance(guards[0].body[0],ast.Raise),'Old share rejection changed: '+function
    boss=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='BossScript');route=next(n for n in boss.body if isinstance(n,ast.FunctionDef) and n.name=='route')
    assert '1.0 / len(hit) if ev.split and hit else 1.0' in ast.unparse(route),'Native split routing changed'
    gpu='gpu/world_skill_runtime.slang';body=overrides.get(gpu,(root/gpu).read_text())
    assert '(d.damageFlags&H_SPLIT)!=0&&n>1' in body and 'weighted=f64Mul(r.amount,f64Div(ONE,f64FromI64(n)))' in body and 'rounded=f64ToI64(weighted,0,status)' in body,'Shared split rounding changed'
    return dict(passed=True,obsolete_share=dict(classification='native_reference_exclusion',parser_rejects=True,game_support_claim=False),valid_split_damage=dict(classification='gpu_port_gap',native_model_available=True,shared_weighted_rounding_implemented=True,reference_cli='coordinate-mixed-common'),historical_documents_are_not_instructions=True,gpu_calls=0,native_battle_calls=0,calculation_verified=False,public_gpu_admitted=False,source_sha256={name:hashlib.sha256(text.encode()).hexdigest(),gpu:hashlib.sha256(body.encode()).hexdigest()})
