#ifdef PORTABLE_COVER_DEFENSE
        if(d.stat==CDF_STAT && (d.kind!=0||d.enemyBuff!=0||d.healthScaling!=0||d.alliedFlags!=0||d.quantityFlags!=0||!f64Finite(d.value))) { s.error=64;break; }
#endif
        if(d.stat==92U || (d.damageFlags&524288U)!=0)
        {
#ifdef PORTABLE_PROJECTILE_CHAIN
            if(s.combat==0 || commands[input+P_WORLD_FRAME_INPUT_BASE]!=0x57533031U || d.stat==92U && (d.kind!=0 || d.healthScaling!=0 || d.alliedFlags!=0 || d.quantityFlags!=0 || !f64Finite(d.value)) || (d.damageFlags&524288U)!=0 && (d.kind!=3 || d.damagePending==1 || d.name>=P_DEFINITIONS || (d.damageFlags&262144U)!=0)) { s.error=64;break; }
#else
            s.error=64;break;
#endif
        }
        if(d.stat>=81U && d.stat<=83U || d.kind==34)
        {
#ifdef PORTABLE_DAMAGE_ACCUM
            if(!validDamageAccum(s,j,d,protectionPolicy(s,j))) { s.error=64;break; }
#else
            s.error=64;break;
#endif
        }
        if(d.stat==76U || d.stat==77U || d.kind==32)
        {
#ifdef PORTABLE_HEAL_CHARGE
            if(!validHealCharge(s,j,d,protectionPolicy(s,j))) { s.error=64;break; }
#else
            s.error=64;break;
#endif
        }
        if(d.kind==37)
        {
            if(s.combat==0 || d.stat!=0 || d.target!=0 || d.enemyBuff!=0 || d.healthScaling!=0 || d.alliedFlags!=0 || d.quantityFlags!=0 || d.damageFlags!=0 || d.queryResolve!=0 || (d.flags&~3U)!=0 || !f64Finite(d.value) || f64Less(f64FromI64(4096),f64Abs(d.value))) { s.error=64;break; }
            uint recipient=input+P_RECIPIENT_BASE+j*8;
            if(commands[recipient]!=0 || d.owner>=5 || d.recipients!=(1U<<d.owner)) { s.error=64;break; }
        }
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
