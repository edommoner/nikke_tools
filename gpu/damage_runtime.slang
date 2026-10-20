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
uint64_t damageValue(inout Runtime s, uint who, uint64_t coefficient, uint64_t when,
    bool normal, uint64_t coreBonus, uint flags = 0, uint64_t fullChargeMult = ONE,
    bool optimal = false)
{
    uint64_t b[64]; collectStats(s,who,when,b);
    uint64_t enemyModifiers[3]; collectEnemyModifiers(s,who,s.target,when,enemyModifiers);
    b[S_enemy_def_down_pct] = f64Add(b[S_enemy_def_down_pct],enemyModifiers[0]);
    b[S_enemy_def_down_flat] = f64Add(b[S_enemy_def_down_flat],enemyModifiers[1]);
    b[S_received_dmg_pct] = f64Add(b[S_received_dmg_pct],enemyModifiers[2]);
    uint64_t f1 = f64Mul(coefficient,normal ? f64Add(ONE,f64Div(b[S_normal_atk_dmg_pct],HUNDRED)) : ONE);
    uint64_t defense = s.combat != 0 ? s.targetDefense[s.target] : s.defense;
    defense = (flags & H_ARMOR) != 0 ? 0 : f64Mul(larger(0,f64Add(f64Mul(defense,f64Add(ONE,f64Div(b[S_enemy_def_down_pct],HUNDRED))),b[S_enemy_def_down_flat])),f64Add(ONE,f64Div(b[S_def_ignore_pct],HUNDRED) ^ F64_SIGN));
    uint64_t attack = f64Add(f64Mul(s.baseAttack[who],f64Add(ONE,f64Div(b[S_atk_pct],HUNDRED))),b[S_atk_flat]);
    uint64_t f2 = larger(0,f64Add(attack,defense ^ F64_SIGN));
    uint64_t critRate = b[normal ? S_crit_rate : S_crit_rate_skill], critDamage = b[normal ? S_crit_dmg : S_crit_dmg_skill];
    uint64_t f3 = f64Add(ONE,f64Mul(critRate,larger(0,f64Add(s.baseCritDamage,f64Div(critDamage,HUNDRED)))));
    if (s.phase == 5) f3 = f64Add(f3,uint64_t(0x3fe00000) << 32);
    if(normal && hasRangeGeometry(s)) optimal=geometryRange(s,who,true,b[S_optimal_range_min],b[S_optimal_range_max_pct]);
    if (normal && optimal) f3 = f64Add(f3,uint64_t(0x3fd33333) << 32 | 0x33333333);
    uint64_t core = (flags & H_CORE) != 0 ? ONE : normal ? normalProbability(s,who,b[S_accuracy_pct]) : 0;
    if (!f64Zero(core)) f3 = f64Add(f3,f64Mul(core,f64Add(coreBonus,f64Div(b[S_core_dmg_pct],HUNDRED))));
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
    if ((flags & H_PART) != 0) f5 = f64Add(f5,f64Div(b[S_part_dmg_pct],HUNDRED));
    if ((flags & H_INTERCEPT) != 0) f5 = f64Add(f5,f64Div(b[S_intercept_dmg_pct],HUNDRED));
    uint64_t f6 = f64Add(ONE,f64Div(b[S_received_dmg_pct],HUNDRED));
    if ((flags & H_SPLIT) != 0) f6 = f64Add(f6,f64Div(b[S_split_dmg_pct],HUNDRED));
    uint64_t f7 = elementMatch(s,who) ? f64Add(uint64_t(0x3ff19999) << 32 | 0x9999999a,f64Div(b[S_element_bonus],HUNDRED)) : ONE;
    uint64_t raw = f64Mul(f64Div(f1,HUNDRED),f2);
    raw = f64Mul(raw,f3); raw = f64Mul(raw,f4); raw = f64Mul(raw,f5); raw = f64Mul(raw,f6); raw = f64Mul(raw,f7);
    uint status; uint64_t rounded = f64ToI64(raw,0,status);
    if (status != 0) { s.error = 16; return 0; }
    return larger(ONE,f64FromI64(rounded));
}
