// The only admitted scaled stat is charge damage. Its dependency is capacity,
// whose raw quantity readers never collect charge damage or publish a partial
// numeric dictionary. This is the native same-recipient recursion skip without
// a recursive collectStats -> ensureNativeNumeric -> collectStats call graph.
uint scaledBuffCapacity(inout Runtime s,uint who,uint64_t when)
{
    WORLD_STATE_SCOPE_BEGIN(s,0)
    int mode=s.modeIndex[who];uint capacity;
    if(mode<0 || commands[s.inputBase+P_MODE_BASE+uint(mode)*P_MODE_WORDS+21]!=0)
        capacity=rawScaledFullCapacity(s,who,s.capacity[who],true,when);
    else if(s.modeCapacityEpoch[who]==s.modeEpoch[who]) capacity=s.modeMagazine[who];
    else
    {
        uint at=s.inputBase+P_MODE_BASE+uint(mode)*P_MODE_WORDS;
        capacity=modeCapacityReference(s,uint(mode))!=0 ? referencedModeCapacity(s,who,uint(mode),when) :
            rawScaledFullCapacity(s,who,commands[at+1],commands[at+23]!=0,when);
        if(s.error==0) { s.modeMagazine[who]=capacity;s.modeCapacityEpoch[who]=s.modeEpoch[who]; }
    }
    WORLD_STATE_SCOPE_END(s)
    return capacity;
}
bool validMaxAmmoScaling(inout Runtime s,uint row,Definition d)
{
    if((d.flags&4096U)==0) return true;
    if(s.combat==0 || commands[s.inputBase+P_WORLD_FRAME_INPUT_BASE]!=0x57533031U || d.kind!=0 || d.stat!=S_charge_dmg_pct ||
       d.enemyBuff!=0 || d.healthScaling!=0 || d.alliedFlags!=0 || d.quantityFlags!=0 || d.damageFlags!=0 ||
       (d.flags&128U)!=0 || referenceScaleMode(s,row)!=0 || !f64Finite(d.value) || !f64Zero(d.interval)) return false;
    return true;
}
