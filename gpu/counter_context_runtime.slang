// Immutable completion context points into the existing append-only ready bank.
// Event targets inherit only through canonical hit_count/counter completion
// notifications. Generic named/HP/resource notifications start without one.
bool counterContextEnabled(inout Runtime s)
{ return targetCountersEnabled(s)&&commands[s.inputBase+P_TARGET_COUNTER_INPUT_BASE+6]==2; }
uint counterContextHead(inout Runtime s) { return s.resourceOutput+P_COUNTER_CONTEXT_BASE; }
uint counterContextFrameAt(inout Runtime s,uint depth)
{ return counterContextHead(s)+72+(results[counterContextHead(s)]-1)*32+depth; }
bool beginCounterContext(inout Runtime s)
{
    if(!counterContextEnabled(s)) return true;
    uint h=counterContextHead(s),level=results[h];
    if(level==32) { s.error=1;return false; }
    results[h+8+level*2]=results[h+1];results[h]=level+1;
    return true;
}
void pushCounterContext(inout Runtime s,uint depth,uint mode,uint event)
{
    if(!counterContextEnabled(s)||s.error!=0) return;
    uint h=counterContextHead(s);
    uint parent=depth==0 ? results[h+8+(results[h]-1)*2] : results[counterContextFrameAt(s,depth-1)];
    results[counterContextFrameAt(s,depth)]=mode!=0||event==8||event==58 ? parent : 0;
}
void setCounterCompletionContext(inout Runtime s,uint depth,uint ready)
{ if(counterContextEnabled(s)&&s.error==0) results[counterContextFrameAt(s,depth)]=ready+1; }
void sampleCounterContext(inout Runtime s,uint depth)
{ if(counterContextEnabled(s)) results[counterContextHead(s)+1]=results[counterContextFrameAt(s,depth)]; }
void endCounterContext(inout Runtime s)
{
    if(!counterContextEnabled(s)) return;
    uint h=counterContextHead(s),level=results[h]-1,previous=results[h+8+level*2];
    for(uint i=0;i<32;i++) results[h+72+level*32+i]=0;
    results[h+8+level*2]=0;results[h]=level;results[h+1]=previous;
}
bool counterContextAdd(inout Runtime s,bool legacy)
{
    uint pointer=counterContextEnabled(s) ? results[counterContextHead(s)+1] : 0;
    return pointer!=0 ? results[pointer-1+5]==5 : legacy;
}
uint counterContextTarget(inout Runtime s,uint legacy)
{
    uint pointer=counterContextEnabled(s) ? results[counterContextHead(s)+1] : 0;
    if(pointer==0) return legacy;
    uint at=pointer-1,kind=results[at+5];
    if(kind==0||kind==1) return 0; // Native logical_enemy maps parts to body.
    if(kind!=5) { s.error=64;return 128; }
    for(uint slot=1;slot<actorPoolCount(s);slot++)
        if(commands[actorBinding(s,slot)]==kind&&commands[actorBinding(s,slot)+1]==results[at+6])
        {
            if(results[actorPoolAt(s,slot)]!=results[at+7]) { s.error=64;return 128; }
            return slot; // Exact dead generation remains the target.
        }
    s.error=64;return 128;
}
