#ifndef WORLD_ALLIED_RNG_FINISH
#define WORLD_ALLIED_RNG_FINISH(s)
#endif
// Shared program phases. GPU admission, command order and all serializers
// remain on the GPU. Failure exits in admission leave ready=false; the entry
// returns without running commands or serializers, as before extraction.

[noinline]
void initializePortableProgram(inout Runtime s,uint input,uint output,out bool ready)
{
    ready=false;
    s.resourceOutput = output;
    LAZY_BANK_INIT(output)
#ifdef PORTABLE_WORLD_PROJECTILE
    for(uint i=0;i<32;i++) results[output+P_FOCUS_STATE_BASE+i]=0;
#endif
    s.resourceCount = commands[input+P_RESOURCE_META_BASE];
    if (s.resourceCount > P_RESOURCE_KEYS) { results[output] = 64; return; }
    s.generation = 1; s.count = commands[input+1]; s.combat = commands[input+3]; s.inputBase = input; s.traceMode = commands[input+5];
    if (commands[input] != PORTABLE_ABI || s.count == 0 || s.count > P_DEFINITIONS || commands[input+2] > P_COMMANDS || s.traceMode > 2)
    { results[output] = 64; return; }
    s.coverSync = commands[input+7];
    if (s.coverSync > 1) { results[output] = 64; return; }
    s.carrierCount = s.count;
    for (uint row = 0; row < s.count; row++) s.carrierDefinition[row] = row;
    for (uint i = 0; i < 5; i++)
    {
        s.baseAttack[i] = loadNumber(input+8+2*i);
        uint health = input+P_HEALTH_BASE+i*P_HEALTH_WORDS;
        s.baseHP[i] = loadNumber(health); s.hp[i] = loadNumber(health+2); s.baseDefense[i] = loadNumber(health+4);
        uint cover = input+P_COVER_BASE+i*4;
        s.baseCoverHP[i] = loadNumber(cover); s.coverHP[i] = loadNumber(cover+2); s.coverMaxHP[i] = s.baseCoverHP[i];
        if (!f64Finite(s.baseCoverHP[i]) || !f64Less(0,s.baseCoverHP[i]) || !f64Finite(s.coverHP[i]) || f64Less(s.coverHP[i],0) || f64Less(s.baseCoverHP[i],s.coverHP[i])) { results[output] = 64; return; }
        s.hpPct[i] = f64Mul(f64Div(s.hp[i],s.baseHP[i]),HUNDRED);
    }
    s.defense = loadNumber(input+18); s.coreBonus = loadNumber(input+22);
    s.baseCrit = loadNumber(input+24); s.baseCritDamage = loadNumber(input+26);
    if (s.combat == 0) for (uint word = 0; word < 16; word++)
        if (commands[input+P_TARGET_ATTACK_BASE+word] != 0) { results[output] = 64; return; }
    if (s.combat == 0 && commands[input+P_AIM_POLICY_BASE] != 0) { results[output] = 64; return; }
    if (s.combat != 0) initializeCombat(s,input);
    if (s.error != 0) { results[output] = s.error; return; }
    uint numericStatus; s.probability = coreProbability(loadNumber(input+20),numericStatus);
    if (numericStatus != 0) { results[output] = 128; return; }
    if(!validGeometry(s)) { results[output]=64;return; }
    PROJECTILE_ADMIT_STAGE(s,4) admitDefinitions(s,input);
    if (s.error != 0) { results[output] = s.error; return; }
    PROJECTILE_ADMIT_STAGE(s,5) if(!initializeWorldFrame(s)) { results[output]=64;return; } PROJECTILE_ADMIT_STAGE(s,6) WORLD_OVERLAY_INIT(s,output) PROJECTILE_ADMIT_STAGE(s,7) WORLD_ACTORS_INIT(s,output) PROJECTILE_ADMIT_STAGE(s,8) WORLD_POOL_INIT(s,output) PROJECTILE_ADMIT_STAGE(s,9) WORLD_FIELDS_INIT(s,output) PROJECTILE_ADMIT_STAGE(s,10) WORLD_STATE_INIT(s,output) PROJECTILE_ADMIT_STAGE(s,11) COUNTER_INIT(s,output)
    PROJECTILE_ADMIT_STAGE(s,12) if(!validEnemyTargeting(s)) { results[output]=64;return; }
    PROJECTILE_ADMIT_STAGE(s,13) if(!validProtection(s)) { results[output]=64;return; }
    PROJECTILE_ADMIT_STAGE(s,14) if (!validStatusDefinitions(s)) { results[output]=64;return; }
    PROJECTILE_ADMIT_STAGE(s,15) if (!validNamedMagnitudes(s) || !validBaseCopies(s) || !validSkillIntervals(s) || !validTriggerReductions(s) || !validSkillHPBasis(s) || !validStackDefinitions(s)) { results[output]=64;return; }
    if (!validPelletInShot(s)) { results[output] = 64; return; }
    PROJECTILE_ADMIT_STAGE(s,16) if (!validEventCandidates(s)) { results[output] = 64; return; }
    PROJECTILE_ADMIT_STAGE(s,17) for (uint row = 0; row < s.count; row++) if (!validPendingDefinition(s,row)) { results[output] = 64; return; }
    PROJECTILE_ADMIT_STAGE(s,18) if (!validateDurationGroups(s)) { results[output] = 64; return; }
    PROJECTILE_ADMIT_STAGE(s,19) if (!validatePeriodicDefinitions(s)) { results[output] = 64; return; }
    PROJECTILE_ADMIT_STAGE(s,20) if (!initializeResources(s) || !validateReferences(s)) { results[output] = 64; return; }
    PROJECTILE_ADMIT_STAGE(s,22) if (!initializeSources(s)) { results[output]=64; return; }
    PROJECTILE_ADMIT_STAGE(s,23) if(!initializeStaged(s)) { results[output]=64;return; }
    PROJECTILE_ADMIT_STAGE(s,24) if (!initializeLandings(s)) { results[output]=64;return; }
    // Preserve existing rejection paths; close raw numeric-stat gaps before
    // any activation/query can silently ignore an unsupported buff identity.
    for(uint row=0;row<s.count;row++)
        if(definition_kind(input,row)==0 && !validPortableBuffStat(definition_stat(input,row))
#ifdef PORTABLE_EFFECT_TARGET_COUNT
           && definition_stat(input,row)!=TC_STAT
#endif
        )
        { PROJECTILE_ADMIT_STAGE(s,25) results[output]=64;return; }
#ifdef PORTABLE_EFFECT_TARGET_COUNT
    if(!validTargetCountDefinitions(s)) { results[output]=64;return; }
#ifdef PORTABLE_GENERATION_LOCKS
    if(!initializeGenerationLocks(s)) { results[output]=64;return; }
#ifdef PORTABLE_PHYSICAL_LOCKS
    if(!initializePhysicalLocks(s)) { results[output]=64;return; }
#ifdef PORTABLE_PHYSICAL_LOCK_COVER
    if(manualControls(s)&&commands[controlInput(s)+6]>=256){results[output]=64;return;}
    initializeManualControls(s);if(s.error!=0){results[output]=64;return;}
#ifdef PORTABLE_LOCK_PACKET_BINDINGS
    if(!initializeLockPackets(s)){results[output]=64;return;}
#endif
#endif
#endif
#endif
#endif
    PROJECTILE_ADMIT_STAGE(s,26) if(!initializeRevival(s)) { results[output]=64;return; }
#ifdef PORTABLE_HEAL_CHARGE
    if(healChargeEnabled(s)) for(uint word=0;word<8+512*20+8;word++) results[output+771072+word]=0;
#endif
    initializeFocusState(s);
    if(!initializeNativeNumeric(s)) { results[output]=64;return; }
    initializeSkillCritical(s);
    initializeNotCore(s);initializeDurationTrace(s);
#ifdef PORTABLE_FULL_BURST_QUERY_DIAGNOSTIC
    initializeNativeQueryDiagnostic(s);
#endif
    for(uint word=0;word<P_PROBABILITY_STATE_WORDS;word++) results[output+P_PROBABILITY_STATE_BASE+word]=0;
    if(commands[input+P_ENEMY_TARGET_META_BASE]!=0) mtSeed(output+P_ENEMY_RNG_BASE,uint64_t(commands[input+P_ENEMY_TARGET_META_BASE+1])|(uint64_t(commands[input+P_ENEMY_TARGET_META_BASE+2])<<32));
#ifdef PORTABLE_ATTACK_GROUPS
    if(!initializeAttackGroups(s)) { results[output]=64;return; }
#endif
    initializeHPWatches(s);
    ready=true;
}

[noinline]
void writePortableQuery(inout Runtime s,uint at,uint64_t when,uint output,inout uint queries)
{
    if(nativeNumericEnabled(s)) results[output+P_NATIVE_QUERY_BASE+9]=1;
    do
    {
        uint index = commands[at+6];
        if (index >= P_COMMANDS) { s.error = 64; break; }
        if (s.hpWatchCount != 0) dispatch(s,7,0,0,0,when,output); else syncHealth(s,when);
        writeHealth(s,when,output+P_HEALTH_QUERY_BASE+index*P_HEALTH_QUERY_WORDS);
        writeCovers(s,when,output+P_COVER_QUERY_BASE+index*40);
        writePendingBurst(s,output+P_PENDING_QUERY_BASE+index*4,false);
        writeIncoming(s,output+P_INCOMING_QUERY_BASE+index*P_INCOMING_QUERY_WORDS);
        writeProtection(s,output+P_PROTECTION_QUERY_BASE+index*50);
        writeDamageAccounting(s,output+P_DAMAGE_ACCOUNTING_QUERY_BASE+index*40);
        queries = max(queries,index+1); uint dst = output+P_QUERY_BASE+index*P_QUERY_WORDS;
        storeNumber(dst,when);
        for (uint who = 0; who < 5; who++) { storeNumber(dst+2+2*who,s.total[who]); storeNumber(dst+16+2*who,readStat(s,who,0,when)); }
        uint masks[P_MASK_WORDS]; for (uint word = 0; word < P_MASK_WORDS; word++) masks[word] = 0;
        for (uint j = 0; j < s.count; j++) if (s.timerActive[j] != 0) masks[j/32] |= 1U << (j%32);
        for (uint word = 0; word < P_MASK_WORDS; word++) results[output+P_TIMER_MASK_BASE+index*P_MASK_WORDS+word] = masks[word];
        if (s.combat != 0) writeCombatQuery(s,output+P_COMBAT_QUERY_BASE+index*P_COMBAT_QUERY_WORDS,output+P_COMBAT_STATE_QUERY_BASE+index*P_COMBAT_STATE_QUERY_WORDS);
        if (int(commands[at+5]) < -1) { s.error = 64; break; }
        uint selectedEnemy = int(commands[at+5]) < 0 ? 0 : commands[at+5];
        if (s.combat != 0 && selectedEnemy >= s.targetCount) { s.error = 64; break; }
        uint64_t enemyModifiers[3]; collectEnemyModifiers(s,commands[at+4],selectedEnemy,when,enemyModifiers);
        for (uint key = 0; key < 3; key++) storeNumber(dst+26+2*key,enemyModifiers[key]);
        results[dst+12] = masks[0]; results[dst+13] = s.combat != 0 ? s.targetGeneration[s.target] : s.generation; results[dst+14] = 0; results[dst+15] = s.timerClock;
    } while(false);
    if(nativeNumericEnabled(s)) results[output+P_NATIVE_QUERY_BASE+9]=0;
}

[noinline]
void executePortableCommands(inout Runtime s,uint input,uint output,out uint queries)
{
    queries = 0;
    for (uint step = 0; step < commands[input+2] && s.error == 0; step++)
    {
        uint at = input+P_COMMAND_BASE+step*8, op = commands[at]; uint64_t when = loadNumber(at+1);
        if (s.combat == 0 || op == 4) { beginLazyRoot(s,when); sampleWorld(s); }
        if (op == 4 && s.combat != 0 && s.combatStarted == 0)
        { s.combatStarted = 1; teamNotify(s,0,when,output); WORLD_INITIAL_SPAWN_START(s,when,output) initializeMagazines(s,when); }
        if (s.combat == 0 || op == 4) tick(s,when,output);
        if (s.error != 0) break;
        if (op == 0)
        {
            uint event = commands[at+3];
            if (s.combat == 0 && event == 1) s.phase = 5;
            if (s.combat == 0 && event == 2) s.phase = 0;
            dispatch(s,0,event,commands[at+4],int(commands[at+5]),when,output);
        }
#ifdef PORTABLE_EFFECT_TARGET_COUNT
#ifdef PORTABLE_GENERATION_LOCKS
        else if(op==45||op==46) { if(!generationLockCommand(s,at,when)) { s.error=64;break; } }
#endif
        else if(op==44) { if(!targetCountCommand(s,at,when,output,queries)) { s.error=64;break; } }
#endif
        else if (op == 4 && s.combat != 0) { if (s.clockMode != 0) { s.error = 64; break; } squadFrame(s,when,output); s.frameCount++; }
        WORLD_ACTOR_COMMAND(s,at) WORLD_POOL_COMMAND(s,at) WORLD_FIELDS_COMMAND(s,at) WORLD_STATE_COMMAND(s,at) COUNTER_COMMAND(s,at) else if (op == 26)
        {
            uint mask = commands[at+5]; uint64_t amount = loadNumber(at+6);
            if (commands[at+3] != 0 || commands[at+4] != 0 || mask == 0 || mask > 31 || !f64Finite(amount) || f64Less(amount,0)) { s.error = 64; break; }
            for (uint who = 0; who < 5 && s.error == 0; who++) if ((mask & ~s.downMask & (1U << who)) != 0 && !f64Zero(s.coverHP[who]) && !f64Zero(amount))
            {
                uint64_t taken = smaller(s.coverHP[who],amount);
                s.coverHP[who] = f64Add(s.coverHP[who],taken ^ F64_SIGN);
                s.coverDamage[who] = f64Add(s.coverDamage[who],taken);
                dispatch(s,0,36,who,0,when,output);
            }
        }
        else if (op==29)
        {
            uint owner=commands[at+4], name=commands[at+5], index=commands[at+6];
            if (owner>=5 || name>=P_DEFINITIONS || index>=P_COMMANDS || commands[at+3]!=0 || commands[at+7]!=0) { s.error=64; break; }
            writeSourceQuery(s,owner,name,index,when);
        }
        else if(op==32)
        {
            uint raw=s.inputBase+P_INCOMING_BASE+step*P_INCOMING_WORDS;
            if(commands[at+3]>1 || commands[at+4]!=0 || commands[at+5]!=0 || commands[at+6]!=0 || commands[at+7]!=0 || !f64Finite(loadNumber(raw)) || !f64Finite(loadNumber(raw+2)) || f64Less(loadNumber(raw),0) || f64Less(loadNumber(raw+2),0) || f64Less((uint64_t(0x46293e59)<<32)|uint64_t(0x39a08cea),loadNumber(raw)) || f64Less(f64FromI64(1000000),loadNumber(raw+2))) { s.error=64;break; }
            dispatch(s,8,0,0,int(step),when,output);
        }
        else if(op==31)
        {
            uint raw=s.inputBase+P_INCOMING_BASE+step*P_INCOMING_WORDS;
            if(commands[at+3]>1 || commands[at+4]>31 || commands[at+5]==0 || commands[at+5]>31 || commands[at+6]!=0 || commands[at+7]!=0 || !f64Finite(loadNumber(raw)) || !f64Finite(loadNumber(raw+2)) || f64Less(loadNumber(raw),0) || f64Less(loadNumber(raw+2),0) || f64Less((uint64_t(0x46293e59)<<32)|uint64_t(0x39a08cea),loadNumber(raw)) || f64Less(f64FromI64(1000000),loadNumber(raw+2))) { s.error=64;break; }
            dispatch(s,8,0,0,int(step),when,output);
        }
        else if (op == 25) dispatch(s,8,0,0,int(step),when,output);
        else if (op == 24 && s.combat != 0) { advanceCombat(s,when,output); WORLD_SKILL_FINAL(s,when,output) }
        else if ((op == 20 || op == 21 || op == 22 || op == 27) && s.combat != 0)
        {
            uint target = commands[at+5], who = commands[at+4];
            if (who >= 5 || (op == 27 ? target > 1 : target >= s.targetCount)) { s.error = 64; break; }
            if (op == 27)
            {
                uint bit = 1U << who; s.automaticAddAim = target != 0 ? s.automaticAddAim | bit : s.automaticAddAim & ~bit;
                uint aimed = aimedTarget(s,who); s.target = aimed == 0xffffffff ? 0 : aimed;
            }
            else if (op == 20) { s.automaticAddAim &= ~(1U << who); s.aim[who] = target; s.target = target; }
            else if (op == 22) s.targetAlive[target] = 0;
            else
            {
                if (s.targetGeneration[target] == 0x7fffffff) { s.error = 2; break; }
                if (s.enemyEpoch == 0x7fffffff) { s.error = 2; break; }
                s.enemyBirth[target] = ++s.enemyEpoch;
                s.enemyAttackOrder = 0; s.enemySpawnOrder = 0; // Both ranks depend on spawn order.
                s.targetGeneration[target]++; s.targetAlive[target] = 1; s.targetHP[target] = loadNumber(at+6); s.targetMaxHP[target] = s.targetHP[target]; s.targetDealt[target] = 0;
            }
        }
        else if (op == 18)
        {
            uint who = commands[at+4];
            if (who >= 5) { s.error = 64; break; }
            if ((s.downMask & (1U << who)) != 0) continue;
            uint target = s.combat != 0 ? aimedTarget(s,who) : 0;
            if (target == 0xffffffff) continue;
            s.target = target;
            uint64_t amount = damageValue(s,who,loadNumber(at+5),when,true,s.coreBonus,0,ONE,(s.attackContext[who] & 1) != 0);
            if (s.error != 0) break;
            if (s.landingPolicy==0) land(s,who,target,amount);
            dispatch(s,0,8,who,0,when,output);
            WORLD_PHYSICAL_BEGIN(s,who,target,amount) if (s.landingPolicy!=0) land(s,who,target,amount);
            if ((s.healthMask & 64) != 0 && s.error == 0) dispatch(s,17,0,who,0,when,output,amount); WORLD_GATE_END
        }
        else if (op == 30)
        {
            if (s.landingPolicy==0 || commands[at+3]!=0 || commands[at+4]!=0 || commands[at+5]!=0 || commands[at+6]!=0 || commands[at+7]!=0) { s.error=64;break; }
            drainLandings(s,when,output);
        }
        else if (op == 28)
        {
            uint who = commands[at+4], key = commands[at+5], index = commands[at+6];
            if (who >= 5 || key >= s.resourceCount || index >= P_COMMANDS || commands[at+3] != 0 || commands[at+7] != 0) { s.error = 64; break; }
            uint dst = output+P_RESOURCE_QUERY_BASE+index*12, pos = who*P_RESOURCE_KEYS+key;
            storeNumber(dst,when); results[dst+2] = who; results[dst+3] = key;
            results[dst+4] = resourceFlags(s,pos); results[dst+5] = 0;
            storeNumber(dst+6,resourceValue(s,pos)); storeNumber(dst+8,resourceCap(s,pos));
            storeNumber(dst+10,(resourceFlags(s,pos) & 2) != 0 ? effectiveResourceCap(s,who,key) : 0);
        }
        else if (op == 2) writePortableQuery(s,at,when,output,queries);
        else s.error = 64;
    }
}

[noinline]
void writePortableProgram(inout Runtime s,uint input,uint output,uint queries)
{
    worldFrameFinish(s);
    writeDamageAccounting(s,output+P_DAMAGE_ACCOUNTING_STATE_BASE,true);
    writePendingBurst(s,output+P_PENDING_STATE_BASE,true);
    writeCovers(s,commands[input+2] > 0 ? loadNumber(input+P_COMMAND_BASE+(commands[input+2]-1)*8+1) : 0,output+P_COVER_STATE_BASE);
    writeIncoming(s,output+P_INCOMING_STATE_BASE);
    writeProtection(s,output+P_PROTECTION_STATE_BASE);
    writeHealth(s,commands[input+2] > 0 ? loadNumber(input+P_COMMAND_BASE+(commands[input+2]-1)*8+1) : 0,output+P_HEALTH_STATE_BASE);
    for (uint j = 0; j < s.count; j++)
    {
        uint at = output+P_STATE_BASE+j*10; storeNumber(at,s.due[j]); storeNumber(at+2,s.expiry[j]);
        results[at+4] = s.timerEpoch[j]; results[at+5] = s.timerOrder[j]; results[at+6] = s.timerActive[j];
        results[at+7] = s.stacks[j]; results[at+8] = s.activations[j];
        for (uint slot = 0; slot < 8; slot++) results[output+P_COUNTER_STATE_BASE+j*8+slot] = s.counters[j*8+slot];
        storeNumber(output+P_PERIOD_STATE_BASE+j*4,s.periodDue[j]); storeNumber(output+P_PERIOD_STATE_BASE+j*4+2,s.periodPrevious[j]);
        results[output+P_TIMER_TARGET_BASE+j*2] = s.timerTarget[j];
        results[output+P_TIMER_TARGET_BASE+j*2+1] = s.timerGeneration[j];
        uint periodic = output+P_PERIODIC_STATE_BASE+j*12;
        results[periodic] = definition_periodicFlags(s.inputBase,j); results[periodic+1] = definition_periodicGroup(s.inputBase,j);
        results[periodic+2] = s.periodicOrder[j]; results[periodic+3] = 0;
        for (uint target = 0; target < 8; target++) results[periodic+4+target] = s.periodicGeneration[j*8+target];
    }
    if (s.combat != 0) for (uint who = 0; who < 5; who++)
    {
        uint at = output+P_WEAPON_STATE_BASE+who*P_WEAPON_STATE_WORDS;
        storeNumber(at,s.warm[who]); storeNumber(at+2,s.lastFire[who]); storeNumber(at+4,s.lastInterval[who]);
        storeNumber(at+6,s.postReloadUntil[who]); storeNumber(at+8,s.lastSpread[who]); storeNumber(at+10,s.lastProbability[who]);
        results[at+12] = s.probabilityEvaluations[who]; results[at+13] = s.pendingAutoReload[who]; storeNumber(at+14,s.chargeStartedAt[who]);
    }
    if (s.combat != 0) for (uint j = 0; j < s.targetCount; j++)
    {
        uint dst = output+P_TARGET_STATE_BASE+j*10;
        results[dst] = s.targetGeneration[j]; results[dst+1] = s.targetAlive[j];
        storeNumber(dst+2,s.targetHP[j]); storeNumber(dst+4,s.targetDamage[j]); results[dst+6] = s.targetHits[j];
    }
    for (uint pass = 0; pass < s.orderedCount; pass++)
    {
        uint slot = s.orderedRows[pass], at = output+P_CARRIER_STATE_BASE+pass*P_CARRIER_WORDS;
        results[at] = slot; results[at+1] = s.carrierDefinition[slot]; results[at+2] = s.activeRecipients[slot];
        results[at+3] = s.stacks[slot]; results[at+4] = s.alive[slot] | (s.lazyPending[slot] << 1) | (uint(s.bulletInitialized[slot]==2)<<2);
        storeNumber(at+5,s.end[slot]); storeNumber(at+7,s.activated[slot]); results[at+9] = s.entryOrder[slot]; storeNumber(at+10,s.hpSnapshot[slot]);
        results[at+12] = definition_enemyBuff(s.inputBase,s.carrierDefinition[slot])!=0 ? s.enemyCaptureGeneration[slot] : uint(s.bulletLeft[slot]);
        for (uint who = 0; who < 5; who++) { results[at+13+who] = s.recipientBullets[slot*5+who]; results[at+18+who] = s.recipientStacks[slot*5+who]; }
    }
    if (s.error==0 && s.sourceEnabled!=0 && commands[input+2]!=0) finishSourceCounts(s,loadNumber(input+P_COMMAND_BASE+(commands[input+2]-1)*8+1));
    results[output+P_RESOURCE_HEADER_BASE] = s.resourceTraceCount; results[output+P_RESOURCE_HEADER_BASE+1] = s.resourceTraceTotal;
    results[output+9] = s.orderedCount;
    results[output+10] = s.cacheCount; results[output+11] = s.cacheEvaluations; results[output+12] = s.cacheReuses; results[output+13] = s.lazyPendingCount; results[output+14] = s.lazyMappedPendingCount; results[output+15] = s.bulletCount;
    if((s.quantityMask & 512)!=0) for(uint who=0;who<5;who++) storeNumber(output+P_MODE_ENTRY_STATE_BASE+who*2,s.modeEntryUntil[who]);
    results[output] = s.error; results[output+1] = queries; results[output+2] = s.traceCount; results[output+3] = s.maxDepth; results[output+4] = s.burstTraceCount; results[output+6] = s.traceTotal;
    results[output+7] = s.burstTraceTotal; results[output+8] = s.frameCount; WORLD_RELOAD_FINAL(s) WORLD_ALLIED_RNG_FINISH(s) LAZY_BANK_FINISH(output)
#ifdef PORTABLE_WORLD_PROJECTILE
    if(nativeNumericEnabled(s) && !finishOrderedHistory(output+P_ORDERED_HISTORY_BASE,results[output+P_REVIVAL_BASE+6])) results[output]=64;
#ifdef PORTABLE_COORDINATE_EXISTING_HANDLERS
    if(s.error==0&&!finishCoordinatePacketHistory(s)) results[output]=64;
#ifdef PORTABLE_COORDINATE_TYPED_WEAPONS
    if(s.error==0&&!finishCoordinateTypedWeaponHistory(s)) results[output]=64;
#endif
#endif
#endif
}
