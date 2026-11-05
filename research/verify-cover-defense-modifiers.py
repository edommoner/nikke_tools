"""Additional branches use the same complete battle adapter and shared GPU entry."""
import importlib.util
from pathlib import Path
from unittest.mock import patch
s=importlib.util.spec_from_file_location('cover_modifier_common_adapter',Path(__file__).with_name('verify-cover-defense-battle.py'));base=importlib.util.module_from_spec(s);s.loader.exec_module(base)
from portable_cover_defense_modifier_cases import fixtures
from portable_cover_defense_modifier_contracts import verify
SOURCE=base.SOURCE;suite=base.suite;cross=base.cross
STRICT_WIRE_DIMENSIONS=True;NATIVE_COMPARISON_CONTEXT=base.NATIVE_COMPARISON_CONTEXT

def cohort():
    from portable_cover_defense_battle_cases import fixtures as retained
    return retained()+fixtures()

def prepare():
    with patch.object(base,'fixtures',cohort):return base.prepare()
_reference=base.native_reference

def native_reference(domain):
    import world_original_support_native as support
    case=domain[0]
    if case['cover_defense_case']['contract']['scenario']!='noah-modifiers':return _reference(domain)
    row=case['cover_defense_case']['contract']['noah_source_row']
    assert case['owners'][row]==1 and case['effects'][row]['trigger']['condition']==['prob:10']
    with patch.object(support,'selected',lambda c:[row]):
        with support.capture(case) as receipts:
            def checked(raw,native):
                native['received_conditions']=receipts
                return verify(raw,native)
            with patch.object(base,'verify',checked):return _reference(domain)

def compare(block,domain):
    with patch.object(base,'native_reference',native_reference):native=base.compare(block,domain)
    if 'received_conditions' not in native:return native
    from portable_runtime import decode
    row=domain[0]['cover_defense_case']['contract']['noah_source_row']
    count=len(native['received_conditions']['activations'])
    binding=domain[1]['binding_source_indices'].index(row)
    assert decode(block[:159744],domain[1])['timers'][binding]['activations']==count,'Actual original Noah probability activations'
    return native
validate_rejection=base.validate_rejection
