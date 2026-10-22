#include "damage_factors.slang"
#include "skill_hp_basis_runtime.slang"

// Re-evaluate geometry at impact; cache only the exact normalized ratio.
// The cache is per actor and shared by both backends, never CPU-produced.
uint64_t normalProbability(inout Runtime s, uint who, uint64_t accuracy)
{
    if (s.combat == 0 || s.geometry[who] == 0) return s.probability;
    uint64_t spread = s.spreadStart[who];
    if (!f64Zero(s.spreadShots[who]))
    {
        uint64_t progress = f64Div(smaller(s.warm[who],s.spreadShots[who]),s.spreadShots[who]);
        spread = f64Add(spread,f64Mul(f64Add(s.spreadEnd[who],spread ^ F64_SIGN),progress));
    }
    uint64_t slope = uint64_t(0x3f829888) << 32 | 0xf861a60d; // binary64 .00908
    spread = larger(ONE,f64Mul(spread,f64Add(ONE,f64Mul(slope,accuracy) ^ F64_SIGN)));
    s.lastSpread[who] = spread;
    uint64_t ratio = f64Div(s.coreDiameter[who],spread);
    if (s.probabilityValid[who] == 0 || !f64Equal(ratio,s.probabilityRatio[who]))
    {
        uint status; uint64_t probability = coreProbability(ratio,status);
        if (status != 0) { s.error = 128; return 0; }
        if (s.probabilityEvaluations[who] == 0x7fffffff) { s.error = 2; return 0; }
        s.probabilityEvaluations[who]++; s.probabilityValid[who] = 1;
        s.probabilityRatio[who] = ratio; s.lastProbability[who] = probability;
    }
    return s.lastProbability[who];
}

// Seven-factor scalar damage, shared by CUDA and Metal. All intermediate
// arithmetic is software binary64 and follows the authored reference order.
[noinline]
void sampleDamageFactorsForReach(inout Runtime s, uint who, uint64_t coefficient, uint64_t when,
    out uint64_t factors[9], out uint64_t interceptFactor, out uint64_t explosionRange, out uint64_t pierceRange, out uint sampledFlags, bool captureReach,
    bool normal, uint64_t coreBonus, uint flags = 0, uint64_t fullChargeMult = ONE,
    bool optimal = false, bool physical = false, uint basisRow = P_DEFINITIONS)
{
    uint64_t b[64]; collectStats(s,who,when,b);
    // Physical weapon flags also apply to weapon-mode skill packets. A skill
    // labelled normal/auto_damage still derives its flags from its own family.
    if(physical)
    {
        if(!f64Zero(b[S_pierce_enabled])) flags|=H_PIERCE;
        if(!f64Zero(b[S_armor_break_enabled])) flags|=H_ARMOR;
    }
    sampledFlags=flags;
    explosionRange=0;pierceRange=0;
    if(captureReach)
    {
        if((flags&H_EXPLOSION)!=0) explosionRange=plainQuantity(s,who,S_explosion_range,when);
        else if((flags&H_PIERCE)!=0) pierceRange=plainQuantity(s,who,S_pierce_range,when);
    }
    uint64_t enemyModifiers[3]; collectEnemyModifiers(s,who,s.target,when,enemyModifiers);
    b[S_enemy_def_down_pct] = f64Add(b[S_enemy_def_down_pct],enemyModifiers[0]);
    b[S_enemy_def_down_flat] = f64Add(b[S_enemy_def_down_flat],enemyModifiers[1]);
    b[S_received_dmg_pct] = f64Add(b[S_received_dmg_pct],enemyModifiers[2]);
    uint64_t f1 = f64Mul(coefficient,normal ? f64Add(ONE,f64Div(b[S_normal_atk_dmg_pct],HUNDRED)) : ONE);
    uint64_t defense = s.combat != 0 ? s.targetDefense[s.target] : s.defense;
    defense = (flags & H_ARMOR) != 0 ? 0 : f64Mul(larger(0,f64Add(f64Mul(defense,f64Add(ONE,f64Div(b[S_enemy_def_down_pct],HUNDRED))),b[S_enemy_def_down_flat])),f64Add(ONE,f64Div(b[S_def_ignore_pct],HUNDRED) ^ F64_SIGN));
    uint64_t attack = skillAttackBasis(s,who,basisRow,when,b[S_atk_pct],b[S_atk_flat]);
    uint64_t f2 = larger(0,f64Add(attack,defense ^ F64_SIGN));
    uint64_t critRate = b[normal ? S_crit_rate : S_crit_rate_skill], critDamage = b[normal ? S_crit_dmg : S_crit_dmg_skill];
    if((s.incomingMask&32)!=0) s.lastDamageCritRate=critRate;
    uint64_t f3 = f64Add(ONE,f64Mul(critRate,larger(0,f64Add(s.baseCritDamage,f64Div(critDamage,HUNDRED)))));
    if (s.phase == 5) f3 = f64Add(f3,uint64_t(0x3fe00000) << 32);
    if(normal && hasRangeGeometry(s)) optimal=geometryRange(s,who,true,b[S_optimal_range_min],b[S_optimal_range_max_pct]);
    if (normal && optimal) f3 = f64Add(f3,uint64_t(0x3fd33333) << 32 | 0x33333333);
    factors[7] = f3; // Part receipts retain this shot's critical/range basis, without core.
    uint64_t core = COUNTER_PART_CORE(s,flags,(flags & H_CORE) != 0 ? ONE : normal ? normalProbability(s,who,b[S_accuracy_pct]) : WORLD_MODE_CORE(s,who,flags,b[S_accuracy_pct]));
    WORLD_FRACTION_SAMPLE(s,who,critRate,core,physical,flags) if (!f64Zero(core)) f3 = f64Add(f3,f64Mul(core,f64Add(coreBonus,f64Div(b[S_core_dmg_pct],HUNDRED))));
    uint64_t f4 = (flags & H_CHARGE) != 0 ? f64Add(f64Mul(fullChargeMult,f64Add(ONE,f64Div(b[S_charge_dmg_mag_pct],HUNDRED))),f64Div(b[S_charge_dmg_pct],HUNDRED)) : ONE;
    uint64_t f5 = f64Add(ONE,f64Div(b[S_atk_dmg_pct],HUNDRED));
    if ((flags & H_BURST) != 0)
    {
        f5 = f64Add(f5,f64Div(b[S_burst_dmg_pct],HUNDRED));
        if ((flags & H_AOE_BURST) != 0) f5 = f64Add(f5,f64Div(b[S_burst_dmg_aoe_pct],HUNDRED));
        if ((flags & H_SINGLE_BURST) != 0) f5 = f64Add(f5,f64Div(b[S_burst_dmg_single_pct],HUNDRED));
    }
    if ((flags & H_PIERCE) != 0) f5 = f64Add(f5,f64Div(b[S_pierce_dmg_pct],HUNDRED));
    if ((flags & H_ARMOR) != 0) f5 = f64Add(f5,f64Div(b[S_armor_break_dmg_pct],HUNDRED));
    if ((flags & H_DOT) != 0) f5 = f64Add(f5,f64Div(b[S_dot_dmg_pct],HUNDRED));
    if ((flags & H_EXPLOSION) != 0) f5 = f64Add(f5,f64Div(b[S_projectile_explosion_dmg_pct],HUNDRED));
    if ((flags & H_ATTACHMENT) != 0) f5 = f64Add(f5,f64Div(b[S_projectile_attachment_dmg_pct],HUNDRED));
    if ((flags & H_SEQUENTIAL) != 0) f5 = f64Add(f5,f64Div(b[S_sequential_dmg_pct],HUNDRED));
    interceptFactor=f64Add(f5,f64Div(b[S_intercept_dmg_pct],HUNDRED));
    factors[8] = f64Add(f5,f64Div(b[S_part_dmg_pct],HUNDRED));
    if ((flags & H_PART) != 0) f5 = f64Add(f5,f64Div(b[S_part_dmg_pct],HUNDRED));
    if ((flags & H_INTERCEPT) != 0) f5 = f64Add(f5,f64Div(b[S_intercept_dmg_pct],HUNDRED));
    uint64_t f6 = f64Add(ONE,f64Div(b[S_received_dmg_pct],HUNDRED));
    if ((flags & H_SPLIT) != 0) f6 = f64Add(f6,f64Div(b[S_split_dmg_pct],HUNDRED));
    uint64_t f7 = elementMatch(s,who) ? f64Add(uint64_t(0x3ff19999) << 32 | 0x9999999a,f64Div(b[S_element_bonus],HUNDRED)) : ONE;
    factors[0]=f1; factors[1]=f2; factors[2]=f3; factors[3]=f4;
    factors[4]=f5; factors[5]=f6; factors[6]=f7;
}

void sampleDamageFactors(inout Runtime s, uint who, uint64_t coefficient, uint64_t when,
    out uint64_t factors[9], bool normal, uint64_t coreBonus, uint flags=0,
    uint64_t fullChargeMult=ONE,bool optimal=false,bool physical=false,uint basisRow=P_DEFINITIONS)
{
    uint64_t interceptFactor,explosionRange,pierceRange;uint sampledFlags;
    sampleDamageFactorsForReach(s,who,coefficient,when,factors,interceptFactor,explosionRange,pierceRange,sampledFlags,false,normal,coreBonus,flags,fullChargeMult,optimal,physical,basisRow);
}

// Keep the reference's divide, seven ordered products and integer boundary.
// A part packet uses the captured no-core and part-only additive factors;
// no stats query, RNG/fraction sampling or reverse ratio is performed here.
uint64_t damageFromFactors(inout Runtime s, uint64_t factors[9], bool part)
{
    uint64_t raw = damageFactorProduct(factors,part);
    uint status; uint64_t rounded = f64ToI64(raw,0,status);
    if (status != 0) { s.error = 16; return 0; }
    return larger(ONE,f64FromI64(rounded));
}

[noinline]
uint64_t damageValue(inout Runtime s, uint who, uint64_t coefficient, uint64_t when,
    bool normal, uint64_t coreBonus, uint flags = 0, uint64_t fullChargeMult = ONE,
    bool optimal = false, bool physical = false, uint basisRow = P_DEFINITIONS)
{
    uint64_t factors[9];
    sampleDamageFactors(s,who,coefficient,when,factors,normal,coreBonus,flags,fullChargeMult,optimal,physical,basisRow);
    return damageFromFactors(s,factors,false);
}

// The caller requests a part value only when a reached live part needs it.
// The old single-value path never adds a second rounding/error boundary.
[noinline]
uint64_t damageValueWithPart(inout Runtime s, uint who, uint64_t coefficient, uint64_t when,
    bool normal, uint64_t coreBonus, uint flags, out uint64_t partAmount,
    uint64_t fullChargeMult = ONE, bool optimal = false, bool physical = false, uint basisRow = P_DEFINITIONS)
{
    uint64_t factors[9];
    sampleDamageFactors(s,who,coefficient,when,factors,normal,coreBonus,flags,fullChargeMult,optimal,physical,basisRow);
    uint64_t amount=damageFromFactors(s,factors,false);
    partAmount=s.error==0 ? damageFromFactors(s,factors,true) : 0;
    return amount;
}
