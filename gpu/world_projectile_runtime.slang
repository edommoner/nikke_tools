// One ordered scalar query for identities outside the numeric damage vector.
// Integer conversion is the same binary64 ties-to-even implementation as Python round.
void initializeProjectiles(inout Runtime s)
{
    uint head=s.resourceOutput+720912;for(uint i=0;i<16+2048*16;i++) results[head+i]=0;
    results[head]=0x57505231;
    for(uint row=0;row<s.count;row++)
    {
        Definition d=readDefinition(s.inputBase,row);
        if(d.stat!=S_pellet_count&&d.stat!=S_pellet_count_fixed&&d.stat!=S_pierce_range&&d.stat!=S_explosion_range) continue;
        if(d.kind!=0||d.enemyBuff!=0||!f64Finite(d.value)||s.combat==0) { s.error=64;return; }
    }
}
void snapshotProjectileParts(inout Runtime s)
{
    uint parts=commands[s.inputBase+P_WORLD_TEAM_INPUT_BASE+3];
    for(uint slot=1;slot<actorPoolCount(s)&&parts==0;slot++)
        if(commands[actorBinding(s,slot)]==1&&results[actorPoolAt(s,slot)+1]!=0) parts=1;
    results[s.resourceOutput+720912+3]=parts;
}
bool validProjectileResourceCondition(inout Runtime s,uint at,uint kind,uint64_t arg)
{
    if(commands[at+1]>=s.resourceCount||!f64Finite(arg)) return false;
    if(kind!=C_GAUGE_MOD) return true;
    uint step=f64ToPositiveStep(arg);return step!=0&&f64Equal(f64FromI64(step),arg);
}
void sampleProjectilePellets(inout Runtime s,uint who,uint64_t when,inout uint pellets)
{
    uint64_t fixed=plainQuantity(s,who,S_pellet_count_fixed,when);
    uint64_t value=f64Less(0,fixed)?fixed:plainQuantity(s,who,S_pellet_count,when);
    uint64_t rounded=f64Integral(value,0);
    if(!f64Finite(rounded)) { s.error=16;return; }
    bool absolute=f64Less(0,fixed);
    int floor=absolute?1:1-int(pellets),ceiling=absolute?4096:4096-int(pellets);
    if(!f64Less(f64FromI64(floor),rounded)) { pellets=1;return; }
    if(f64Less(f64FromI64(ceiling),rounded)) { s.error=64;return; }
    uint status;uint64_t converted=f64ToI64(rounded,1,status);
    if(status!=0) { s.error=2;return; }
    int64_t split=int64_t(converted)+(absolute?int64_t(0):int64_t(pellets));
    pellets=uint(split);
}
uint projectileReach(inout Runtime s,uint who,uint flags,uint64_t when,uint legacy)
{
    // Native hit_reach prioritizes explosion over pierce, even when only the
    // pierce range reaches the next step. Keep the exact binary64 threshold.
    uint64_t threshold=f64Add(HUNDRED,uint64_t(0xbe112e0b)<<32|uint64_t(0xe826d695)); // -1e-9
    if((flags&H_EXPLOSION)!=0) return !f64Less(plainQuantity(s,who,S_explosion_range,when),threshold)?4U:3U;
    if(legacy!=0) return !f64Less(plainQuantity(s,who,S_pierce_range,when),threshold)?2U:1U;
    return 0;
}
void recordProjectileShot(inout Runtime s,uint who,uint mode,uint pellets,uint muzzles,uint64_t when,uint64_t amount)
{
    uint head=s.resourceOutput+720912,count=results[head+1];
    if(count>=2048) { results[head+2]++;return; }
    uint at=head+16+count*16;results[head+1]=count+1;
    results[at]=who;results[at+1]=mode;storeNumber(at+2,when);results[at+4]=pellets;results[at+5]=muzzles;
    results[at+6]=results[s.resourceOutput+P_COUNTER_LANDING_SHOT_BASE+who*8];storeNumber(at+8,amount);
}
