[noinline]
void worldFrameBegin(inout Runtime s,uint64_t when)
{
    if(!worldFrameEnabled(s)) return;
    WorldSchedule w=frameSchedule(s);
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
    wsBegin(w,when,actorPoolsCleared(s));s.error=w.error;
    if(s.error==0) actorPoolsSync(s,when);
#else
    wsBegin(w,when,0);s.error=w.error;
#endif
#ifdef PORTABLE_ENEMY_HEALING
    if(s.error==0) enemyHealingFrame(s,when);
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
    WORLD_STATE_DROP_GONE(s) while(cursor<end && s.error==0)
    {
        uint record=head+WS_LOG+cursor*6;cursor++;results[head+5]=cursor;
        if(results[record]!=3) continue;
        uint query=results[head+7];if(query>=1024) { s.error=2;break; }
        results[head+7]=query+1;results[head+8]=query;
        dispatch(s,8,0,0,int(0x80000000U|results[record+1]),when,output);
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
