// Caster camera predicates and frame-owned aim snapshots, shared by both GPUs.
bool focusAimEnabled(inout Runtime s)
{
#ifdef PORTABLE_WORLD_PROJECTILE
    return (commands[s.inputBase+P_WORLD_META_BASE+4]&~1U)==0x46414330U;
#else
    return false;
#endif
}
bool validFocusMetadata(uint input)
{
    uint tag=commands[input+P_WORLD_META_BASE+4];
#ifdef PORTABLE_WORLD_PROJECTILE
    return tag==0 || (tag&~1U)==0x46414330U;
#else
    return tag==0;
#endif
}
bool validStatePredicate(uint input,uint row,uint at,uint combat)
{
#ifndef PORTABLE_WORLD_PROJECTILE
    return false;
#else
    uint kind=commands[at];
    if(combat==0 || commands[input+P_WORLD_FRAME_INPUT_BASE]==0 ||
        commands[at+1]!=0 || !f64Zero(loadNumber(at+2))) return false;
    if(kind==C_NO_BROKEN_COVER_ALLY)
        for(uint i=0;i<definition_triggerCount(input,row);i++)
            { uint event=input+P_EVENT_BASE+row*P_EVENT_WORDS+i*8;if(commands[event]==0 && commands[event+6]!=0) return false; }
    return kind==C_NO_BROKEN_COVER_ALLY || kind==C_FOCUSING;
#endif
}
bool allAliveCovers(inout Runtime s)
{
    for(uint who=0;who<5;who++)
        if((s.downMask&(1U<<who))==0 && !f64Less(0,s.coverHP[who])) return false;
    return true;
}
uint focusCamera(inout Runtime s)
{
#ifdef PORTABLE_WORLD_OVERLAYS
    return WORLD_CONTROL_CAMERA(s,commands[s.inputBase+WO_IN+1]);
#else
    return 0;
#endif
}
// 128 means an add aim: native resolves its first surviving add at landing.
uint focusFirstAdd(inout Runtime s)
{
#ifdef PORTABLE_WORLD_ACTOR_POOLS
    uint selected=0,order=0xffffffffU;
    for(uint i=1;i<actorPoolCount(s);i++)
        if(commands[actorBinding(s,i)]==5 && results[actorPoolAt(s,i)+1]!=0 && results[actorPoolAt(s,i)+10]<order)
        { selected=i;order=results[actorPoolAt(s,i)+10]; }
    return selected;
#else
    return 0;
#endif
}
void captureFocusAims(inout Runtime s,uint64_t when)
{
#ifdef PORTABLE_WORLD_ACTOR_POOLS
    if(!focusAimEnabled(s) || !actorPoolsEnabled(s)) return;
    uint rest=focusFirstAdd(s)!=0 ? 128 : 0,lead=rest;
    bool layer2=(commands[s.inputBase+P_WORLD_META_BASE+4]&1U)!=0;
    if(layer2)
    {
        uint interrupt=0,penalty=0;
        for(uint i=1;i<actorPoolCount(s);i++) if(results[actorPoolAt(s,i)+1]!=0)
        {
            uint kind=commands[actorBinding(s,i)];
            if(kind==6 && interrupt==0) interrupt=i;
            if(kind==1 && penalty==0 && commands[actorPoolDef(s,i)+11]!=0 && f64Less(0,loadNumber(actorPoolDef(s,i)+2))) penalty=i;
        }
        lead=interrupt!=0 ? interrupt : rest!=0 ? rest : penalty;
    }
    uint camera=focusCamera(s),mask=0;uint64_t aims=0;
    if(camera==0) lead=rest;
    for(uint who=0;who<5;who++)
    {
        bool focused=(camera&(1U<<who))!=0 || s.phase==5 || liveMarker(s,who,S_focus_fire,when);
        if(focused) mask|=1U<<who;
        aims|=uint64_t(focused ? lead : rest)<<(8*who);
    }
    uint at=s.resourceOutput+P_FOCUS_STATE_BASE;storeNumber(at,aims);results[at+2]=camera;
    results[at+3]=uint(s.phase==5);results[at+4]++;results[at+5]=mask;
    results[at+6]=0x46414331U;
#endif
}

// Numeric dictionary queries cache camera eligibility for this exact query
// time, target and exclusion, until the shared carrier/value epoch changes.
bool focusNumericEnabled(inout Runtime s)
{
#ifdef PORTABLE_WORLD_PROJECTILE
    return (s.incomingMask&128U)!=0;
#else
    return false;
#endif
}
void initializeFocusState(inout Runtime s)
{
#ifdef PORTABLE_WORLD_PROJECTILE
    initializeInterruptAimDiagnostics(s); // After recipient/counter tail clearing.
    bool numeric=false;
    for(uint row=0;row<s.count;row++) for(uint i=0;i<definition_conditionCount(s.inputBase,row);i++)
        numeric |= commands[s.inputBase+P_CONDITION_BASE+row*P_CONDITION_WORDS+i*4]==C_FOCUSING;
    if(!numeric && !focusAimEnabled(s)) return;
    for(uint i=0;i<P_FOCUS_STATE_WORDS;i++) results[s.resourceOutput+P_FOCUS_STATE_BASE+i]=0;
    results[s.resourceOutput+P_FOCUS_STATE_BASE+8]=uint(numeric);
    if(numeric) s.incomingMask|=128U;
#endif
}
void invalidateFocusNumeric(inout Runtime s)
{
    invalidateNativeNumeric(s);
    if(!focusNumericEnabled(s)) return;
    uint at=s.resourceOutput+P_FOCUS_STATE_BASE;
    if(results[at+17]==0xffffffffU) { s.error=2;return; }
    results[at+17]++;results[at+16]=0;
}
void beginFocusNumeric(inout Runtime s,uint who,uint64_t when)
{
    if(!focusNumericEnabled(s)) return;
    uint head=s.resourceOutput+P_FOCUS_STATE_BASE;
    uint64_t prior=uint64_t(results[head+18])|(uint64_t(results[head+19])<<32);
    if(results[head+20]==0 || !f64Equal(prior,when))
    { results[head+16]=0;storeNumber(head+18,when);results[head+20]=1; }
    uint target=s.target;
#ifdef PORTABLE_WORLD_ACTOR_POOLS
    if((target&ACTOR_REF)!=0) target&=127U;
#endif
    uint key=who|(s.damageExclusion<<3),count=results[head+16],epoch=results[head+17];
    for(uint i=0;i<count;i++)
    {
        uint at=head+32+i*8;
        if(results[at]==key && results[at+1]==target && results[at+4]==epoch)
        { results[head+9]=results[at+5];return; }
    }
    if(count==P_FOCUS_CACHE_COUNT) { s.error=64;return; }
    uint at=head+32+count*8,camera=focusCamera(s);results[head+16]=count+1;
    results[at]=key;results[at+1]=target;storeNumber(at+2,when);
    results[at+4]=epoch;results[at+5]=camera;results[at+6]=0;results[at+7]=1;
    results[head+9]=camera;
}
uint predicateFocusCamera(inout Runtime s,uint definition)
{
    return s.queryActive!=0 && definition_queryResolve(s.inputBase,definition)!=0 && focusNumericEnabled(s)
        ? results[s.resourceOutput+P_FOCUS_STATE_BASE+9] : focusCamera(s);
}
