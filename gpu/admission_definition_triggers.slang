        uint entry=s.inputBase+P_MODE_BASE+j*P_MODE_WORDS+28;
        PROJECTILE_ADMIT_STAGE(s,401)
        uint64_t entryDelay=loadNumber(entry);
        if(d.kind==2)
        {
            if(s.combat==0 || !f64Finite(entryDelay) || f64Less(entryDelay,0) || f64Less(f64FromI64(180),entryDelay) || (commands[entry+2]>2 || commands[entry+2]!=1 && !f64Zero(entryDelay)) || WORLD_MODE_POLICY_INVALID(s,commands[entry+3])) { s.error=64;break; }
            if(commands[entry+2]!=0) s.quantityMask|=512;
        }
        else if(commands[entry]!=0 || commands[entry+1]!=0 || commands[entry+2]!=0 || commands[entry+3]!=0) { s.error=64;break; }
        if ((d.owner >= 5 && !validWorldBossDebuff(s,j,d)) || d.triggerCount == 0 || d.triggerCount > P_TRIGGERS || d.conditionCount > P_CONDITIONS) { s.error = 64; break; }
        PROJECTILE_ADMIT_STAGE(s,402)
        for(uint slot=0;slot<d.conditionCount;slot++)
        {
            uint at=input+P_CONDITION_BASE+j*P_CONDITION_WORDS+slot*4;
            if(commands[at]==C_NOT_CORE)
            {
#ifdef PORTABLE_NOT_CORE
                if(s.combat==0 || commands[input+P_WORLD_FRAME_INPUT_BASE]!=0x57533031U || commands[at+1]!=0 || !f64Zero(loadNumber(at+2))) { s.error=64;break; }
                s.incomingMask|=512U;
#else
                s.error=64;break;
#endif
            }
            if((commands[at]==C_FOCUSING || commands[at]==C_NO_BROKEN_COVER_ALLY) && !validStatePredicate(input,j,at,s.combat)) { s.error=64;break; }
            if(commands[at]==C_SELF_UNDYING && !validUndyingPredicate(input,j,at,s.combat)) { s.error=64;break; }
            if(commands[at]==C_STAT_ABOVE && !validStatAbovePredicate(commands[at+1],loadNumber(at+2))) { s.error=64;break; }
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
        {
            uint at=input+P_EVENT_BASE+j*P_EVENT_WORDS+slot*8,event=commands[at];
            if(event==62)
            {
#ifndef PORTABLE_ATTACK_GROUPS
                s.error=64;break;
#endif
            }
            if(event==51)
            {
#ifdef PORTABLE_PROJECTILE_CHAIN
                if(s.combat==0 || commands[at+3]!=0 || loadNumber(at+1)!=0 || commands[at+4]>=P_DEFINITIONS || commands[at+5]!=0 || commands[at+6]!=0 || commands[at+7]!=0) { s.error=64;break; }
#else
                s.error=64;break;
#endif
            }
            if(event==50)
            {
#ifndef PORTABLE_DAMAGE_ACCUM
                s.error=64;break;
#else
                if(s.combat==0 || commands[input+P_WORLD_FRAME_INPUT_BASE]!=0x57533031U || uint(commands[at+4])>=P_DEFINITIONS) { s.error=64;break; }
#endif
            }
            if(event==40)
            {
#ifdef PORTABLE_PARTIAL_CHARGE
                uint64_t threshold=loadNumber(at+1);uint status;uint64_t count=f64ToI64(threshold,1,status);
                if(s.combat==0 || commands[input+P_WORLD_FRAME_INPUT_BASE]!=0x57533031U || status!=0 || count==0 || count>0x7fffffff || !f64Equal(threshold,f64FromI64(count)) || commands[at+3]!=1 || commands[at+6]!=0 || commands[at+5]>1 || commands[at+5]==0 && commands[at+4]!=0xffffffffU || commands[at+5]==1 && (int(commands[at+4])>0 || count!=1 || commands[at+7]!=1) || commands[at+7]!=1 && commands[at+7]!=2) { s.error=64;break; }
#else
                s.error=64;break;
#endif
            }
            if(event==41)
            {
#ifdef PORTABLE_WORLD_ROSTER
                uint stage=commands[at+7];
                if(s.combat==0 || commands[input+P_WORLD_FRAME_INPUT_BASE]!=0x57533031U || stage<1 || stage>3 || !f64Equal(loadNumber(at+1),f64FromI64(stage)) || commands[at+3]!=0 || commands[at+4]!=0xffffffffU || commands[at+5]!=0 || commands[at+6]!=0) { s.error=64;break; }
#else
                s.error=64;break;
#endif
            }
            if (event == 42 && s.combat == 0) { s.error = 64; break; }
            if (event == 31) s.namedEventOwners |= 1U << d.owner;
        }
        if (s.error != 0) break;
        for (uint slot = 0; slot < d.triggerCount; slot++)
            if (commands[input+P_EVENT_BASE+j*P_EVENT_WORDS+slot*8] == 9) s.stackEventOwners |= 1U << d.owner;
