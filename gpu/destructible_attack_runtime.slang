// Caller owns scratch for 128 frozen (slot,kind,id,generation) rows and one
// existing impact packet. Reuses world landing and existing collector/DFS.
uint dwAttackProjectiles(inout Runtime s,inout WorldSchedule w,uint bindings,uint count,uint base,uint header,uint frozen,uint packet,uint who,uint family,uint outcome,uint attackId,uint64_t amount,uint64_t credit,uint64_t when,uint output,uint answer)
{
    if(w.error!=0||s.error!=0) return 0;
    if(count==0||count>128||who>=5||family>=4||attackId>=0x1000000U||outcome>2||!dtQuantity(amount)||!dtQuantity(credit)||outcome!=2&&!f64Zero(amount)||outcome==0&&!f64Zero(credit)||results[header+2]==0||results[header+3]!=0||!f64Equal(dtNumber(header),when))
    { w.error=64;return 0; }
    uint selected=0;
    for(uint slot=0;slot<count;slot++)
    {
        uint at=dtAt(base,slot);
        if(results[at+3]!=0&&results[at]==2)
        { uint p=frozen+selected*4;results[p]=slot;results[p+1]=2;results[p+2]=results[at+1];results[p+3]=results[at+2];selected++; }
    }
    results[answer]=selected;
    for(uint i=0;i<selected&&w.error==0&&s.error==0;i++)
    {
        uint p=frozen+i*4,slot=results[p],kind=results[p+1],identity=results[p+2],generation=results[p+3];
        DWReceipt r=dwLand(w,base,count,header,slot,kind,identity,generation,outcome,amount,credit,when);
        uint a=answer+1+i*8;results[a]=slot;results[a+1]=kind;results[a+2]=identity;results[a+3]=generation;results[a+4]=r.delivered;results[a+5]=r.broken;dtStore(a+6,r.took);
        if(w.error==0) dwPublishImpact(s,r,packet,who,family,outcome,attackId,kind,identity,generation,amount,credit,when,output);
    }
    return selected;
}
