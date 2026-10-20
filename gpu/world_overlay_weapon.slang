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
