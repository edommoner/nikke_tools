// Native automatic vanish pause:discard debt,reload partial magazines,and
// cool warmup only by actual non-firing time. Static camera input belongs to
// the authored control descriptor;dynamic control is still a separate stage.
bool worldPauseWeapon(inout Runtime s,Weapon w,uint who,uint64_t when)
{
    if(!worldOverlayEnabled(s)) return false;
    uint at=s.resourceOutput+WO_OUT+288+who*8;
    if(!worldVanish(s) || w.mode==1 || (commands[s.inputBase+WO_IN+1]&(1U<<who))!=0)
    { results[at+6]=0;return false; }
    if(w.mode==2)
    {
        if(results[at+6]==0)
        {
            results[at+6]=1;storeNumber(at,s.warm[who]);storeNumber(at+2,when);
            storeNumber(at+4,larger(0,f64Add(f64Add(when,s.lastFire[who]^F64_SIGN),s.lastInterval[who]^F64_SIGN)));
        }
        uint64_t idle=f64Add(woRead(at+4),f64Add(when,woRead(at+2)^F64_SIGN));
        s.warm[who]=larger(0,f64Add(woRead(at),f64Mul(f64Div(w.warmLimit,w.coolTime),idle)^F64_SIGN));
        s.lastFire[who]=when;
    }
    s.nextShot[who]=larger(s.nextShot[who],f64Add(when,uint64_t(0x3f911111)<<32|0x11111111));
    if(f64Less(s.reloadUntil[who],0) && s.ammo[who]<int(w.capacity) && w.infinite==0) beginReload(s,w,who,when);
    return true;
}

// Literal character policy only;all return times and charge latches are GPU-owned.
bool worldChargePolicy(inout Runtime s,uint who)
{ return worldOverlayEnabled(s) && (commands[s.inputBase+WO_IN+7]&(1U<<who))!=0; }
void worldChargeReset(inout Runtime s,uint who)
{
    if(!worldChargePolicy(s,who)) return;
    uint at=s.resourceOutput+WO_OUT+328+who*8;
    for(uint i=0;i<8;i++) results[at+i]=0;
}
bool worldVanishReturn(inout Runtime s,out uint64_t returnAt)
{
    returnAt=0;uint count=commands[s.inputBase+P_WORLD_FRAME_INPUT_BASE+1];
    for(uint n=0;n<count;n++)
    {
        if(commands[woNode(s,n)]!=6 || results[woGraphState(s,n)]==0) continue;
        uint d=s.inputBase+P_WORLD_FRAME_INPUT_BASE+16+n*64;
        if(commands[d+1]!=1 || commands[d+11]!=0) return false;
        returnAt=larger(returnAt,f64Add(woRead(woGraphState(s,n)+2),loadNumber(d+4)));
    }
    return true;
}
bool worldChargeHold(inout Runtime s,Weapon w,uint who,uint64_t when)
{
    if(!worldChargePolicy(s,who) || s.error!=0) return false;
    uint at=s.resourceOutput+WO_OUT+328+who*8;
    if((results[at]&1)==0)
    {
        if(f64Less(when,s.chargeUntil[who])) return false;
        results[at]=1;storeNumber(at+2,s.chargeUntil[who]);storeNumber(at+6,when);
    }
    s.chargeUntil[who]=woRead(at+2); // Full charge stays latched across buff expiry.
    if(worldVanish(s))
    {
        uint64_t returnAt;bool known=worldVanishReturn(s,returnAt);uint64_t two=f64FromI64(2);
        if(!known || !f64Less(two,f64Add(returnAt,when^F64_SIGN)))
        {
            if((results[at]&2)==0) { results[at]|=2;storeNumber(at+4,f64Add(when,two)); }
            if(f64Less(when,woRead(at+4))) return true;
        }
    }
    results[at]&=~2U;return false;
}
