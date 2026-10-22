// Private, versioned38-word receipt. Legacy periodic snapshots are untouched.
// Order uses128*7 bits, leaving four words for generated interrupt metadata.
static const uint INTERRUPT_PACKET_TAG=0x49525001U;
uint interruptPacketSlot(uint at,uint index)
{
    uint bit=index*7,word=at+6+bit/32,shift=bit%32;
    uint value=results[word]>>shift;
    if(shift>25) value|=results[word+1]<<(32-shift);
    return value&127U;
}
bool validInterruptPacket(uint at)
{
    uint tag=results[at+37],count=results[at];
    if((tag!=INTERRUPT_PACKET_TAG&&tag!=(INTERRUPT_PACKET_TAG|2U))||count>128||results[at+36]>4) return false;
    bool frozen=(tag&2U)!=0;
    if(!frozen&&(count!=0||results[at+1]!=0)) return false;
    uint seen[4];for(uint i=0;i<4;i++) seen[i]=0;
    for(uint i=0;i<128;i++)
    {
        uint slot=interruptPacketSlot(at,i);
        if(i>=count) { if(slot!=0) return false;continue; }
        uint mask=1U<<(slot%32);
        if((seen[slot/32]&mask)!=0) return false;
        seen[slot/32]|=mask;
    }
    for(uint i=0;i<4;i++) if(seen[i]!=results[at+2+i]) return false;
    return true;
}
bool storeInterruptPacket(uint at,uint order[128],uint count,uint birth,uint low,uint high,uint reach,bool frozen)
{
    if(count>128||reach>4||!frozen&&(count!=0||birth!=0)) return false;
    uint seen[4];for(uint i=0;i<4;i++) seen[i]=0;
    for(uint i=0;i<count;i++)
    {
        uint slot=order[i];if(slot>=128) return false;
        uint mask=1U<<(slot%32);if((seen[slot/32]&mask)!=0) return false;seen[slot/32]|=mask;
    }
    // Validate before touching a reused packet, including its suffix.
    for(uint i=0;i<38;i++) results[at+i]=0;
    results[at]=count;results[at+1]=birth;
    for(uint i=0;i<4;i++) results[at+2+i]=seen[i];
    for(uint i=0;i<count;i++)
    {
        uint bit=i*7,shift=bit%32,word=at+6+bit/32,slot=order[i];
        results[word]|=slot<<shift;
        if(shift>25) results[word+1]|=slot>>(32-shift);
    }
    results[at+34]=low;results[at+35]=high;results[at+36]=reach;
    results[at+37]=INTERRUPT_PACKET_TAG|(frozen?2U:0U);
    return true;
}
