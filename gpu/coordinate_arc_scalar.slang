// Ordered angular arithmetic. Include after the existing Sum/addSum runtime.
// Finite input and positive finite period are the caller's checked contract.
#ifndef PORTABLE_COORDINATE_ARC_SCALAR
#define PORTABLE_COORDINATE_ARC_SCALAR
#include "coordinate_arc_sets.slang"
uint64_t coordinateTau(){return uint64_t(0x401921fbU)<<32|uint64_t(0x54442d18U);}
[noinline]
uint64_t coordinatePositiveModulo(uint64_t x,uint64_t period)
{
    uint64_t remainder=f64Abs(x);
    if(remainder>=period)
    {
        int ex,ep;uint64_t sx,sp;f64Unpack(remainder,ex,sx);f64Unpack(period,ep,sp);
        while(ex>ep)
        {
            if(sx>=sp)sx-=sp;
            if(sx==0)return 0;
            sx<<=1;ex--;
        }
        if(sx>=sp)sx-=sp;
        remainder=f64Pack(0,ep,sx<<3);
    }
    // CPython fmod sign correction may round a tiny negative remainder to
    // the period itself. Preserve that result rather than clamping to zero.
    if((x&F64_SIGN)!=0&&!f64Zero(remainder))return f64Add(period,remainder^F64_SIGN);
    return remainder; // positive-period modulo of either signed zero is +0
}
[noinline]
void coordinateArcCreate(uint64_t start,uint64_t length,out CoordinateArcSet value)
{
    coordinateArcClear(value);uint64_t tau=coordinateTau();
    if(!f64Less(0,length))return;
    uint64_t epsilon=uint64_t(0x3d719799U)<<32|uint64_t(0x812dea11U); // 1e-12
    if(!f64Less(length,f64Add(tau,epsilon^F64_SIGN))){coordinateArcAppend(value,0,tau);return;}
    uint64_t a=coordinatePositiveModulo(start,tau),b=f64Add(a,length);
    if(!f64Less(tau,b))coordinateArcAppend(value,a,b);
    else{coordinateArcAppend(value,0,f64Add(b,tau^F64_SIGN));coordinateArcAppend(value,a,tau);}
}
[noinline]
uint64_t coordinateArcMeasure(CoordinateArcSet value)
{
    Sum sum={};
    for(uint i=0;i<value.count;i++)addSum(sum,f64Add(value.end[i],value.start[i]^F64_SIGN));
    // Same finite Neumaier finalization already used by periodicSkillInterval.
    return f64Finite(sum.correction)&&!f64Zero(sum.correction)?f64Add(sum.total,sum.correction):sum.total;
}
[noinline]
void coordinateArcInsert(inout CoordinateArcSet value,uint64_t start,uint64_t end)
{
    // Stable lexicographic insertion followed by the same touching merge as
    // sorted(value+[interval]). Only active entries move; no 1024-row copies.
    uint position=0;
    while(position<value.count&&(f64Less(value.start[position],start)||
        f64Equal(value.start[position],start)&&!f64Less(end,value.end[position])))position++;
    uint destination=position;
    if(position>0&&!f64Less(value.end[position-1],start))
    {
        destination=position-1;start=value.start[destination];
        if(f64Less(end,value.end[destination]))end=value.end[destination];
    }
    uint after=position;
    while(after<value.count&&!f64Less(end,value.start[after]))
    {if(f64Less(end,value.end[after]))end=value.end[after];after++;}
    uint removed=after-destination,nextCount=value.count+1-removed;
    if(nextCount>COORDINATE_ARC_CAPACITY){value.overflow=true;return;}
    if(removed==0)
    {for(uint at=value.count;at>destination;at--){value.start[at]=value.start[at-1];value.end[at]=value.end[at-1];}}
    else if(removed>1)
    {for(uint at=after;at<value.count;at++){value.start[at-removed+1]=value.start[at];value.end[at-removed+1]=value.end[at];}}
    value.start[destination]=start;value.end[destination]=end;value.count=nextCount;
}
[noinline]
void coordinateArcShift(CoordinateArcSet a,uint64_t by,out CoordinateArcSet value)
{
    coordinateArcClear(value);
    for(uint i=0;i<a.count;i++)
    {
        CoordinateArcSet fragment;
        coordinateArcCreate(f64Add(a.start[i],by),f64Add(a.end[i],a.start[i]^F64_SIGN),fragment);
        for(uint j=0;j<fragment.count&&!value.overflow;j++)coordinateArcInsert(value,fragment.start[j],fragment.end[j]);
        value.overflow=value.overflow||fragment.overflow;
        if(value.overflow)return;
    }
    value.overflow=value.overflow||a.overflow;
}
#endif
