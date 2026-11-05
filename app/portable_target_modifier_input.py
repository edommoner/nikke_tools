"""One lossless lowering for the declared target-specific modifier carriers."""
import copy
from destructible_damage_policy import modifier_axis
from portable_specs import LIMITS as L,FIELDS as F

def lower_effect(effect):
    result=copy.deepcopy(effect)
    if modifier_axis(effect):result['stat']='atk_dmg_pct'
    return result

def pack_axes(words,metadata,effects):
    """Keep the axis separate from ordinary numeric stats; never edit effects."""
    axes=[0]*L['DEFINITIONS']
    for row,index in enumerate(metadata['binding_source_indices']):
        if index>=len(effects):
            if row not in metadata.get('boss_debuffs',{}).get('definitions',()) or words[L['DEFINITION_BASE']+row*L['DEFINITION_WORDS']+F['OWNER']]!=5:
                raise ValueError('Unowned appended target modifier definition')
            # Boss effects remain ordinary numeric/status carriers, never a
            # projectile/shield contribution of the attacking squad.
            continue
        axis=modifier_axis(effects[index]);axes[row]=axis
        if axis:
            at=L['DEFINITION_BASE']+row*L['DEFINITION_WORDS']
            if words[at+F['KIND']]!=0:raise ValueError('Target modifier must lower from a numeric carrier')
            words[at+F['KIND']]=4;words[at+F['STAT']]=0
    return axes
