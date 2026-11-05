"""Independent reference: call the installed native landing-heal routine.

No formula copy and no CPU-produced GPU state. Admission stays closed until
normal, skill and queued landing phases are connected and verified together.
"""
import types

def native_lifesteal():
    from calculator import timeline
    found=[c for c in timeline.simulate.__code__.co_consts if isinstance(c,types.CodeType) and c.co_name=='_apply_lifesteal']
    if len(found)!=1 or found[0].co_freevars:raise ValueError('Native lifesteal extraction changed')
    return types.FunctionType(found[0],timeline.simulate.__globals__)

MODEL_WARNING='吸血の回復元は攻撃した本人として計算します。味方が付与した吸血を他者からの回復とみなすかは実機未検証です。'
