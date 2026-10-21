// The same GPU admission checks and observer masks, isolated from execution.
// No checks are moved to the CPU or omitted for either backend.
[noinline]
void admitDefinitions(inout Runtime s,uint input)
{
    uint world=input+P_WORLD_META_BASE,codeNames=commands[world+1];
    if(codeNames>P_DEFINITIONS || commands[world]>codeNames) { s.error=64;return; }
    if(commands[world+2]>s.count) { s.error=64;return; }
    uint elementDefinitions=0;
    if(commands[world+3]>1) { s.error=64;return; }
#ifndef PORTABLE_WORLD_ROSTER
    if(commands[world+3]!=0) { s.error=64;return; }
#endif
    for(uint word=4;word<P_WORLD_META_WORDS;word++) if(commands[world+word]!=0) { s.error=64;return; }
    if(commands[input+P_RECIPIENT_META_BASE]>P_RECIPIENT_NODES) { s.error=64;return; }
    for(uint word=1;word<8;word++) if(commands[input+P_RECIPIENT_META_BASE+word]!=0) { s.error=64;return; }
    uint refs=input+P_BURST_REFERENCE_BASE;
    if(commands[refs]>1 || commands[refs+1]>31 || commands[refs]!=0 && s.combat==0) { s.error=64;return; }
    for(uint word=2;word<8;word++) if(commands[refs+word]!=0) { s.error=64;return; }
    for(uint word=28;word<P_BURST_REFERENCE_WORDS;word++) if(commands[refs+word]!=0) { s.error=64;return; }
    if(commands[refs]==0)
    { for(uint word=1;word<P_BURST_REFERENCE_WORDS;word++) if(commands[refs+word]!=0) { s.error=64;return; } }
    else for(uint who=0;who<5;who++)
    {
        uint64_t energy=loadNumber(refs+8+who*4),raw=loadNumber(refs+10+who*4);
        if(!f64Finite(energy) || !f64Finite(raw) || f64Less(energy,0) || f64Less(raw,0) || f64Less(f64FromI64(1000000),energy) || f64Less(f64FromI64(1000000),raw) ||
           (commands[refs+1] & (1U<<who))==0 && !f64Zero(raw)) { s.error=64;return; }
    }
    for (uint j = 0; j < s.count; j++)
    {
        Definition d;loadDefinition(input,j,d); PROJECTILE_ADMIT_ROW(s,j,d)
        if(d.kind==33)
        {
            if(d.stat!=0 || d.enemyBuff!=0 || d.target!=0 || d.damageFlags!=0 || d.healthScaling!=0 || d.quantityFlags!=0) { s.error=64;break; }
            uint forced=input+P_FORCE_BASE+j*P_MASK_WORDS;
            for(uint word=0;word<P_MASK_WORDS;word++)
                for(uint bit=0;bit<32;bit++) if((commands[forced+word]&(1U<<bit))!=0)
                { uint target=word*32+bit;if(target>=s.count || target==j || definition_owner(input,target)!=d.owner) { s.error=64;break; } }
            if(s.error!=0) break;
        }
        if((d.damageFlags&H_NAMED_SKILL)!=0 && (d.kind!=3 || commands[world+3]==0 || d.name>=P_DEFINITIONS)) { s.error=64;break; }
        PROJECTILE_ADMIT_STAGE(s,4000)
        if(d.stat==S_skill_cooldown_pct)
        {
#ifndef PORTABLE_WORLD_ROSTER
            s.error=64;break;
#else
            if(s.combat==0 || d.kind!=0 || d.enemyBuff!=0 || !f64Finite(d.value)) { s.error=64;break; }
            s.quantityMask|=2048;
#endif
        }
        if((d.quantityFlags&1)!=0)
        {
#ifndef PORTABLE_WORLD_PROJECTILE
            s.error=64;break;
#else
            if(d.kind!=4 || s.combat==0 || d.stat!=0 || (d.quantityFlags&~32U)!=1 || d.enemyBuff!=0 ||
               d.alliedFlags!=0 || d.healthScaling!=0 || d.damageFlags!=0 || !f64Finite(d.value)) { s.error=64;break; }
            s.quantityMask|=16384;
#endif
        }
        if(d.kind==22 && (s.combat==0 || d.stat!=0 || d.enemyBuff!=0 || !f64Finite(d.value))) { s.error=64;break; }
        PROJECTILE_ADMIT_STAGE(s,4001) if(d.stat==S_stun)
        { if(d.kind!=0 || s.combat==0 || !f64Equal(d.value,ONE)) { s.error=64;break; }s.incomingMask|=8; }
        PROJECTILE_ADMIT_STAGE(s,4002) if((d.quantityFlags&2)!=0)
        { if(d.kind!=4 || s.combat==0 || d.stat!=0 || d.quantityFlags!=2 || !f64Finite(d.value)) { s.error=64;break; }s.incomingMask|=16; }
        PROJECTILE_ADMIT_STAGE(s,4003) if(d.kind==25)
        {
            uint plan=input+P_RECIPIENT_BASE+j*8;
            if(s.combat==0 || d.stat!=0 || d.enemyBuff!=0 || !f64Finite(d.value) || f64Zero(d.value) ||
               commands[plan]>1 || !validRecipientPlan(plan,false,input)) { s.error=64;break; }
        }
        PROJECTILE_ADMIT_STAGE(s,4004) if(d.stat==S_pierce_enabled || d.stat==S_armor_break_enabled || d.stat==S_burst_charge_speed_pct)
        {
            if(d.kind!=0 || d.enemyBuff!=0 || !f64Finite(d.value) || d.damageFlags!=0) { s.error=64;break; }
            for(uint word=0;word<P_DAMAGE_DEFINITION_WORDS;word++)
                if(commands[input+P_DAMAGE_DEFINITION_BASE+j*P_DAMAGE_DEFINITION_WORDS+word]!=0) { s.error=64;break; }
            if(s.error!=0) break;
            if(d.stat==S_burst_charge_speed_pct)
            { if(commands[refs]!=1) { s.error=64;break; } s.quantityMask|=128; }
        }
        PROJECTILE_ADMIT_STAGE(s,4005) if(d.stat==S_atk_from_hp_pct)
        {
            if(d.kind!=0 || d.enemyBuff!=0 || d.alliedFlags!=0 || d.healthScaling!=0 || d.queryResolve!=0 || !f64Finite(d.value) || d.damageFlags!=0) { s.error=64;break; }
            for(uint word=0;word<P_DAMAGE_DEFINITION_WORDS;word++)
                if(commands[input+P_DAMAGE_DEFINITION_BASE+j*P_DAMAGE_DEFINITION_WORDS+word]!=0) { s.error=64;break; }
            if(s.error!=0) break;
            s.quantityMask|=256;
        }
        uint entry=s.inputBase+P_MODE_BASE+j*P_MODE_WORDS+28;
        PROJECTILE_ADMIT_STAGE(s,401)
        uint64_t entryDelay=loadNumber(entry);
        if(d.kind==2)
        {
            if(s.combat==0 || !f64Finite(entryDelay) || f64Less(entryDelay,0) || f64Less(f64FromI64(180),entryDelay) || (commands[entry+2]>1 || commands[entry+2]==0 && !f64Zero(entryDelay)) || WORLD_MODE_POLICY_INVALID(s,commands[entry+3])) { s.error=64;break; }
            if(commands[entry+2]!=0) s.quantityMask|=512;
        }
        else if(commands[entry]!=0 || commands[entry+1]!=0 || commands[entry+2]!=0 || commands[entry+3]!=0) { s.error=64;break; }
        if (d.owner >= 5 || d.triggerCount == 0 || d.triggerCount > P_TRIGGERS || d.conditionCount > P_CONDITIONS) { s.error = 64; break; }
        PROJECTILE_ADMIT_STAGE(s,402)
        for(uint slot=0;slot<d.conditionCount;slot++)
        {
            uint at=input+P_CONDITION_BASE+j*P_CONDITION_WORDS+slot*4;
            if(commands[at]==C_TRIGGER_HIT_CRIT)
            {
                if(s.combat==0 || commands[world+3]!=1 || commands[input+P_LANDING_META_BASE]!=1 || commands[at+1]!=0 || !f64Zero(loadNumber(at+2))) { s.error=64;break; }
                s.incomingMask|=32;
            }
            if((commands[at]==C_TARGET_STUNNED || commands[at]==C_SELF_STUN_IMMUNE) &&
               (s.combat==0 || commands[at+1]!=0 || !f64Zero(loadNumber(at+2)))) { s.error=64;break; }
            if(commands[at]==C_TARGET_STATE || commands[at]==C_NOT_TARGET_STATE || commands[at]==C_TARGET_STACK)
            {
                uint64_t arg=loadNumber(at+2);uint conversionStatus;
                uint64_t integer=f64ToI64(arg,1,conversionStatus);
                if(commands[at+1]>=P_DEFINITIONS || !f64Finite(arg) ||
                   commands[at]!=C_TARGET_STACK && !f64Zero(arg) ||
                   commands[at]==C_TARGET_STACK && (conversionStatus!=0 || f64Less(arg,0) || f64Less(f64FromI64(2147483647),arg) || !f64Equal(arg,f64FromI64(integer)))) { s.error=64;break; }
            }
            if((commands[at]==C_CORE || commands[at]==C_OPTIMAL_RANGE) && (!hasRangeGeometry(s) || commands[at+1]!=0 || !f64Zero(loadNumber(at+2)))) { s.error=64;break; }
            if(commands[at]==C_PROB && (commands[at+1]!=0 || !f64Finite(loadNumber(at+2)) || f64Less(loadNumber(at+2),0) || f64Less(ONE,loadNumber(at+2)))) { s.error=64;break; }
            if(commands[at]==22) { s.error=64;break; } // Legacy CPU-folded code predicate is not a portable condition.
            if(commands[at]==C_TARGET_CODE && (commands[at+1]==0 || commands[at+1]>codeNames || !f64Zero(loadNumber(at+2)))) { s.error=64;break; }
        }
        if(s.error!=0) break;
        WORLD_TEAM_VALIDATE(s,d,input,j) WORLD_FRACTION_VALIDATE(s,d,input,j) WORLD_INITIAL_SPAWN_VALIDATE(s,d,input,j) for (uint slot = 0; slot < d.triggerCount; slot++)
            if (commands[input+P_EVENT_BASE+j*P_EVENT_WORDS+slot*8] == 31) s.namedEventOwners |= 1U << d.owner;
        for (uint slot = 0; slot < d.triggerCount; slot++)
            if (commands[input+P_EVENT_BASE+j*P_EVENT_WORDS+slot*8] == 9) s.stackEventOwners |= 1U << d.owner;
        if ((d.kind == 2 || d.kind == 13 || d.kind == 14) && (d.target > 1 || !f64Finite(d.value))) { s.error = 64; break; }
        PROJECTILE_ADMIT_STAGE(s,403)
         s.lazyEnabled |= uint(d.lazyGroup != 0);
        if ((WORLD_RELOAD_FORCE_KIND(d.kind) || d.kind == 0 || d.kind == 4 || d.kind == 5 || d.kind == 6 || d.kind == 7 || d.kind == 8 || d.kind == 13 || d.kind == 14 || d.kind == 22 || d.kind == 24 || d.kind == 27 || d.kind == 31 || d.kind == 30) && !validRecipientPlan(input+P_RECIPIENT_BASE+j*8,d.enemyBuff != 0,input)) { s.error = 64; break; }
        if (d.lazyGroup != 0)
        {
            uint plan = input+P_RECIPIENT_BASE+j*8, selector = commands[plan];
            if (d.lazyGroup > s.count || d.kind != 0 && d.kind != 4 || !(selector == 5 || selector == 6 || selector == 7 || selector == 15 || selector == 16)) { s.error = 64; break; }
            uint previous = s.lazyGroupDefinition[d.lazyGroup-1];
            if (previous != 0)
            {
                uint prior = input+P_RECIPIENT_BASE+(previous-1)*8;
                bool same = definition_owner(s.inputBase,previous-1) == d.owner;
                for (uint field = 0; field < 4; field++) if (commands[prior+field] != commands[plan+field]) same = false;
                if (!same) { s.error = 64; break; }
            }
            else s.lazyGroupDefinition[d.lazyGroup-1] = j+1;
        }
        if((d.stat==S_optimal_range_min || d.stat==S_optimal_range_max_pct) && (d.kind!=0 || d.enemyBuff!=0 || !hasRangeGeometry(s))) { s.error=64;break; }
        uint packet = input+P_DAMAGE_DEFINITION_BASE+j*P_DAMAGE_DEFINITION_WORDS;
        PROJECTILE_ADMIT_STAGE(s,404)
        if(d.stat==S_element_code_override)
        {
            elementDefinitions++;
            if(d.kind!=0 || d.enemyBuff!=0 || d.damageRoute>codeNames || d.damageFlags!=0 || !f64Zero(d.value)) { s.error=64;break; }
            for(uint word=1;word<P_DAMAGE_DEFINITION_WORDS;word++) if(commands[packet+word]!=0) { s.error=64;break; }
            if(s.error!=0) break;
        }
        uint periodic = input+P_PERIODIC_DEFINITION_BASE+j*2;
        if (d.enemyBuff != 0 && (d.enemyBuff != 1 || !(d.kind==0 || d.kind==4 && (d.flags&56)!=0 || d.kind==4 && d.stat==0 || d.kind==19) || s.combat == 0 || d.lazyGroup != 0 ||
            !WORLD_ENEMY_ATTACK_STAT(s,d,(d.stat == S_enemy_def_down_pct || d.stat == S_def_caster_based_pct || d.stat == S_received_dmg_pct || namedMagnitudeStat(d.stat) || d.stat == S_taunt || d.stat == S_stun || d.kind==4 && (d.flags&56)!=0 || d.kind==4 && d.stat==0 || d.kind==19)) ||
            d.damageRoute > 9 || d.damageCount == 0 || d.damageCount > 256 || d.damageHits != 0 || d.damageNormal != 0 || !f64Zero(d.damageGauge) || d.damagePending != 0 || d.pendingHits != 0 ||
            commands[input+P_RECIPIENT_BASE+j*8] != 4)) { s.error = 64; break; }
        if (d.kind == 3 && (d.damageRoute > 9 || d.damageCount == 0 || d.damageCount > 256 || d.damageHits > 256 ||
            d.damageRoute >= 2 && s.combat == 0 || !f64Finite(d.damageGauge) || f64Less(d.damageGauge,0) && !f64Equal(d.damageGauge,F64_SIGN | ONE) || f64Less(f64FromI64(1000000),d.damageGauge) ||
            d.damageNormal > 1 || d.damagePending > 1 || d.damagePending == 0 && d.pendingHits != 0 || d.damagePending != 0 && (s.combat == 0 || d.damageHits != 1 || d.damageFlags != 0 || d.damageNormal != 0 || d.pendingHits == 0 || d.pendingHits > 256))) { s.error = 64; break; }
        if ((d.kind == 3 || d.enemyBuff != 0 || (d.kind == 1 || d.kind == 15) && d.target == 2) && (d.damageRoute == 7 || d.damageRoute == 8))
            for (uint target = 1; target < s.targetCount; target++) if (!f64Zero(s.targetDefense[target])) { s.error = 64; break; }
        if(!validDurationExtension(input,s.count,s.combat,j)) { s.error=64;break; }
        if(!validRemovalDefinition(input,s.combat,j)) { s.error=64;break; }
        PROJECTILE_ADMIT_STAGE(s,405)
        uint bullet = input+P_BULLET_DEFINITION_BASE+j*2;
        if (d.bulletDuration > 0x7fffffff || d.bulletBound > 1 || d.bulletDuration == 0 && d.bulletBound != 0 || d.bulletDuration != 0 && (s.combat == 0 || d.kind != 0 && d.kind != 4)) { s.error = 64; break; }
        uint extra = input+P_DEFINITION_EXTRA_BASE+j*P_DEFINITION_EXTRA_WORDS;
        uint health = input+P_HEALTH_DEFINITION_BASE+j*P_HEALTH_DEFINITION_WORDS;
        uint duration = input+P_DURATION_DEFINITION_BASE+j*2;
        if (d.kind == 0 && d.stat == S_fullburst_duration)
        {
            if (s.combat == 0 || d.durationGroup == 0 || d.durationGroup > s.count || d.durationCast > 1) { s.error = 64; break; }
            bool cast = false;
            for (uint slot = 0; slot < d.triggerCount; slot++) if (commands[input+P_EVENT_BASE+j*P_EVENT_WORDS+slot*8] == 3 && commands[input+P_EVENT_BASE+j*P_EVENT_WORDS+slot*8+3] == 0) cast = true;
            if (d.durationCast != uint(cast)) { s.error = 64; break; }
            s.durationEnabled = 1;
        }
        else if (d.durationGroup != 0 || d.durationCast != 0) { s.error = 64; break; }
        // Low bits retain the named-event/audience policy. Higher bits hold an
        // optional stat-applied event name plus one, authored by the compiler.
        uint statNotice = d.buffEvent >> 2;
        if (d.enemyBuff > 1 || d.kind != 0 && d.kind != 4 && d.buffEvent != 0 ||
            statNotice > P_DEFINITIONS || statNotice != 0 && (d.kind != 0 || d.stat != S_dot_dmg_pct && d.stat != S_split_dmg_pct)) { s.error = 64; break; }
        if (d.healthScaling > 1) { s.error = 64; break; }
        PROJECTILE_ADMIT_STAGE(s,406)
        if (d.kind == 0 && d.stat == S_cover_hp_pct) s.coverMask |= 1;
        if ((d.kind == 7 || d.kind == 30) && (f64Less(d.value,0) || d.kind == 30 && f64Zero(d.value))) { s.error = 64; break; }
        if (d.kind == 7 || d.kind == 30) s.coverMask |= 2;
        if (d.kind == 0 && (d.stat >= S_max_hp_pct && d.stat <= S_max_hp_only_pct || d.stat == S_max_hp_from_max_hp_pct)) s.healthMask |= 1;
        if (d.kind == 0 && d.enemyBuff == 0 && ((d.alliedFlags & 1) != 0 || d.stat == S_def_caster_based_pct)) s.healthMask |= 2;
        if (d.kind == 0 && d.stat == S_heal_received_pct) s.healthMask |= 4;
        if (d.kind == 0 && d.stat == S_outgoing_heal_pct) s.healthMask |= 8;
        if (d.kind == 0 && d.stat == S_lifesteal_pct) s.healthMask |= 64;
        if (d.kind == 6 || d.kind == 8) s.healthMask |= 16;
        if (d.group >= s.count || d.alias >= int(j)) { s.error = 64; break; }
        PROJECTILE_ADMIT_STAGE(s,407)
        if (d.kind == 0 && d.stat == S_invincible) s.incomingMask |= 1;
        if (d.kind == 0 && d.stat == S_undying) s.incomingMask |= 2;
        if (d.kind == 0 && d.stat == S_received_dmg_pct) s.incomingMask |= 4;
        if ((d.kind == 13 || d.kind == 14 || d.kind == 5 || d.kind == 24 || d.kind == 0 && d.stat == S_burst_cooldown) && s.combat == 0) { s.error = 64; break; }
        if (d.kind == 0 && d.stat == S_burst_cooldown) s.burstModifierMask |= 1;
        if (d.kind == 0 && d.stat == S_reload_speed_pct) s.quantityMask |= 64;
        if (d.kind == 0 && d.stat == S_max_ammo_flat) s.quantityMask |= 16;
        if (d.kind == 0 && d.stat == S_charge_time_flat) s.quantityMask |= 32;
        if (d.kind == 0 && d.stat == S_max_ammo_pct) s.quantityMask |= 1;
        if (d.kind == 0 && (d.stat == S_charge_speed_pct || d.stat == S_charge_speed_caster_based_pct)) s.quantityMask |= 2;
        if ((d.quantityFlags & 64) != 0) s.quantityMask |= 4;
        if (d.kind == 0 && d.stat == S_charge_time_fixed) s.quantityMask |= 8;
    }
    if(s.error==0 && (elementDefinitions!=commands[world+2] || uint((s.incomingMask&32)!=0)!=commands[world+3])) s.error=64;
}
