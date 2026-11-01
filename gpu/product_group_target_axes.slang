// Shared admission of the exact BODY/PART/ADD modifier-axis descriptor.
bool validProductGroupTargetAxes(inout Runtime s)
{
    uint descriptor=s.inputBase+104408;
    if(commands[descriptor]!=0x50474131U||commands[descriptor+1]!=1||commands[descriptor+2]==0||commands[descriptor+2]>256) return false;
    for(uint i=3;i<8;i++) if(commands[descriptor+i]!=0) return false;
    if(actorPoolCount(s)==0||commands[actorBinding(s,0)]!=0) return false;
    for(uint slot=1;slot<actorPoolCount(s);slot++)
        {
            uint kind=commands[actorBinding(s,slot)];
#ifdef PORTABLE_ADD_ATTACK_BATTLE
            if(kind!=1&&kind!=5) return false;
#else
            if(kind!=1) return false;
#endif
        }
    uint count=0;
    for(uint row=0;row<256;row++)
    {
        uint axis=commands[descriptor+8+row];
        if(axis==0) continue;
        if(row>=s.count||(axis!=2&&axis!=3)) return false;
        Definition d=readDefinition(s.inputBase,row);
        if(d.kind!=4||d.stat!=0||d.enemyBuff!=0||d.healthScaling!=0||d.quantityFlags!=0||d.alliedFlags!=0||d.damageFlags!=0||!f64Finite(d.value)) return false;
        count++;
    }
    return count==commands[descriptor+2];
}

