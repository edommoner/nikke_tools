// Explicit visible-with-moving-owner-v1; typed HP/lifetime remain in DT.
uint movingTypedOwnerSlot(inout Runtime s,uint typed)
{
    uint binding=DF_EXTRA(s)+2328+typed*12,kind=commands[binding+5],identity=commands[binding+6];
    if(kind==0)return 0;
    for(uint slot=1;slot<actorPoolCount(s);slot++)
        if(commands[actorBinding(s,slot)]==kind&&commands[actorBinding(s,slot)+1]==identity)return slot;
    return 128;
}
bool initializeMovingTypedGeometry(inout Runtime s)
{
    uint p=DF_EXTRA(s);
    if(!coordinateTypedWeapons(s)||!typedAimEnabled(s)||commands[p+12]!=3||commands[p+15]!=2)return false;
    for(uint typed=0;typed<commands[p+2];typed++)
    {
        uint slot=movingTypedOwnerSlot(s,typed);if(slot>=actorPoolCount(s))return false;
        if(slot!=0&&lagShape(s,slot)==0)return false;
    }
    return true;
}
bool movingTypedVisible(inout Runtime s,uint typed)
{
    uint slot=movingTypedOwnerSlot(s,typed);if(slot==0)return true;
    if(slot>=actorPoolCount(s)){s.error=64;return false;}
    uint actor=actorPoolAt(s,slot),binding=DF_EXTRA(s)+2328+typed*12;
    return results[actor+1]!=0&&results[actor]==commands[binding+7];
}
uint64_t movingTypedCenter(inout Runtime s,uint typed,uint axis)
{
    uint row=DF_EXTRA(s)+16+typed*18,slot=movingTypedOwnerSlot(s,typed);
    uint64_t literal=cNumber(row+2+axis*2);if(slot==0)return literal;
    if(slot>=actorPoolCount(s)){s.error=64;return 0;}
    uint st=emState(s,slot),shape=lagShape(s,slot),binding=DF_EXTRA(s)+2328+typed*12;
    if(shape==0||results[st+8]==0||results[st]!=commands[binding+7]){s.error=64;return 0;}
    uint64_t delta=f64Add(actorNumber(st+4+axis*2),cNumber(shape+8+axis*2)^F64_SIGN),value=f64Add(literal,delta);
    if(!f64Finite(value)){s.error=16;return 0;}return value;
}
void movingTypedAimStore(inout Runtime s,uint typed)
{
    uint at=s.resourceOutput+TMR_AIM_BASE+typed*4;
    storeNumber(at,movingTypedCenter(s,typed,0));storeNumber(at+2,movingTypedCenter(s,typed,1));
}
