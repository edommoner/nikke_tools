"""Check that existing runtime operations are wired to one adapter and GPU hooks."""
import dataclasses,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
import engine_worker
from effect_runtime import CATALOG
from lifecycle_specs import gpu_source_matches
from reference_rewrite import referenced_names
from calculator.buff_manager import BuffManager

assert CATALOG.sealed and gpu_source_matches()
assert all(Path(getattr(BuffManager,name).__code__.co_filename).resolve()==ROOT/'app/effect_runtime.py'
           for name in ('notify','_dispatch_instant','knock_down'))
assert '_apply_enemy_carrier' in referenced_names(BuffManager._activate)
names=referenced_names(BuffManager._activate)|referenced_names(BuffManager._apply_enemy_carrier)
assert 'effect_runtime_activate' in names and 'effect_runtime_protection' in names
assert 'effect_runtime_prepare' in names
assert 'effect_runtime_carrier' in names
assert all(spec.current_instance for spec in CATALOG.specs if spec.gpu_activate)
assert 'effect_runtime_prepare' in BuffManager._dispatch_instant.__wrapped__.__code__.co_names
assert 'shield_per_target' not in names and 'decoy_per_target' not in names
rows=[]
for spec in CATALOG.specs:
    handler=CATALOG.handlers[spec.key]
    rows.append({'operation':dataclasses.asdict(spec),'callbacks':{
        field.name:getattr(handler,field.name).__module__+'.'+getattr(handler,field.name).__qualname__
        for field in dataclasses.fields(handler) if callable(getattr(handler,field.name))},
        'resource_kind':handler.resource_kind})
report={'passed':True,'catalog_sealed':True,'generated_gpu_hooks_match':True,'single_event_adapter':True,
        'legacy_inline_protection_removed':True,'operations':rows,'game_rules_verified':False,
        'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
                         for p in (ROOT/'app').glob('*.py')}}
(ROOT/'research/runtime-wiring.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'passed':True,'operations':len(rows)}))
