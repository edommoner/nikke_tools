// Shared actual-shot allocation; caller supplies head/who/when/count.
    uint group=0;while(group<32&&results[agAt(s,group)]!=0) group++;
    if(group==32||results[head+1]>=0xffffffU||results[head+2]>=0x7ffffffU||results[head+10]==0&&results[head+5]>=AG_LOG_CAP) { s.error=64;return true; }
    uint at=agAt(s,group);for(uint i=0;i<AG_WORDS;i++) results[at+i]=0;
    results[at]=1;results[at+1]=who;results[at+2]=++results[head+1];results[at+3]=++results[head+2];results[at+5]=count;results[at+6]=1;storeNumber(at+8,when);results[head+3]=group+1;
