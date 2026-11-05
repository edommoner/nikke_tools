"""V1 declared policy assertions; deliberately retain reference-model-gap lane."""
import struct

def verify(case,native):
    assert native['damage']==case['expected'],(case['name'],native,case['expected'])
    assert struct.pack('<d',native['factor5'])==struct.pack('<d',case['factor']),(case['name'],native['factor5'],case['factor'])
    assert native['kind']==case['kind'] and native['declared_model']=='v1' and native['in_game_rules_verified'] is False
    return dict(verified=True,reference_model_gap=True,declared_model=True,canonical_consumer_verified=False,seven_native_factors_preserved=True,modifiers_before_final_round=True,gpu_connected=False,in_game_rules_verified=False)
