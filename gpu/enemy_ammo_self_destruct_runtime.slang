// Only actual queued WS_LOG shots preceding their own same-frame retirement
// can spend the retired generation's magazine. HP/time death grants no lease.
bool enemyAmmoRetiredQueue(inout Runtime s,uint record,uint node,uint slot,uint generation,uint64_t when)
{
    uint actor=actorPoolAt(s,slot);
    if(slot==0||results[actor]!=generation||results[actor+1]!=0||results[actor+2]!=3)return false;
    uint log=s.resourceOutput+WF_OUTPUT+WS_LOG+record*6;
    if(results[log]!=3||results[log+1]!=node||actorNumber(log+3)!=when||results[log+5]!=0)return false;
    uint head=asdHead(s);
    for(uint i=0;i<results[head+1];i++)
    {
        uint at=head+ASD_HEADER+i*ASD_ROW_WORDS;
        if(results[at]!=node||results[at+1]!=slot||results[at+2]!=generation||actorNumber(at+4)!=when)continue;
        uint death=results[at+6],d=s.resourceOutput+WF_OUTPUT+WS_LOG+death*6;
        return record<death&&results[log+2]<results[at+3]&&results[at+7]==1&&
            results[d]==5&&results[d+1]==node&&results[d+2]==slot&&actorNumber(d+3)==when;
    }
    return false;
}
