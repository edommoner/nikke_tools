// GPU-owned lost definitions and global (allied-selector) RNG; no private arrays.
bool revivalEnabled(inout Runtime s) { return (s.quantityMask&262144U)!=0; }
uint revivalAt(inout Runtime s) { return s.resourceOutput+P_REVIVAL_BASE; }
bool revivalNullHP(inout Runtime s,uint who)
{
#ifdef PORTABLE_WORLD_PROJECTILE
    return revivalEnabled(s) && (results[revivalAt(s)+5]&(1U<<who))!=0;
#else
    return false;
#endif
}
void revivalClearNull(inout Runtime s,uint who)
{
#ifdef PORTABLE_WORLD_PROJECTILE
    if(revivalEnabled(s)) results[revivalAt(s)+5]&=~(1U<<who);
#endif
}
void revivalRecord(inout Runtime s,uint kind,uint who,uint64_t when,uint ammo)
{
#ifdef PORTABLE_WORLD_PROJECTILE
    if(!revivalEnabled(s)) return;
    uint index=results[revivalAt(s)+6]++;
    uint history=s.resourceOutput+P_ORDERED_HISTORY_BASE;
    uint at=orderedHistoryRecordAt(s.resourceOutput+P_REVIVAL_TRACE_BASE,history,index,nativeNumericEnabled(s));
    if(at==0xffffffffU) { s.error=64;return; }
    if(kind==1) results[revivalAt(s)+7]++;
    results[at]=kind;results[at+1]=who;storeNumber(at+2,when);storeNumber(at+4,s.hp[who]);results[at+6]=ammo;
    results[at+7]=0;
    if(!orderedHistoryRecordDone(history,index,at)) s.error=64;
#endif
}
bool initializeRevival(inout Runtime s)
{
    bool enabled=false,seeded=false,friendly=false;uint64_t seed=19;
    if(alliedRandomEnabled(s))
    {
#ifndef PORTABLE_WORLD_PROJECTILE
        return false;
#else
        if(s.combat==0 || !worldFrameEnabled(s)) return false;
        uint at=s.inputBase+P_RECIPIENT_META_BASE;
        seed=uint64_t(commands[at+3])|(uint64_t(commands[at+4])<<32);seeded=true;
#endif
    }
    for(uint row=0;row<s.count;row++)
    {
        Definition d=readDefinition(s.inputBase,row);
        if((d.flags&2048U)!=0)
        {
#ifndef PORTABLE_WORLD_PROJECTILE
            return false;
#else
            if(s.combat==0 || d.kind!=4 || d.enemyBuff!=0) return false;
            enabled=true;
#endif
        }
        if((d.flags&1024U)!=0)
        {
#ifndef PORTABLE_WORLD_PROJECTILE
            return false;
#else
            if(s.combat==0 || !(d.kind==0 || d.kind==4 && (d.flags&2048U)!=0) || d.enemyBuff!=0) return false;
            enabled=true;
#endif
        }
        uint plan=s.inputBase+P_RECIPIENT_BASE+row*8;
        uint leaves=commands[plan]==17 ? commands[plan+1] : 1;
        if(commands[plan]==17 && (leaves>21 || commands[plan+2]>P_RECIPIENT_NODES || leaves>P_RECIPIENT_NODES-commands[plan+2])) return false;
        for(uint leaf=0;leaf<leaves;leaf++)
        {
            uint selector=commands[commands[plan]==17 ? s.inputBase+P_RECIPIENT_NODE_BASE+(commands[plan+2]+leaf)*8 : plan];
            if((selector==22 || selector==23) && d.kind!=29) return false;
            if(selector==19 || selector==25)
            {
                friendly=true;
                if(!alliedRandomEnabled(s) || (d.kind==0 || d.kind==4) && (commands[plan]==17 || (selector==19 ? d.lazyGroup==0 : d.lazyGroup!=0))) return false;
            }
        }
        if(d.kind!=29) { if(commands[s.inputBase+P_MODE_BASE+row*P_MODE_WORDS]==P_REVIVAL_MAGIC) return false;continue; }
#ifndef PORTABLE_WORLD_PROJECTILE
        return false;
#else
        uint at=s.inputBase+P_MODE_BASE+row*P_MODE_WORDS;
        if(s.combat==0 || !worldFrameEnabled(s) || d.stat!=0 || d.enemyBuff!=0 || d.quantityFlags!=0 || d.healthScaling!=0 || d.alliedFlags!=0 || d.damageFlags!=0 || !f64Finite(d.value) || !f64Less(0,d.value) || !f64Zero(d.interval) || commands[at]!=P_REVIVAL_MAGIC || commands[at+3]!=0) return false;
        for(uint word=4;word<28;word++) if(commands[at+word]!=0) return false;
        uint64_t next=uint64_t(commands[at+1])|(uint64_t(commands[at+2])<<32);
        if(seeded && next!=seed) return false;
        seed=next;seeded=true;enabled=true;
#endif
    }
#ifdef PORTABLE_WORLD_PROJECTILE
    if(commands[s.inputBase+P_RECIPIENT_META_BASE+1]!=uint(enabled) || alliedRandomEnabled(s)!=friendly) return false;
    if(enabled || friendly)
    {
        if(enabled) s.quantityMask|=262144U;
        for(uint word=0;word<P_REVIVAL_WORDS;word++) results[revivalAt(s)+word]=0;
        mtSeed(s.resourceOutput+P_REVIVAL_RNG_BASE,seed);
    }
#endif
    return true;
}
void revivalRemember(inout Runtime s,uint who,uint slot)
{
#ifdef PORTABLE_WORLD_PROJECTILE
    if(!revivalEnabled(s) || s.end[slot]!=F64_INF) return;
    uint index=results[revivalAt(s)+who]++;
    if(index>=P_CARRIERS) { s.error=64;return; }
    results[s.resourceOutput+P_REVIVAL_LOST_BASE+who*P_CARRIERS+index]=s.carrierDefinition[slot];
#endif
}
// Called by the existing DFS; child activation finishes before the next lost row.
void advanceRevival(inout Runtime s,inout Frame frames[32],inout int depth)
{
#ifdef PORTABLE_WORLD_PROJECTILE
    Frame f=frames[depth];uint who=f.owner,bit=1U<<who,base=revivalAt(s);
    if(f.mode==28)
    {
        uint encoded=f.cursor<21 ? uint(f.value>>(f.cursor*3))&7 : 0;
        if(encoded==0) { depth--;return; }
        frames[depth].cursor++;
        if((s.downMask&(1U<<(encoded-1)))==0) return;
        pushFrame(s,frames,depth,29,0,encoded-1,f.argument,f.time,f.healthValue);return;
    }
    if(f.event==0)
    {
        s.downMask&=~bit;results[base+5]|=bit;s.hpPendingMask&=~bit;s.hpDirtyMask&=~bit;
        frames[depth].event=1;frames[depth].cursor=0;return;
    }
    while(frames[depth].cursor<results[base+who])
    {
        uint index=frames[depth].cursor++,row=results[s.resourceOutput+P_REVIVAL_LOST_BASE+who*P_CARRIERS+index];
        Definition d=readDefinition(s.inputBase,row);
        if(!(d.kind==0 || d.kind==4 && (d.flags&2048U)!=0) || d.bulletDuration!=0) continue;
        bool startup=false,passive=false;
        for(uint slot=0;slot<d.triggerCount;slot++)
        { uint at=s.inputBase+P_EVENT_BASE+row*P_EVENT_WORDS+slot*8;if(commands[at]==0) { startup=true;passive|=commands[at+6]!=0; } }
        if(!startup) continue;
        uint resident=P_CARRIERS;
        for(uint i=0;i<s.orderedCount;i++) { uint slot=s.orderedRows[i];if(s.alive[slot]!=0 && s.carrierDefinition[slot]==row) { resident=slot;break; } }
        if(resident!=P_CARRIERS)
        {
            if(s.lazyPending[resident]!=0 || (s.activeRecipients[resident]&bit)!=0 || d.lazyGroup!=0) continue;
            uint64_t order=carrierOrder(s,resident);uint shift=0;for(uint64_t rest=order;rest!=0;rest>>=3) shift+=3;
            if(shift>=63) { s.error=64;return; }
            s.activeRecipients[resident]|=bit;storeCarrierOrder(s,resident,order|(uint64_t(who+1)<<shift));
            continue;
        }
        if((s.downMask&(1U<<d.owner))!=0) continue;
        bool ok=activationConditions(s,row,f.time);
        if(!ok && (!passive || !f64Less(d.duration,0))) continue;
        pushFrame(s,frames,depth,1,47,d.owner,int(row),f.time);return;
    }
    uint64_t maximum=effectiveMaxHP(s,who,f.time);
    s.hp[who]=f64Div(f64Mul(maximum,f.value),HUNDRED);results[base+5]|=bit;
    syncHealthActor(s,who,f.time);
    results[base+who]=0;
    s.charging[who]=0;s.reloadUntil[who]=F64_SIGN|ONE;s.postReloadUntil[who]=F64_SIGN|ONE;s.pendingAutoReload[who]=0;
    s.modeIndex[who]=-1;s.physicalModeIndex[who]=-2;s.modeEpoch[who]++;s.appliedEpoch[who]=s.modeEpoch[who];s.modeEntryUntil[who]=F64_SIGN|ONE;s.modeEntryPhase[who]=0;
    WORLD_CONTROL_RELOAD(s,who)
    s.ammo[who]=int(fullCapacity(s,who,s.capacity[who],true,f.time));s.nextShot[who]=f.time;s.weaponInitialized[who]=1;
    revivalRecord(s,2,who,f.time,uint(s.ammo[who]));
    worldReviveLog(s,who,results[base+7],f.time);depth--;
#else
    s.error=64;
#endif
}
