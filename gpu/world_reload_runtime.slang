// Absolute reload values and force requests use existing carriers, recipients,
// common binary64 arithmetic and the one shared reload lifecycle.
uint reloadHead(inout Runtime s) { return s.resourceOutput+P_WORLD_RELOAD_HEAD_BASE; }
uint reloadPolicy(uint input,uint row) { return commands[input+P_WORLD_RELOAD_INPUT_BASE+8+row]; }
[noinline]
void initializeWorldReload(inout Runtime s)
{
    uint p=s.inputBase+P_WORLD_RELOAD_INPUT_BASE;
    if(commands[p]!=0x57524c31||commands[p+1]!=1||commands[p+2]!=s.count) { s.error=64;return; }
    if(commands[p+3]>=32||commands[p+4]!=(commands[p+3]!=0 ? 0x574d5331U : 0U)) { s.error=64;return; }
    for(uint i=5;i<8;i++) if(commands[p+i]!=0) { s.error=64;return; }
    for(uint row=0;row<P_DEFINITIONS;row++)
    {
        uint flags=commands[p+8+row];if(row>=s.count) { if(flags!=0) s.error=64;continue; }
        Definition d=readDefinition(s.inputBase,row);
        if(d.kind==23)
        {
            if(flags!=2||!f64Finite(d.value)||d.stat!=0||d.enemyBuff!=0||s.combat==0||!validRecipientPlan(s.inputBase+P_RECIPIENT_BASE+row*8,false,s.inputBase)) { s.error=64;return; }
        }
        else if(d.stat==S_reload_time_fixed)
        {
            if(flags>1||d.kind!=0||d.enemyBuff!=0||!f64Finite(d.value)||s.combat==0) { s.error=64;return; }
        }
        else if(flags!=0) { s.error=64;return; }
    }
    if(s.error!=0) return;
    for(uint at=P_WORLD_RELOAD_HEAD_BASE;at<P_WORLD_RELOAD_TRACE_BASE+P_WORLD_RELOAD_TRACE_COUNT*16;at++) results[s.resourceOutput+at]=0;
    results[reloadHead(s)]=0x57524c31;
}
[noinline]
bool fixedReloadDuration(inout Runtime s,uint who,uint64_t when,out uint64_t value)
{
    bool present=false;value=0;
    for(uint pass=0;pass<s.orderedCount;pass++)
    {
        uint row=s.orderedRows[pass],definition=s.carrierDefinition[row];Definition d=residentDefinition(s,row);
        // Native _fixed_reload_time reads active target membership directly:
        // no get_buffs runtime predicate or per-recipient stack override.
        if(d.kind!=0||d.stat!=S_reload_time_fixed||reloadPolicy(s.inputBase,definition)!=1||s.alive[row]==0||!f64Less(when,s.end[row])||(s.activeRecipients[row]&(1U<<who))==0) continue;
        uint64_t next=scalarValue(s,row,d.owner);
        if(!f64Finite(next)) { s.error=16;return true; }
        if(!present||f64Less(value,next)) value=next;present=true;
    }
    return present;
}
uint appendReloadTrace(inout Runtime s,uint kind,uint who,uint64_t when)
{
    uint h=reloadHead(s),count=results[h+1];if(count>=P_WORLD_RELOAD_TRACE_COUNT) { s.error=64;return 0; }
    uint at=s.resourceOutput+P_WORLD_RELOAD_TRACE_BASE+count*16;results[h+1]=count+1;results[at]=kind;results[at+1]=who;storeNumber(at+2,when);return at;
}
void recordForcedReload(inout Runtime s,Definition d,uint64_t when)
{ uint at=appendReloadTrace(s,0,d.owner,when);if(s.error==0) results[at+4]=d.name; }
void recordWorldReload(inout Runtime s,uint who,uint64_t when,uint kind)
{
    uint at=appendReloadTrace(s,kind,who,when);if(s.error!=0) return;
    uint c=controlState(s,who);storeNumber(at+4,s.reloadUntil[who]);results[at+6]=uint(s.ammo[who]);results[at+7]=results[c+24];storeNumber(at+8,actorNumber(c+2));storeNumber(at+10,actorNumber(c+6));
}
[noinline]
void applyForcedReload(inout Runtime s,uint64_t order,uint64_t when)
{
    for(uint i=0;i<21&&s.error==0;i++)
    {
        uint encoded=(order>>(3*i))&7;if(encoded==0) break;uint who=encoded-1;
        if(f64Less(0,s.reloadUntil[who])) continue;
        // A handler between weapon ticks sees the restored base weapon. During
        // a shot callback it sees that physical shot's temporary weapon even
        // when a child already changed the logical session.
        Weapon w;w.reloadTime=s.reloadTime[who];
        int physical=s.physicalModeIndex[who];
        if(s.frameAmmoActive[who]!=0&&physical>=0) w.reloadTime=loadNumber(s.inputBase+P_MODE_BASE+uint(physical)*P_MODE_WORDS+8);
        s.ammo[who]=0;beginReload(s,w,who,when);
    }
}

// Authored owner flags only; readiness is resolved inside the shared GPU frame.
bool manualSwapEnabled(inout Runtime s,uint who)
{ return (commands[s.inputBase+P_WORLD_RELOAD_INPUT_BASE+3]&(1U<<who))!=0; }
[noinline]
bool manualSwapReady(inout Runtime s,uint who,uint64_t when)
{
    if(s.modeIndex[who]>=0) return false;
    for(uint row=0;row<s.count&&s.error==0;row++)
    {
        Definition d=readDefinition(s.inputBase,row);
        if(d.kind!=2||d.owner!=who||d.conditionCount==0) continue;
        // Native notify indexing retains duplicate timing descriptors. Readiness
        // checks conditions, not max_trigger, before the completion dispatcher.
        for(uint slot=0;slot<d.triggerCount&&s.error==0;slot++)
            if(commands[s.inputBase+P_EVENT_BASE+row*P_EVENT_WORDS+slot*8]==19&&activationConditions(s,row,when)) return true;
    }
    return false;
}
[noinline]
bool advanceManualSwap(inout Runtime s,Weapon w,uint who,uint64_t when)
{
    if(!manualSwapEnabled(s,who)||s.modeIndex[who]>=0) return false;
    if(f64Less(0,s.reloadUntil[who])&&hasInfiniteAmmo(s,who,when))
    { s.reloadUntil[who]=F64_SIGN|ONE;s.nextShot[who]=larger(s.nextShot[who],when); }
    if(!f64Less(0,s.reloadUntil[who])) s.ammo[who]=min(s.ammo[who],int(w.capacity));
    if(f64Less(0,s.reloadUntil[who])||f64Less(0,s.postReloadUntil[who])) return false;
    bool ready=manualSwapReady(s,who,when);
    if(s.error!=0) return true;
    if(!ready) return false;
    beginReload(s,w,who,when);return true;
}
