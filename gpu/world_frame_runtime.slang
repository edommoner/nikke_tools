[noinline]
void worldFrameBegin(inout Runtime s,uint64_t when)
{
    if(!worldFrameEnabled(s)) return;
    WorldSchedule w=frameSchedule(s);wsBegin(w,when,0);s.error=w.error;
}
[noinline]
void worldFrameDeliver(inout Runtime s,uint64_t when,uint output)
{
    if(!worldFrameEnabled(s)) return;
    uint head=s.resourceOutput+WF_OUTPUT,cursor=results[head+5],end=results[head+2];
    while(cursor<end && s.error==0)
    {
        uint record=head+WS_LOG+cursor*6;cursor++;results[head+5]=cursor;
        if(results[record]!=3) continue;
        uint query=results[head+7];if(query>=1024) { s.error=2;break; }
        results[head+7]=query+1;results[head+8]=query;
        dispatch(s,8,0,0,int(0x80000000U|results[record+1]),when,output);
        if(s.error==0) results[record+5]=query+1;
    }
}
[noinline]
void worldFrameFinish(inout Runtime s)
{
    if(!worldFrameEnabled(s) || s.error!=0) return;
    WorldSchedule w=frameSchedule(s);wsFinish(w,wsLoad(w.input+6));s.error=w.error;
}
