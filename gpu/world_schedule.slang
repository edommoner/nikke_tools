// Shared pattern-graph clock. Caller supplies authored descriptors and GPU-owned
// cleared state; no CPU-generated open/close/shot schedule is consumed.
static const uint WS_NODES=32, WS_EDGES=8, WS_NODE_WORDS=64, WS_STATE_WORDS=24;
static const uint WS_HISTORY=784, WS_HISTORY_CAP=512, WS_LOG=2832, WS_LOG_CAP=2048;
static const uint WS_SNAP=15120;
static const uint64_t WS_EPS=uint64_t(0x3e112e0b)<<32|0xe826d695; // 1e-9
struct WorldSchedule { uint input, output, count, error; };
uint64_t wsLoad(uint at) { return uint64_t(commands[at])|uint64_t(commands[at+1])<<32; }
uint64_t wsRead(uint at) { return uint64_t(results[at])|uint64_t(results[at+1])<<32; }
void wsStore(uint at,uint64_t v) { results[at]=uint(v);results[at+1]=uint(v>>32); }
uint wsNode(WorldSchedule w,uint n) { return w.input+16+n*WS_NODE_WORDS; }
uint wsState(WorldSchedule w,uint n) { return w.output+16+n*WS_STATE_WORDS; }
bool wsReached(uint64_t now,uint64_t due) { return !f64Less(now,f64Add(due,WS_EPS^F64_SIGN)); }
[noinline]
bool wsValidate(WorldSchedule w)
{
    if(w.count==0 || w.count>32) return false;
    uint reachable=0;
    for(uint n=0;n<32;n++)
    {
        uint d=wsNode(w,n);
        if(n>=w.count) { for(uint j=0;j<64;j++) if(commands[d+j]!=0) return false;continue; }
        uint flags=commands[d+1],ac=commands[d+10],uc=commands[d+11];
        if(commands[d]>0x7fffffff || flags>3 || ac==0 || ac>8 || uc>8 || commands[d+6]>0x7fffffff || commands[d+7]!=0) return false;
#ifdef PORTABLE_WORLD_FRAME
        for(uint j=0;j<2;j++)
        {
            uint count=commands[d+12+j],packed=commands[d+14+j];
            if(count>8 || (packed>>(count*3))!=0) return false;
            for(uint i=0;i<count;i++) { uint event=(packed>>(i*3))&7;if(event==0 || event>4) return false; }
        }
#else
        for(uint j=12;j<16;j++) if(commands[d+j]!=0) return false;
#endif
        for(uint j=56;j<64;j++) if(commands[d+j]!=0) return false;
        uint64_t delay=wsLoad(d+2),until=wsLoad(d+4),interval=wsLoad(d+8);
        if(!f64Finite(delay) || f64Less(delay,0) || !f64Finite(until) || !f64Finite(interval) || f64Less(interval,0)) return false;
        if((flags&1)!=0 ? f64Zero(until)||f64Less(until,0) : !f64Zero(until)) return false;
        if(commands[d+6]==0 && !f64Zero(interval)) return false;
        for(uint e=0;e<8;e++)
        {
            uint a=d+16+e*2,node=commands[a],outcome=commands[a+1];
            if(e>=ac) { if(node!=0 || outcome!=0) return false; }
            else
            {
                if(node>=w.count && node!=32 || outcome>3 || node==32 && outcome!=0) return false;
                if(node==32) reachable|=1U<<n;
                else if(outcome!=0)
                {
                    uint source=wsNode(w,node);
                    if(outcome==1 && (commands[source+1]&2)==0 || outcome==2 && (commands[source+1]&1)==0 || outcome==3 && commands[source+11]==0) return false;
                }
            }
            uint u=d+32+e*3;node=commands[u];uint64_t wait=wsLoad(u+1);
            if(e>=uc) { if(node!=0 || !f64Zero(wait)) return false; }
            else if(node>=w.count || node==n || !f64Finite(wait) || f64Less(wait,0)) return false;
        }
    }
    for(uint pass=0;pass<32;pass++) for(uint n=0;n<w.count;n++)
    {
        uint d=wsNode(w,n);
        for(uint e=0;e<commands[d+10];e++) { uint source=commands[d+16+e*2];if(source<32 && (reachable&(1U<<source))!=0) reachable|=1U<<n; }
    }
    return reachable==(w.count==32?0xffffffffU:(1U<<w.count)-1);
}
[noinline]
void wsLog(inout WorldSchedule w,uint kind,uint node,uint arg,uint64_t time)
{
    uint count=results[w.output+2];if(count>=WS_LOG_CAP) { w.error=2;return; }
    uint at=w.output+WS_LOG+count*6;results[at]=kind;results[at+1]=node;results[at+2]=arg;wsStore(at+3,time);results[w.output+2]=count+1;
}
[noinline]
void wsEnd(inout WorldSchedule w,uint node,uint outcome,uint64_t time)
{
    uint count=results[w.output+1];if(count>=WS_HISTORY_CAP) { w.error=2;return; }
    uint at=w.output+WS_HISTORY+count*4;results[at]=node;results[at+1]=outcome;wsStore(at+2,time);results[w.output+1]=count+1;
}
[noinline]
uint wsMatches(WorldSchedule w,uint node,uint outcome,uint index,out uint64_t time)
{
    uint count=0;time=0;
    for(uint i=0;i<results[w.output+1];i++)
    {
        uint at=w.output+WS_HISTORY+i*4;
        if(results[at]==node && (outcome==0 || results[at+1]==outcome))
        { if(count==index) time=wsRead(at+2);count++; }
    }
    return count;
}
[noinline]
void wsClose(inout WorldSchedule w,uint n,uint outcome,uint64_t time)
{
    wsEnd(w,n,outcome,time);if(w.error!=0) return;
    results[wsState(w,n)]=0;wsLog(w,2,n,outcome,time);
}
[noinline]
void wsOpen(inout WorldSchedule w,uint n,uint trigger,uint64_t time)
{
    uint d=wsNode(w,n),s=wsState(w,n);results[s]=1;results[s+1]++;wsStore(s+2,time);results[s+4]=0;results[s+6]=0;
    uint64_t ignored;
    for(uint e=0;e<commands[d+10];e++) results[s+8+e]=wsMatches(w,commands[d+16+e*2],commands[d+17+e*2],0,ignored);
    for(uint e=0;e<commands[d+11];e++) results[s+16+e]=wsMatches(w,commands[d+32+e*3],0,0,ignored);
    wsLog(w,1,n,trigger,time);
}
[noinline]
void wsBegin(inout WorldSchedule w,uint64_t time,uint clearedMask)
{
    if(results[w.output+1]==0) wsEnd(w,32,0,time);
    for(uint n=0;n<w.count;n++)
    {
        uint s=wsState(w,n),d=wsNode(w,n);results[s+5]=0;
        if(results[s]==0) continue;
        if((clearedMask&(1U<<n))!=0) results[s+6]=1;
        if((commands[d+1]&2)!=0 && results[s+6]!=0) results[s+5]=1;
        else if((commands[d+1]&1)!=0 && wsReached(time,f64Add(wsRead(s+2),wsLoad(d+4)))) results[s+5]=2;
    }
    // Propagate same-frame following to a fixed point. A cleared reason wins;
    // followed wins over expiration, independently of descriptor declaration order.
    for(uint pass=0;pass<32;pass++)
    {
        bool grew=false;
        for(uint n=0;n<w.count;n++)
        {
            uint s=wsState(w,n),d=wsNode(w,n);
            if(results[s]==0 || results[s+5]==1 || results[s+5]==3) continue;
            for(uint e=0;e<commands[d+11];e++)
            {
                uint at=d+32+e*3,source=commands[at],k=results[s+16+e];uint64_t ended;
                uint count=wsMatches(w,source,0,k,ended);
                if(count<=k) { if(results[wsState(w,source)+5]==0) continue;ended=time; }
                if(wsReached(time,f64Add(ended,wsLoad(at+1)))) { results[s+5]=3;grew=true;break; }
            }
        }
        if(!grew) break;
    }
    for(uint n=0;n<w.count && w.error==0;n++)
    { uint s=wsState(w,n),reason=results[s+5];if(reason!=0) wsClose(w,n,reason,time);results[s+5]=0; }
    for(uint n=0;n<w.count && w.error==0;n++)
    {
        uint s=wsState(w,n),d=wsNode(w,n),opens=results[s+1],repeat=commands[d];
        if(results[s]!=0 || repeat!=0 && opens>=repeat) continue;
        for(uint e=0;e<commands[d+10];e++)
        {
            uint at=d+16+e*2,k=opens!=0?results[s+8+e]:0;uint64_t ended;
            if(wsMatches(w,commands[at],commands[at+1],k,ended)>k && wsReached(time,f64Add(ended,wsLoad(d+2))))
            { wsOpen(w,n,e,time);break; }
        }
    }
    for(uint n=0;n<w.count && w.error==0;n++)
    {
        uint s=wsState(w,n),d=wsNode(w,n),fired=results[s+4],hits=commands[d+6];
        while(results[s]!=0 && fired<hits && w.error==0)
        {
            // Native pending is start+i*interval, not repeated addition.
            uint64_t due=f64Add(wsRead(s+2),f64Mul(f64FromI64(fired),wsLoad(d+8)));
            if(!wsReached(time,due)) break;
            wsLog(w,3,n,fired,time);if(w.error!=0) break;fired++;results[s+4]=fired;
        }
    }
}
[noinline]
void wsFinish(inout WorldSchedule w,uint64_t time)
{ for(uint n=0;n<w.count && w.error==0;n++) if(results[wsState(w,n)]!=0) wsClose(w,n,4,time); }
