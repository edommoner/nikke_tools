// One DFS step per call. The caller retains frame sampling, work/depth
// budgets, HP edge draining and context restoration. Both targets use this file.
// The single-pass loop preserves outer continue/break exits of the original
// dispatch body; nested loops and all arithmetic/side effects stay in order.

[noinline]
void advanceSkillDamageFrame(inout Runtime s, inout Frame frames[32], inout int depth, Frame f, uint output)
{
    do
    {
        Definition damage = readDefinition(s.inputBase,uint(f.argument)); damage.damageHits=f.repeatLeft;
        if (f.cursor >= damage.damageHits
#ifdef PORTABLE_FULL_BURST_LANDING
            && !(damage.damagePending==2 && f.cursor==0)
#endif
        )
        {
#ifdef PORTABLE_PROJECTILE_CHAIN
            if(f.cursor==0 && f.event==1)
            {
                uint saved=s.target;s.target=0;WORLD_SKILL_SCOPE_BEGIN(s)
                queryOnlyFullBurstLanding(s,uint(f.argument),f.time);
                WORLD_SKILL_SCOPE_END(s) s.target=saved;
            }
#endif
            depth--;
            if (s.combat != 0 && f.value != 0)
            {
                uint64_t gain = f64Less(damage.damageGauge,0) ? (s.physicalGaugeOwner==damage.owner+1 ? s.physicalGaugeGain : s.gain[damage.owner]) : damage.damageGauge;
                WORLD_SKILL_GAUGE(s,damage.owner) addBurstGauge(s,f64Add(f64Mul(gain,f64FromI64(f.value)),f64Mul(f.gaugeFlat,f64FromI64(f.value))));
            }
#ifdef PORTABLE_PROJECTILE_CHAIN
            if(f.event==1 && s.error==0) pushFrame(s,frames,depth,0,51,damage.owner,int(damage.name),f.time);
#endif
            continue;
        }
        if (s.landingPolicy != 0)
        {
            if (f.cursor == 0)
            {
                s.target=WORLD_SKILL_BASIS(s,damage.damageRoute>=2 || damage.damageRoute==1 ? 0 : f.target);
                uint64_t partAmount=0,interruptAmount=0;uint interruptReach=0;
#ifdef PORTABLE_FULL_BURST_LANDING
                uint parentExclusion=s.damageExclusion;if(damage.damagePending==2) s.damageExclusion=uint(f.argument)+1;
#endif
                WORLD_SKILL_SCOPE_BEGIN(s)
#ifdef PORTABLE_FULL_BURST_LANDING
                if(damage.damagePending==2 && damage.damageHits==0)
                { queryOnlyFullBurstLanding(s,uint(f.argument),f.time);frames[depth].healthPrevious=0; }
                else
#endif
                {

#ifdef PORTABLE_WORLD_PROJECTILE
                if(worldSkillsEnabled(s)&&worldSkillNeedsReach(s,damage))
                    frames[depth].healthPrevious=sampleWorldPartSkill(s,damage,f.healthValue,f.time,partAmount,interruptAmount,interruptReach);
                else
#endif
                    frames[depth].healthPrevious=damage.damageNormal!=0 ? damageValue(s,damage.owner,f.healthValue,f.time,true,s.combat!=0 ? s.coreDamageBonus[damage.owner] : s.coreBonus,damage.damageFlags,ONE,(s.attackContext[damage.owner]&1)!=0,false,damage._wireRow) : damageValue(s,damage.owner,f.healthValue,f.time,false,s.coreBonus,damage.damageFlags,ONE,false,false,damage._wireRow);
                }
#ifdef PORTABLE_FULL_BURST_LANDING
                s.damageExclusion=parentExclusion;
#endif
                WORLD_SKILL_SCOPE_END(s)
                // Coefficient is consumed at cursor0; subsequent hits and child
                // returns reuse this captured part value, never the coefficient.
                frames[depth].healthValue=partAmount;frames[depth].interruptAmount=interruptAmount;frames[depth].interruptReach=interruptReach;
                uint order=0;frames[depth].repeatRow=(damage.periodicFlags&1)!=0 ? periodicDamageMask(s,uint(f.argument),order) : 0xffffffff;
                frames[depth].skillCritRate=s.lastDamageCritRate;
                frames[depth].repeatPassive=order;frames[depth].healthNext=s.enemyEpoch;
            }
            if (s.error!=0) break;
#ifdef PORTABLE_FULL_BURST_LANDING
            if(damage.damagePending==2 && damage.damageHits==0)
            { depth--;
#ifdef PORTABLE_PROJECTILE_CHAIN
              if(f.event==1 && s.error==0) pushFrame(s,frames,depth,0,51,damage.owner,int(damage.name),f.time);
#endif
              continue;
            }
#endif
            enqueueLanding(s,uint(f.argument),f.target,frames[depth].repeatRow,frames[depth].repeatPassive,frames[depth].healthPrevious,f.time,f.cursor+1,damage.damageHits,uint(depth+1),uint(frames[depth].healthNext),frames[depth].healthValue,frames[depth].interruptAmount,frames[depth].interruptReach);
            frames[depth].cursor++;frames[depth].value++;
            if (s.error==0) pushSkillHit(s,frames,depth,damage,frames[depth].skillCritRate,f.time);
            continue;
        }
        uint packedOrder; uint mask = (damage.periodicFlags & 1) != 0 ? periodicDamageMask(s,uint(f.argument),packedOrder) : enemyDamageMask(s,damage,f.target,packedOrder);
        if (mask == 0 && (damage.periodicFlags & 1) == 0) { frames[depth].cursor = damage.damageHits; continue; }
        uint basis = damage.damageRoute >= 2 || damage.damageRoute == 1 ? 0 : f.target;
        s.target = basis;
        uint64_t coefficient = f.healthValue, amount;
        if (damage.damageNormal != 0)
            amount = damageValue(s,damage.owner,coefficient,f.time,true,s.combat != 0 ? s.coreDamageBonus[damage.owner] : s.coreBonus,damage.damageFlags,ONE,(s.attackContext[damage.owner] & 1) != 0,false,damage._wireRow);
        else amount = damageValue(s,damage.owner,coefficient,f.time,false,s.coreBonus,damage.damageFlags,ONE,false,false,damage._wireRow);
        if (s.error != 0) break;
        uint64_t weighted = (damage.damageFlags & H_SPLIT) != 0 && damage.damageRoute >= 2 && (damage.periodicFlags & 1) == 0 ? f64Mul(amount,f64Div(ONE,f64FromI64(enemyMaskCount(mask)))) : amount;
        uint64_t share = weighted;
        if ((damage.damageFlags & H_SPLIT) != 0 && enemyMaskCount(mask) > 1)
        {
            uint status; uint64_t rounded = f64ToI64(weighted,0,status);
            if (status != 0) { s.error = 16; break; }
            share = f64FromI64(rounded);
        }
        for (uint pass = 0; pass < 8; pass++)
        { uint encoded = (packedOrder >> (pass*4)) & 15; if (encoded == 0) break; WORLD_SKILL_BEGIN(s,damage.owner,encoded-1,share) land(s,damage.owner,encoded-1,share); WORLD_GATE_END }
        frames[depth].cursor++; frames[depth].value++;
        logDamagePacket(s,damage,uint(f.argument),mask,basis,f.cursor+1,share,weighted,packedOrder,f.time,uint(depth+1),output);
        if (s.error == 0) pushSkillHit(s,frames,depth,damage,s.lastDamageCritRate,f.time);
        continue;
    } while(false);
}

[noinline]
void advanceIncomingFrame(inout Runtime s, inout Frame frames[32], inout int depth, Frame f, uint output)
{
    do
    {
        uint at = incomingCommandAddress(s,uint(f.argument));
        if(f.event==5) { depth--;continue; }
        if(f.event==6) { frames[depth].event=0;continue; }
        if(f.mode==23 && f.event==0)
        {
            frames[depth].event=1;
            pushFrame(s,frames,depth,20,0,f.owner,f.argument,f.time);
            if(s.error==0) { frames[depth].healthValue=f.healthValue;frames[depth].repeatPassive=f.repeatRow; }
            continue;
        }
        if (f.event == 0)
        {
            // Selection is part of this event frame:sourceTime and HP edges
            // are current before choosing the frozen,ordered victim list.
            WORLD_ENEMY_ATTACK_CAPTURE(s,frames,depth,f) if(f.mode==8 && commands[at]==32 && f.cursor==0)
            {
                chooseEnemyVictims(s,uint(f.argument),f.time);
                if(s.error!=0) break;
            }
            uint who;
            if(commands[at]==32)
            {
                uint order=results[enemyQueryAddress(s,uint(f.argument))+1],cursor=frames[depth].cursor,encoded=0;
                while(cursor<5)
                {
                    encoded=(order>>(3*cursor++))&7;
                    if(encoded==0 || (s.downMask&(1U<<(encoded-1)))==0) break;
                }
                if(encoded==0 || (s.downMask&(1U<<(encoded-1)))!=0) { depth--;continue; }
                who=encoded-1;frames[depth].cursor=cursor;
            }
            else
            {
                uint mask=commands[at+5] & ~s.downMask;who=frames[depth].cursor;
                while(who<5 && (mask&(1U<<who))==0) who++;
                if(who==5) { depth--;continue; }
                frames[depth].cursor=who+1;
            }
            frames[depth].owner=who;
            uint input = incomingDamageAddress(s,uint(f.argument));
            frames[depth].healthValue = incomingBodyDamage(s,who,WORLD_ENEMY_ATTACK_VALUE(s,frames,depth,f,loadNumber(input)),loadNumber(input+2),f.time);
            frames[depth].event = 1;
            if((commands[at]==31 || commands[at]==32))
            {
                uint64_t amount=frames[depth].healthValue;
                uint group=incomingSplitGroup(s,who,f.time);
                if(group!=0)
                {
                    uint count=0;for(uint order=group;order!=0;order>>=3) count++;
                    frames[depth].event=6;pushFrame(s,frames,depth,22,0,who,f.argument,f.time,group);
                    if(s.error==0) frames[depth].healthValue=f64Div(amount,f64FromI64(count));
                    continue;
                }
                uint record=incomingRecordAddress(s,uint(f.argument),who,who,true,P_PROTECTION_HIT_BASE+(uint(f.argument)*5+who)*16);frames[depth].repeatRow=record;
                pushFrame(s,frames,depth,20,0,who,f.argument,f.time);
                if(s.error==0) { frames[depth].healthValue=amount;frames[depth].repeatPassive=record; }
            }
            continue;
        }
        if (f.event == 1)
        {
            uint64_t amount = liveMarker(s,f.owner,S_invincible,f.time) ? 0 : f.healthValue;
            amount=transferHealingStorage(s,f.owner,amount,f.time,false);
            if (!f64Zero(amount) && !f64Less(amount,s.hp[f.owner]) && liveMarker(s,f.owner,S_undying,f.time)) amount = larger(0,f64Add(s.hp[f.owner],ONE ^ F64_SIGN));
            frames[depth].healthValue = amount; frames[depth].event = 2;
            if (!f64Zero(amount) && !f64Less(amount,s.hp[f.owner])) pushFrame(s,frames,depth,0,37,f.owner,0,f.time);
            continue;
        }
        if (f.event == 2)
        {
            uint64_t amount = f.healthValue;
            if (!f64Zero(amount) && !f64Less(amount,s.hp[f.owner]) && liveMarker(s,f.owner,S_undying,f.time)) amount = larger(0,f64Add(s.hp[f.owner],ONE ^ F64_SIGN));
            bool fell = !f64Zero(amount) && !f64Less(amount,s.hp[f.owner]);
            if((commands[at]==31 || commands[at]==32)) frames[depth].healthValue=amount;
            s.receivedDamage[f.owner] = f64Add(s.receivedDamage[f.owner],amount);
            if (!f64Finite(s.receivedDamage[f.owner])) { s.error = 16; break; }
            if (s.receivedHits[f.owner] == 0x7fffffff) { s.error = 2; break; }
            s.receivedHits[f.owner]++;
            s.hp[f.owner] = larger(0,f64Add(s.hp[f.owner],amount ^ F64_SIGN));
            if (!fell) syncHealthActor(s,f.owner,f.time);
            frames[depth].value = uint(fell); frames[depth].event = 3;
            if(f.mode==8 || f.repeatPassive!=0) pushFrame(s,frames,depth,0,32,f.owner,0,f.time); continue;
        }
        if(f.event==3 && f64Less(0,f.healthPrevious))
        { frames[depth].event=4;pushFrame(s,frames,depth,0,36,f.owner,0,f.time);continue; }
        if((commands[at]==31 || commands[at]==32))
        {
            uint hit=output+f.repeatRow;
            storeNumber(hit+12,f.healthValue);storeNumber(hit+14,f.value!=0 && (s.downMask&(1U<<f.owner))==0 ? 0 : s.hp[f.owner]);
            if(f.value!=0 && (s.downMask&(1U<<f.owner))==0) results[hit+3]|=4;
        }
        frames[depth].event = f.mode==23 ? 5 : 0;
        if (f.value != 0 && (s.downMask & (1U << f.owner)) == 0)
        {
            knockDown(s,f.owner,f.time);
            if(revivalEnabled(s)) pushFrame(s,frames,depth,30,0,f.owner,0,f.time);
            else for (int observer = 4; observer >= 0; observer--) if ((s.downMask & (1U << observer)) == 0) pushFrame(s,frames,depth,0,46,uint(observer),0,f.time);
            pushFrame(s,frames,depth,0,38,f.owner,0,f.time);
        }
        continue;
    } while(false);
}

[noinline]
void applyDefinitionFrame(inout Runtime s,inout Frame frames[32],inout int depth,Frame f,uint output,Definition d,uint row,uint recipientMask,uint64_t recipientOrder)
{
    do
    {
        if (d.kind == 0 || d.kind == 4)
        {
            uint sourceRow=row; uint64_t duration = d.duration; bool activationLazy = d.lazyGroup != 0;
            uint64_t expires=definitionExpiry(s,sourceRow,f.time);
            if(!activationLazy) { recipientMask=filterHarmful(s,d,recipientMask,recipientOrder);if(d.polarity==2 && recipientMask==0) continue; }
            uint capturedGeneration=d.enemyBuff!=0 && recipientMask!=0 ? (f.mode==19 ? f.repeatPassive : s.targetGeneration[firstbithigh(recipientMask>>5)]) : 0;
            row = findCarrier(s,row,recipientMask,f.time,capturedGeneration,recipientOrder);
            if (s.error != 0) break;
            d = residentDefinition(s,row);
            bool live = s.alive[row] != 0;
            if (!live) { storeReferenceCapture(s,row,0,0);captureBuffReference(s,row,sourceRow); }
            if (!live) { resetBulletCarrier(s,row); discardLazy(s,row); s.stacks[row] = 0; s.hpSnapshot[row] = 0; markEntry(s,row); }
            invalidateFocusNumeric(s);
            uint previousStack = s.stacks[row];
            if (activationLazy)
            {
                if (!live) { s.lazyPending[row] = 1; s.lazyPendingCount++; s.lazyMappedPendingCount += d.queryResolve; s.activeRecipients[row] = 0; }
                else if (s.lazyPending[row] != 0) unlinkLazyCache(s,row);
            }
            else { s.activeRecipients[row] = recipientMask; storeCarrierOrder(s,row,recipientOrder); }
            if(!live || d.maxStack!=1) s.stacks[row] = checkedStackIncrement(s.stacks[row],d.maxStack,s.error);
            if (s.error!=0) break;
            WORLD_FIELDS_BIND(s,row,d,f) s.alive[row] = 1; s.activated[row] = f.time;
            s.end[row] = expires;
            if(activationLazy && d.stat==S_heal_overcharge_store)
            {
                uint object=protectionObject(s,row);
                if(object!=PROTECTION_NONE) results[protectionAddress(s,object)+22]|=STORAGE_PENDING;
            }
            prepareBaseCopy(s,row,!live);
            COUNTER_PREPARE(s,row,f.time) if (d.enemyBuff != 0) s.enemyCaptureGeneration[row] = capturedGeneration;
            if (d.bulletDuration != 0) prepareBulletActivation(s,row,recipientMask,live,activationLazy,previousStack);
            bool namedCandidate = (d.buffEvent & 1) != 0 && (!live || d.maxStack != 1) && s.namedEventOwners != 0;
#ifdef PORTABLE_BUFF_AUDIENCE_SCAN_REFERENCE
            uint64_t audienceOrder = buffAudienceOrder(s,row);
#else
            uint64_t audienceOrder = namedCandidate ? buffAudienceOrder(s,row) : 0;
#endif
            bool namedNotice = namedCandidate && (s.namedEventOwners & packedRecipientMask(audienceOrder)) != 0;
            bool stackNotice = (d.buffEvent & 1) != 0 && previousStack != s.stacks[row] && (s.stackEventOwners & (1U << d.owner)) != 0;
            if (live && !namedNotice && !stackNotice) captureBuffReference(s,row,sourceRow);
            if (namedNotice || stackNotice || (d.buffEvent >> 2) != 0 || baseCopyStat(d.stat) || immunityPolicy(s.inputBase,sourceRow)==3 || (protectionPolicy(s,sourceRow)&255)==1 || (protectionPolicy(s,sourceRow)&255)==2 || (protectionPolicy(s,sourceRow)&255)==9
#ifdef PORTABLE_HEAL_CHARGE
                || (protectionPolicy(s,sourceRow)&255)==10
#endif
#ifdef PORTABLE_DAMAGE_ACCUM
                || ((protectionPolicy(s,sourceRow)&255)>=13 && (protectionPolicy(s,sourceRow)&255)<=15)
#endif
                )
            {
                pushFrame(s,frames,depth,13,0,d.owner,int(row),f.time,d.enemyBuff!=0 ? uint64_t(recipientMask&~31U)<<16 : recipientOrder);
                if (s.error == 0)
                {
                    frames[depth].healthValue = audienceOrder; frames[depth].healthPrevious = previousStack;
                    frames[depth].healthNext = s.stacks[row]; frames[depth].repeatLeft = uint(live);
                    frames[depth].repeatRow = s.carrierDefinition[row]; frames[depth].repeatPassive = s.entryOrder[row]; frames[depth].cursor=sourceRow+1;
                }
            }
            else if (activationLazy) { }
            else if (s.hpWatchCount != 0 && (d.stat >= S_max_hp_pct && d.stat <= S_max_hp_only_pct || d.stat == S_max_hp_from_max_hp_pct))
            {
                uint64_t grant = prepareHealthGrant(s,row,f.time);
                pushFrame(s,frames,depth,5,0,d.owner,int(row),f.time);
                if (s.error == 0) { frames[depth].healthValue = grant; frames[depth].value = recipientOrder; }
            }
            else
            {
                applyHealthBuff(s,row,f.time);
            }
        }
        else if(d.kind==27 || d.kind==31)
        {
            uint kind=d.kind==27 ? 1 : 2;
            if(!f64Zero(d.value)) for(uint i=0;i<5;i++)
            {
                uint encoded=(recipientOrder>>(i*3))&7;if(encoded==0) break;uint who=encoded-1;
                uint64_t basis=d.healthScaling!=0 ? effectiveMaxHP(s,d.owner,f.time) : protectionCapacity(s,who,kind);
                uint64_t amount=f64Div(f64Mul(basis,d.value),HUNDRED);
                if(!f64Finite(amount)) { s.error=16;break; }
                healProtection(s,who,kind,amount,f.time);
            }
        }
        else if(d.kind==29)
        { pushFrame(s,frames,depth,28,0,d.owner,int(row),f.time,recipientOrder);if(s.error==0) frames[depth].healthValue=d.value; }
        else if (d.kind == 7 || d.kind == 30)
        {
            pushFrame(s,frames,depth,11,0,d.owner,int(row),f.time);
            if (s.error == 0) frames[depth].value = recipientOrder;
        }
        else if (d.kind == 6)
        {
            // Stack recipient deliveries in reverse so each child completes
            // synchronously before the next squad member's heal is evaluated.
            for (int index = 4; index >= 0; index--)
            {
                uint encoded = (recipientOrder >> (3*uint(index))) & 7;
                if (encoded != 0) pushFrame(s,frames,depth,3,0,encoded-1,int(row),f.time);
            }
        }
        else if (d.kind == 8)
        {
            if (s.hpWatchCount != 0)
            { pushFrame(s,frames,depth,6,0,d.owner,int(row),f.time); if (s.error == 0) frames[depth].value = recipientOrder; }
            else
            {
                for (uint who = 0; who < 5; who++) if ((recipientMask & (1U << who)) != 0)
                    s.hp[who] = storageBodyReduce(s,who,d.value,f.time);
                syncHealth(s,f.time);
            }
        }
        else if (d.kind == 5) reduceBurstReady(s,recipientMask,d.value,f.time);
        else if (d.kind == 22) reduceSkillCooldown(s,recipientMask,d.value,f.time);
        else if (d.kind == 24) { if (recipientMask != 0) addBurstGauge(s,d.value); }
        WORLD_RELOAD_DISPATCH(s,d,recipientOrder,f.time) else if (d.kind == 13 || d.kind == 14)
        {
            applyAmmoInstant(s,d,recipientMask,f.time);
            // The percentage form emits its named completion even with no recipients.
            if (d.kind == 13 && d.target != 0 && s.error == 0)
                pushFrame(s,frames,depth,0,31,d.owner,int(d.name),f.time);
        }
        else if (d.kind >= 9 && d.kind <= 11)
        {
            ResourceDefinition r = resourceDefinition(s,row);
            if ((r.flags & 2) == 0) continue;
            uint key = r.key-1, at = d.owner*P_RESOURCE_KEYS+key;
            if ((r.flags & 1) != 0) { setResourceCap(s,at,r.cap); }
            uint64_t old = resourceValue(s,at), value = old, spent = 0;
            if (d.kind == 9)
            {
                value = f64Add(old,d.value);
                if ((resourceFlags(s,at) & 2) != 0) value = smaller(value,effectiveResourceCap(s,d.owner,key));
            }
            else
            {
                uint64_t available = larger(0,f64Add(old,r.minimum ^ F64_SIGN));
                bool all = f64Equal(d.value,F64_SIGN | ONE);
                value = all ? r.minimum : larger(r.minimum,f64Add(old,d.value ^ F64_SIGN));
                spent = all ? available : larger(0,smaller(d.value,available));
            }
            if (!f64Finite(value) || !f64Finite(spent)) { s.error = 16; break; }
            setResourceValue(s,at,value); results[resourceAddress(s,at)] |= 1;
            if (d.kind == 9 && f64Less(old,value) && results[s.resourceOutput+P_RESOURCE_STEP_HEAD_BASE+at] != 0)
            {
                pushFrame(s,frames,depth,14,0,d.owner,int(key),f.time);
                if (s.error == 0) { frames[depth].healthPrevious = old; frames[depth].healthNext = value; }
            }
            else if (d.kind == 11 && f64Less(0,spent))
            {
                uint status; uint64_t count = f64ToI64(spent,1,status);
                if (status != 0 || count > 0x7fffffff) { s.error = 2; break; }
                if (s.resourceAmmoObserved == 0 && s.traceMode != 1)
                {
                    if (count > 0x7fffffff-s.resourceTraceTotal) { s.error = 2; break; }
                    s.resourceTraceTotal += uint(count);
                }
                else if (count != 0) pushFrame(s,frames,depth,15,0,d.owner,int(key),f.time,uint(count));
            }
        }
        else if (d.kind == 37)
        {
            uint status;int64_t count=int64_t(f64ToI64(d.value,1,status));
            if(status!=0) { s.error=16;break; }
            if(count>1) pushFrame(s,frames,depth,32,0,d.owner,0,f.time,uint(count-1));
        }
        else if (d.kind == 25) s.pendingReentry[d.owner] = 1;
        else if (d.kind == 2)
        {
            int prior = s.modeIndex[d.owner];
            if (d.toggle != 0 && prior >= 0 && definition_name(s.inputBase,prior) == d.name)
            { clearMode(s,d.owner,f.time); pushFrame(s,frames,depth,0,29,d.owner,int(d.name),f.time); }
            else
            {
                if (prior != int(row)) { s.modeEpoch[d.owner]++; s.modeShots[d.owner] = 0; }
                s.modeIndex[d.owner] = int(row);
                s.modeEnd[d.owner] = f64Less(d.duration,0) ? FOREVER : f64Add(f.time,d.duration);
                if (d.target != 0) pushFrame(s,frames,depth,12,31,d.owner,int(d.name),f.time);
            }
        }
        else if(stackOperation(d.kind))
        {
            uint begin=s.removalCount;
            if(d.kind==18) initializeStack(s,row,f.target,f.time);
            else mutateStacks(s,row,recipientMask,f.time);
            if(s.error==0 && s.removalCount>begin) pushFrame(s,frames,depth,9,0,0,int(begin),f.time);
        }
        else if (d.kind == 15) extendNamedResidents(s,row,recipientMask,f.time);
        else if (d.kind == 1)
        {
            uint begin = s.removalCount;
            removeNamedResidents(s,row,f.target,f.time);
            if (s.removalCount > begin) pushFrame(s,frames,depth,9,0,0,int(begin),f.time);
        }
        else if (d.kind==26) WORLD_CLEANSE(s,row,recipientMask,f.time);
#ifdef PORTABLE_HEAL_CHARGE
        else if(d.kind==32)
        {
            uint64_t amount=takeHealCharge(s,d.owner,uint(d.targetName),row,f.time);
            if(s.error==0) { pushFrame(s,frames,depth,38,0,d.owner,int(row),f.time,recipientOrder);if(s.error==0) frames[depth].healthValue=amount; }
        }
#endif
        #ifdef PORTABLE_DAMAGE_ACCUM
        else if(d.kind==34) releaseDamageAccum(s,d,row,f,uint(depth+1));
#endif
        else if (d.kind == 33) pushFrame(s,frames,depth,2,0,d.owner,int(row),f.time);
#ifdef PORTABLE_PARENT_FIXED_DAMAGE
        else if(d.kind==3 && (d.damageFlags&262144U)!=0) enqueueParentFixed(s,d,row,f,depth);
#endif
        else if (d.kind == 3)
        { WORLD_SKILL_SCOPE_BEGIN(s)
            if (f.event != 28) s.stacks[row] = 1;
            if (d.damagePending != 0) enqueuePendingBurst(s,row,f.time);
            else
            {
                uint64_t originalCoefficient=activationDamageCoefficient(s,row);
                uint64_t coefficient=namedDamageCoefficient(s,row,originalCoefficient,f.time);
                uint hits=f64Zero(originalCoefficient) ? 0 : activationHitCount(s,row);
                if (s.error==0) pushFrame(s,frames,depth,10,0,d.owner,int(row),f.time);
                if (s.error==0)
                {
                    frames[depth].repeatLeft=hits; frames[depth].healthValue=coefficient;
#ifdef PORTABLE_PROJECTILE_CHAIN
                    frames[depth].event=uint((d.damageFlags&524288U)!=0 && !f64Zero(originalCoefficient));
#endif
                    // Native skill damage captures buffs before named-hit children.
                    // Unlike physical firing, later callbacks do not resample this gain.
                    if(hits!=0 && (s.quantityMask & 128)!=0) frames[depth].gaugeFlat=readStat(s,d.owner,S_burst_charge_speed_pct,f.time);
                }
            } WORLD_SKILL_SCOPE_END(s)
        }
        else s.error = 32;
#ifdef PORTABLE_HEALTH_SCAN_REFERENCE
        if((s.healthMask&32)==0) syncHealth(s,f.time);
#else
        // Reference/stack-derived HP flushes after all synchronous children.
        if (d.kind == 1 && (s.healthMask&32)==0) syncHealth(s,f.time);
#endif
    } while(false);
}

[noinline]
void advanceDefinitionFrame(inout Runtime s, inout Frame frames[32], inout int depth, Frame f, uint output)
{
    uint row=s.count,passive=0;
    do
    {
        if (f.mode == 1 || f.mode == 19)
        {
            if (f.cursor == 0 && f.argument >= 0 && uint(f.argument) < s.count) row = uint(f.argument);
            frames[depth].cursor++;
        }
        else if (f.repeatLeft != 0)
        { row = f.repeatRow; passive = f.repeatPassive; frames[depth].repeatLeft--; }
        else
        {
#ifndef PORTABLE_NAMED_EVENT_SCAN_REFERENCE
            // Keep the frame, health drains and work/depth accounting intact.
            // With no named-event listener for this owner, no definition can match.
            if (f.mode == 0 && f.event == 31 && (s.namedEventOwners & (1U << f.owner)) == 0)
                frames[depth].cursor = s.count;
#endif
            while (frames[depth].cursor < s.count)
            {
#ifndef PORTABLE_EVENT_SCAN_REFERENCE
                if (f.mode == 0)
                {
                    frames[depth].cursor = nextEventCandidate(s,f.event,frames[depth].cursor);
                    if (frames[depth].cursor >= s.count) break;
                }
#endif
                uint j = frames[depth].cursor++; Definition d = readDefinition(s.inputBase,j);
                if (f.mode == 2)
                {
                    if ((commands[s.inputBase+P_FORCE_BASE+uint(f.argument)*P_MASK_WORDS+j/32] & (1U << (j%32))) != 0 && activationConditions(s,j,f.time)) { row = j; break; }
                    continue;
                }
                if (f.event != 26 && d.owner != f.owner) continue;
                uint multiplicity = 0; bool matched = false;
                for (uint slot = 0; slot < d.triggerCount; slot++)
                {
                    uint at = s.inputBase+P_EVENT_BASE+j*P_EVENT_WORDS+slot*8;
                    uint event = commands[at], mode = commands[at+3]; int tag = int(commands[at+4]), stage = int(commands[at+7]);
                    if (event != f.event) continue;
                    if (event == 27 && tag != f.argument) continue;
                    if ((event == 4 || event == 41) && stage != f.argument || event == 6 && int(j) != f.argument) continue;
                    bool accumNamed=false;
#ifdef PORTABLE_DAMAGE_ACCUM
                    accumNamed=event==50;
#endif
#ifdef PORTABLE_PROJECTILE_CHAIN
                    accumNamed=accumNamed || event==51;
#endif
                    if (COUNTER_NAMED(s,event,WORLD_CONTROL_NAMED(event,(event == 9 || event == 29 || event == 30 || event == 31 || event == 48 || event == 49 || event == 59 || accumNamed))) && tag != f.argument) continue;
                    if (event == 9 && commands[at+5] != f.value) continue; WORLD_PROJECTILE_SKIP_SLOT(event,stage)
                    multiplicity++; bool ok = event != 30 || resourceModulo(f.healthValue,uint(f64ToPositiveStep(loadNumber(at+1)))) == 0;
                    if (mode != 0 || event == 7 || event == 8)
                    {
                        uint counter = j*8+slot, status;
                        uint64_t threshold64 = f64ToI64(loadNumber(at+1),1,status);
                        if (status != 0 || threshold64 == 0 || threshold64 > 0x7fffffff || s.counters[counter] == 0x7fffffff) { s.error = 2; break; }
                        uint count = WORLD_TEAM_COUNTER(s,f.event,counter), threshold = uint(threshold64);
                        if(stage==1 && triggerReductionEvent(event) && (s.quantityMask&1024)!=0)
                        {
                            uint64_t base=threshold64;
#ifdef PORTABLE_PARTIAL_CHARGE
                            if(event==40 && commands[at+5]==1) base=uint64_t(int64_t(int(commands[at+4])));
#endif
                            ok=triggerReductionCountMatches(s,j,count,base,mode,f.time);
                        }
                        else ok = mode == 2 ? count >= threshold : mode == 3 ? count == threshold : count % threshold == 0;
                    }
                    if (stage == 2 && event != 4 && event != 41) ok = false;
                    if (ok && !matched) { matched = true; passive = commands[at+6]; }
                }
                if (!matched) continue;
                row = j;
                if (f.event != 6 && multiplicity > 1)
                { frames[depth].repeatRow = j; frames[depth].repeatLeft = multiplicity-1; frames[depth].repeatPassive = passive; }
                break;
            }
        }
        if (row == s.count) { depth--; continue; }
        Definition d = readDefinition(s.inputBase,row); WORLD_TEAM_GUARD(s,row,f)
        if (f.mode == 2)
        { pushFrame(s,frames,depth,1,47,d.owner,int(row),f.time); continue; }
        if (f.mode == 0 && !activationConditions(s,row,f.time) && !(f.event == 0 && f64Less(d.duration,0) && passive != 0)) continue;
        if(d.damageRoute==10 && f.mode!=19 && d.budget>=0 &&
           (f.event!=28 || (d.flags&1)!=0 && ((s.stagedEnabled==0 || !isStaged(s,row)) || s.alive[row]==0)))
        {
            // Native checks exhaustion before resolving the budget's recipient
            // probe. Its sampled targets are discarded before actual execution.
            if(s.activations[WORLD_TEAM_BUDGET(s,row)]>=uint(d.budget)) continue;
            WORLD_RANDOM_DISCARD(s,row) if(s.error!=0) break;
        }
#ifdef PORTABLE_RANDOM_CLEANSE
        if(d.kind==26 && commands[s.inputBase+P_RECIPIENT_BASE+row*8]==20 && d.budget>=0 && (f.event!=28 || (d.flags&1)!=0 && s.alive[row]==0))
        {
            if(s.activations[WORLD_TEAM_BUDGET(s,row)]>=uint(d.budget)) continue;
            uint64_t discardedOrder;
            if(selectRecipients(s,row,f.time,discardedOrder)==0) continue;
            if(s.error!=0) break;
        }
#endif
        if(d.kind==29 && d.budget>=0)
        {
            if(s.activations[WORLD_TEAM_BUDGET(s,row)]>=uint(d.budget)) continue;
            uint64_t discardedOrder;
            if(selectRecipients(s,row,f.time,discardedOrder)==0) continue;
            if(s.error!=0) break;
        }
        if(d.kind==15 && f.event!=28 && d.budget>=0 && s.activations[WORLD_TEAM_BUDGET(s,row)]>=uint(d.budget)) continue;
        uint64_t recipientOrder=0;uint recipientMask=f.mode==19 ? uint(f.value) : d.recipients,enemyOrder=0;
        if(stackOperation(d.kind))
        {
            uint64_t order;
            if((f.event!=28 || (d.flags&1)!=0 && s.alive[row]==0) && d.budget>=0 && !stackLazySelector(s,row) && stackSelectedRecipients(s,row,f.target,f.time,true,order)==0) continue;
            recipientMask=d.kind>=19 ? stackSelectedRecipients(s,row,f.target,f.time,false,order) : 0;
        }
        if (f.mode!=19 && d.kind==22)
            recipientMask=f64Zero(d.value) ? 0 : selectRecipients(s,row,f.time,recipientOrder);
        if (f.mode!=19 && (WORLD_RELOAD_FORCE_KIND(d.kind) || d.kind == 0 || d.kind == 4 || d.kind == 5 || d.kind == 6 || d.kind == 7 || d.kind == 8 || d.kind == 13 || d.kind == 14 || d.kind == 24 || d.kind == 27 || d.kind == 31 || d.kind == 30 || d.kind==29 || d.kind==15 || d.kind==26
#ifdef PORTABLE_HEAL_CHARGE
            || d.kind==32
#endif
            ))
        {
            if(d.kind==15 && d.budget<0 && !hasDurationExtensionMembers(s,row)) recipientMask=0;
            else if (d.enemyBuff != 0 || (d.kind==15 || d.kind==26) && d.target==2)
            { recipientMask = enemyDamageMask(s,d,f.target,enemyOrder) << 5; recipientOrder = 0; }
            else if (d.lazyGroup == 0) recipientMask = selectRecipients(s,row,f.time,recipientOrder);
            else recipientMask = 0;
            uint selector = commands[s.inputBase+P_RECIPIENT_BASE+row*8];
            bool lazy = selector == 5 || selector == 6 || selector == 7 || selector == 15 || selector == 16 || selector == 19;
            if (d.budget >= 0 && recipientMask == 0 && (!lazy || d.kind==15)
#ifdef PORTABLE_HEAL_CHARGE
                && d.kind!=32
#endif
                ) continue;
        }
        uint stagedTotal=0;
        COUNTER_GUARD(s,row) bool stageRegister=s.stagedEnabled!=0 && isStaged(s,row) && (f.event!=28 || (d.flags&1)!=0 && s.alive[row]==0);
        if(stageRegister) { stagedTotal=stagedCount(s,row);if(s.error!=0) break;if(stagedTotal==0) continue; }
        if (f.mode!=19 && (f.event != 28 || (d.flags & 1) != 0 && ((s.stagedEnabled==0 || !isStaged(s,row)) || stageRegister)))
        {
            if (d.budget >= 0 && s.activations[WORLD_TEAM_BUDGET(s,row)] >= uint(d.budget)) continue;
            if (s.activations[WORLD_TEAM_BUDGET(s,row)] == 0x7fffffff) { s.error = 2; break; }
            s.activations[WORLD_TEAM_BUDGET(s,row)]++;
        }
        bool staged=s.stagedEnabled!=0 && isStaged(s,row);
        bool registering=f.event!=28 || staged && (d.flags&1)!=0 && s.alive[row]==0;
        if (!f64Zero(d.interval) && registering)
        {
            uint count=staged ? stagedTotal : 1;
            if (s.error!=0) break;
            if (staged && count==0) continue;
            bool previousCarrier=s.alive[row]!=0;
            registerTimer(s,row,f.time);
            if(staged && s.error==0) prepareStaged(s,row,count,f.time,previousCarrier);
            continue;
        }
        WORLD_FIELDS_FANOUT(s,frames,depth,d,row,f) if((d.kind==0 || d.kind==4) && d.enemyBuff!=0 && recipientMask!=0 && f.mode!=19 && (countbits(recipientMask)!=1 || s.hpPendingMask!=0 || s.hpDirtyMask!=0))
        {
            pushFrame(s,frames,depth,18,f.event,d.owner,int(row),f.time,enemyOrder);
            if(s.error==0)
            {
                frames[depth].healthValue=uint64_t(s.targetGeneration[0])|(uint64_t(s.targetGeneration[1])<<32);
                frames[depth].healthPrevious=uint64_t(s.targetGeneration[2])|(uint64_t(s.targetGeneration[3])<<32);
                frames[depth].healthNext=uint64_t(s.targetGeneration[4])|(uint64_t(s.targetGeneration[5])<<32);
                frames[depth].repeatLeft=s.targetGeneration[6];frames[depth].repeatPassive=s.targetGeneration[7];
            }
            continue;
        }
        WORLD_RELOAD_ACTIVATE(s,d,f.time) if (d.kind==35) { registerSource(s,row,f.time); continue; }
        if((WORLD_RELOAD_FORCE_KIND(d.kind) || d.kind==5 || d.kind==6 || d.kind==7 || d.kind==8 || d.kind==13 || d.kind==14 || d.kind==27 || d.kind==30 || d.kind==31) && commands[s.inputBase+P_RECIPIENT_BASE+row*8]==17)
        { pushFrame(s,frames,depth,24,0,d.owner,int(row),f.time,recipientOrder);continue; }
        applyDefinitionFrame(s,frames,depth,f,output,d,row,recipientMask,recipientOrder);
    } while(false);
}
