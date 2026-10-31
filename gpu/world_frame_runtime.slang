void releaseWorldBossDebuffs(inout Runtime s,uint firstLog,uint lastLog)
{
    uint head=s.resourceOutput+WF_OUTPUT;
    for(uint i=firstLog;i<lastLog;i++)
    {
        uint record=head+WS_LOG+i*6;
        // Native final 'end' closes reporting only, not bound effects.
        if(results[record]!=2||results[record+2]==4) continue;
        uint p=s.inputBase+WF_PAYLOAD+results[record+1]*16,first=commands[p+4],count=commands[p+5],bound=commands[p+7];
        if(first==0||bound==0) continue;
        for(uint slot=0;slot<s.carrierCount;slot++)
        {
            uint row=s.carrierDefinition[slot];
            if(row>=first-1&&row<first-1+count&&(bound&(1U<<(row-(first-1))))!=0&&s.alive[slot]!=0) queueCarrierEnd(s,slot);
        }
    }
}
[noinline]
void worldFrameBegin(inout Runtime s,uint64_t when)
{
    if(!worldFrameEnabled(s)) return;
    WorldSchedule w=frameSchedule(s);
    uint bossFirstLog=results[w.output+2];
    // Initialization owns clock0. The first combat frame delivers its queued
    // attacks without applying another transition at the same timestamp.
    // Native app/world_frame_runtime.py enforces the same frame-once policy.
    if(f64Zero(when) && results[w.output+1]!=0)
    {
#ifdef PORTABLE_COORDINATE_SKILLS
        if(!coordinateFrameReady(s)) coordinateFrameSnapshot(s,when);
#endif
        return;
    }
#ifdef PORTABLE_WORLD_ACTOR_POOLS
#ifdef PORTABLE_ADD_ATTACK_BATTLE
    uint addAttackFirst=results[w.output+2];
#endif
    wsBegin(w,when,actorPoolsCleared(s));s.error=w.error;
    if(s.error==0)releaseWorldBossDebuffs(s,bossFirstLog,results[w.output+2]);
    if(s.error==0) actorPoolsSync(s,when);
#ifdef PORTABLE_ADD_ATTACK_BATTLE
    if(s.error==0)addAttackBattleFrame(s,when,addAttackFirst);
#endif
#ifdef PORTABLE_ENEMY_AMMO
    if(s.error==0)enemyAmmoRefresh(s,when);
#endif
#else
    wsBegin(w,when,0);s.error=w.error;
    if(s.error==0)releaseWorldBossDebuffs(s,bossFirstLog,results[w.output+2]);
#endif
#ifdef PORTABLE_ENEMY_HEALING
    if(s.error==0) enemyHealingFrame(s,when);
#endif
#ifdef PORTABLE_ENEMY_MOVEMENT
    if(s.error==0) enemyMovementFrame(s,when);
#endif
#ifdef PORTABLE_DESTRUCTIBLE_BATTLE
    if(s.error==0) destructibleBattleSync(s,when,false);
#endif
#ifdef PORTABLE_WORLD_OVERLAYS
    if(s.error==0) applyWorldOverlays(s,when);
#endif
#ifdef PORTABLE_WORLD_ACTORS
    if(s.error==0) worldActorsApply(s); WORLD_PROJECTILE_FRAME(s)
#endif
#ifdef PORTABLE_COORDINATE_SKILLS
    if(s.error==0) coordinateFrameSnapshot(s,when);
#endif
}
[noinline]
void worldFrameNotice(inout Runtime s,uint notice,uint64_t when,uint output)
{
    uint event=notice==1?34U:notice==2?31U:notice==3?35U:33U;
#ifdef PORTABLE_WORLD_ACTOR_POOLS
    if(notice==5) event=5;
#endif
    int argument=notice==2?int(commands[s.inputBase+WF_INPUT+8]-1):0;
    uint target=s.target;s.target=0;
    for(uint who=0;who<5 && s.error==0;who++) dispatch(s,0,event,who,argument,when,output);
    s.target=target;
}
#ifdef PORTABLE_PRODUCT_OUTLINED_HELPERS
[noinline]
uint worldBossDotCountBeforeAllocate(inout Runtime s) { return s.bossDotCount; }
uint worldBossDotNode(inout Runtime s,uint row)
{
    for(uint node=0;node<commands[s.inputBase+WF_INPUT+1];node++)
    {
        uint at=s.inputBase+WF_PAYLOAD+node*16,first=commands[at+4],count=commands[at+5];
        if(first!=0&&row>=first-1&&row<first-1+count)return node;
    }
    s.error=64;return 0;
}
void removeWorldBossDotClock(inout Runtime s,uint index)
{
    for(uint i=index;i+1<s.bossDotCount;i++)
    {
        s.bossDotSlot[i]=s.bossDotSlot[i+1];s.bossDotEntry[i]=s.bossDotEntry[i+1];s.bossDotRow[i]=s.bossDotRow[i+1];
        s.bossDotRecipients[i]=s.bossDotRecipients[i+1];s.bossDotStack[i]=s.bossDotStack[i+1];s.bossDotLive[i]=s.bossDotLive[i+1];
        s.bossDotActivated[i]=s.bossDotActivated[i+1];s.bossDotNext[i]=s.bossDotNext[i+1];s.bossDotExpiry[i]=s.bossDotExpiry[i+1];
    }
    s.bossDotCount--;
}
[noinline]
void worldBossDotTick(inout Runtime s,uint clock,uint who,uint64_t when,uint output)
{
    if((s.downMask&(1U<<who))!=0)return;
    Definition d=readDefinition(s.inputBase,s.bossDotRow[clock]);
    // Native ordered binary64: defense floor, coefficient, stack, incoming
    // modifier, then the minimum1. No shield/cover/decoy or received_hit path.
    uint64_t amount=larger(0,f64Add(d.fixedValue,effectiveDefense(s,who,when)^F64_SIGN));
    amount=f64Div(f64Mul(amount,d.value),HUNDRED);
    amount=f64Mul(amount,f64FromI64(s.bossDotStack[clock]));
    uint64_t received=(s.incomingMask&4)!=0?plainQuantity(s,who,S_received_dmg_pct,when):0;
    amount=larger(ONE,f64Mul(amount,larger(0,f64Add(ONE,f64Div(received,HUNDRED)))));
    if(!f64Finite(amount)){s.error=16;return;}
    uint64_t hpDamage=liveMarker(s,who,S_invincible,when)?0:amount;
    if(!f64Zero(hpDamage)&&!f64Less(hpDamage,s.hp[who])&&liveMarker(s,who,S_undying,when))hpDamage=larger(0,f64Add(s.hp[who],ONE^F64_SIGN));
    bool fell=!f64Zero(hpDamage)&&!f64Less(hpDamage,s.hp[who]);
    uint head=s.resourceOutput+WF_OUTPUT,count=results[head+6],node=worldBossDotNode(s,s.bossDotRow[clock]);
    if(s.error!=0)return;
    if(count>=2048){s.error=2;return;}
    uint hit=s.resourceOutput+WF_HITS+count*16;results[head+6]=count+1;
    for(uint i=0;i<16;i++)results[hit+i]=0;
    storeNumber(hit,when);results[hit+2]=0x80000001U|(node<<5);results[hit+3]=(who<<3)|(fell?4U:0U);
    storeNumber(hit+4,amount);storeNumber(hit+12,hpDamage);
    if(!f64Zero(hpDamage))
    {
        s.hp[who]=larger(0,f64Add(s.hp[who],hpDamage^F64_SIGN));
        if(!fell)syncHealthActor(s,who,when);
    }
    // Native sync_hp runs threshold children before SquadHitEntry snapshots
    // hp_after. A heal/max-HP grant must already be visible in this record.
    if(!fell&&!f64Zero(hpDamage)&&s.hpWatchCount!=0)dispatch(s,7,0,0,0,when,output);
    storeNumber(hit+14,s.hp[who]);
    if(fell)
    {
        // A direct down ordinal keeps queued attack logs from moving this
        // tick's down after later same-frame incoming attacks.
        uint downs=0;for(uint i=0;i<count;i++)if((results[s.resourceOutput+WF_HITS+i*16+3]&4U)!=0)downs++;
        WorldSchedule w=frameSchedule(s);wsLog(w,8,node,downs,when);s.error=w.error;
        knockDown(s,who,when);
        if(s.error==0)dispatch(s,0,38,who,0,when,output);
        if(s.error==0&&revivalEnabled(s))dispatch(s,30,0,who,0,when,output);
        else for(uint observer=0;observer<5&&s.error==0;observer++)if((s.downMask&(1U<<observer))==0)dispatch(s,0,46,observer,0,when,output);
    }
}
[noinline]
void deliverWorldBossDots(inout Runtime s,uint64_t when,uint output)
{
    if(s.bossDotEnabled==0)return;
    // Match native _dot_sched insertion order and UID identity. A recycled
    // carrier slot cannot replace a pending terminal tick of its old UID.
    for(uint i=0;i<s.bossDotCount;i++)s.bossDotLive[i]=0;
    for(uint pass=0;pass<s.orderedCount&&s.error==0;pass++)
    {
        uint slot=s.orderedRows[pass];Definition d=residentDefinition(s,slot);
        if(s.alive[slot]==0||d.owner!=5||d.stat!=S_boss_dot)continue;
        uint count=worldBossDotCountBeforeAllocate(s),i=0;while(i<count&&s.bossDotEntry[i]!=s.entryOrder[slot])i++;
        bool fresh=i==count;
        if(fresh)
        {
            if(i==P_CARRIERS){s.error=64;return;}
            s.bossDotCount=count+1;s.bossDotSlot[i]=slot;s.bossDotEntry[i]=s.entryOrder[slot];s.bossDotRow[i]=s.carrierDefinition[slot];
        }
        if(fresh||!f64Equal(s.bossDotActivated[i],s.activated[slot]))
        {s.bossDotActivated[i]=s.activated[slot];s.bossDotNext[i]=f64Add(s.activated[slot],d.interval);}
        s.bossDotExpiry[i]=s.end[slot];s.bossDotStack[i]=s.stacks[slot];s.bossDotRecipients[i]=s.activeRecipients[slot];s.bossDotLive[i]=1;
    }
    uint64_t epsilon=uint64_t(0x3e112e0bU)<<32|0xe826d695U; // exact binary64 1e-9
    for(uint i=0;i<s.bossDotCount&&s.error==0;)
    {
        bool live=s.bossDotLive[i]!=0;
        if(!live&&f64Less(when,f64Add(s.bossDotExpiry[i],epsilon^F64_SIGN)))
        {removeWorldBossDotClock(s,i);continue;}
        uint64_t next=s.bossDotNext[i],limit=f64Add(smaller(when,s.bossDotExpiry[i]),epsilon);
        uint work=0;
        while(!f64Less(limit,next)&&s.error==0)
        {
            if(work++>=2048){s.error=2;break;}
            for(uint who=0;who<5&&s.error==0;who++)if((s.bossDotRecipients[i]&(1U<<who))!=0)worldBossDotTick(s,i,who,when,output);
            uint64_t later=f64Add(next,definition_interval(s.inputBase,s.bossDotRow[i]));
            if(!f64Less(next,later)){s.error=16;break;}next=later;
        }
        // Deliberately retain the observed canonical legacy re-arming rule.
        // Its optional CPU correction is separate from GPU admission.
        if(f64Less(f64Add(s.bossDotExpiry[i],epsilon),next))removeWorldBossDotClock(s,i);
        else {s.bossDotNext[i]=next;i++;}
    }
}
#endif
[noinline]
void worldFrameDeliver(inout Runtime s,uint64_t when,uint output)
{
    if(!worldFrameEnabled(s)) return;
#ifdef PORTABLE_WORLD_ACTOR_POOLS
    actorPoolsDeliver(s,when,output);
#endif
    uint head=s.resourceOutput+WF_OUTPUT,cursor=results[head+5],end=results[head+2];
    // Native collects all opening/closing notifications before any attacks,
    // even when a later-declared node opens after an earlier node queued a shot.
    for(uint notice=cursor;notice<end && s.error==0;notice++)
    {
        uint record=head+WS_LOG+notice*6,kind=results[record];
        if(kind!=1 && kind!=2 || kind==2 && results[record+2]==4) continue;
        uint d=s.inputBase+WF_INPUT+16+results[record+1]*64,ending=kind==2?1U:0U;
#ifdef PORTABLE_WORLD_ACTOR_POOLS
        if(kind==1) actorPoolsSpawnNotice(s,results[record+1],when,output);
#endif
        uint count=commands[d+12+ending],packed=commands[d+14+ending];
        for(uint i=0;i<count && s.error==0;i++)
        { worldFrameNotice(s,(packed>>(i*3))&7,when,output);if(s.error==0) results[record+5]++; }
    }
#ifdef PORTABLE_ADD_SELF_DESTRUCT
    if(s.error==0)deliverAddSelfDestructNotices(s,when,output);
#endif
    WORLD_STATE_DROP_GONE(s)
#ifdef PORTABLE_PRODUCT_OUTLINED_HELPERS
    if(s.error==0)deliverWorldBossDots(s,when,output);
#endif
    while(cursor<end && s.error==0)
    {
        uint record=head+WS_LOG+cursor*6;cursor++;results[head+5]=cursor;
        if(results[record]!=3) continue;
#ifdef PORTABLE_ENEMY_AMMO
        if(!enemyAmmoAttempt(s,cursor-1,results[record+1],when))continue;
#endif
        uint query=results[head+7];if(query>=1024) { s.error=2;break; }
        results[head+7]=query+1;results[head+8]=query;
#ifdef PORTABLE_ADD_ATTACK_BATTLE
        uint incomingArgument=addAttackDeliveryArgument(s,cursor-1,results[record+1]);
        dispatch(s,8,0,0,int(incomingArgument),when,output);
#else
        dispatch(s,8,0,0,int(0x80000000U|results[record+1]),when,output);
#endif
        if(s.error==0) results[record+5]=query+1;
    }
}
[noinline]
void worldFrameFinish(inout Runtime s)
{
    if(!worldFrameEnabled(s) || s.error!=0) return;
    WorldSchedule w=frameSchedule(s);wsFinish(w,wsLoad(w.input+6));s.error=w.error;
#ifdef PORTABLE_WORLD_ACTOR_POOLS
    if(s.error==0) actorPoolsSync(s,wsLoad(w.input+6));
#ifdef PORTABLE_ADD_ATTACK_BATTLE
    if(s.error==0)addAttackBattleFinish(s);
#endif
#ifdef PORTABLE_ENEMY_AMMO
    if(s.error==0)enemyAmmoFinish(s);
#endif
#ifdef PORTABLE_PHYSICAL_LOCK_ARENA
    if(s.error==0) physicalLockFinalizeGraph(s);
#endif
#endif
#ifdef PORTABLE_WORLD_ACTORS
    if(s.error==0) worldActorsApply(s);
#endif
#ifdef PORTABLE_DESTRUCTIBLE_BATTLE
    if(s.error==0) destructibleBattleSync(s,wsLoad(w.input+6),true);
#endif
}

#ifdef PORTABLE_WORLD_OVERLAYS
void worldDispelLog(inout Runtime s,uint node,uint64_t when)
{ WorldSchedule w=frameSchedule(s);wsLog(w,4,node,0,when);s.error=w.error; }
#endif

void worldReviveLog(inout Runtime s,uint who,uint downs,uint64_t when)
{ WorldSchedule w=frameSchedule(s);wsLog(w,6,who,downs,when);s.error=w.error; }

void worldCoverBreakLog(inout Runtime s,uint node,uint64_t when)
{
    uint ordering=0;
#ifdef PORTABLE_COORDINATE_BURST_CONTROLS
    if(burstControls(s))
    {
        // Cover breaks before this landing can produce its down notice. The
        // explicit ordinal also preserves interleaving across multiple targets.
        uint h=s.resourceOutput+P_WORLD_FRAME_OUTPUT_BASE,downs=0;
        for(uint i=0;i<results[h+6];i++)if((results[s.resourceOutput+P_WORLD_FRAME_HIT_BASE+i*16+3]&4U)!=0)downs++;
        ordering=0x80000000U|downs;
    }
#endif
    WorldSchedule w=frameSchedule(s);wsLog(w,7,node,ordering,when);s.error=w.error;
}
