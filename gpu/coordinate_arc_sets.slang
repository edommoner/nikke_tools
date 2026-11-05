// Canonical sorted, disjoint angular intervals; shared CUDA/Metal binary64.
// No probabilities/geometry are calculated on the host. A caller can feed
// up to 512 intervals per operand, preserving up to 1024 result intervals.
// Overflow is an error, never a clipped or overwritten interval history.
#ifndef PORTABLE_COORDINATE_ARC_SETS
#define PORTABLE_COORDINATE_ARC_SETS
static const uint COORDINATE_ARC_CAPACITY=1024;
struct CoordinateArcSet
{
    uint count;
    bool overflow;
    uint64_t start[COORDINATE_ARC_CAPACITY];
    uint64_t end[COORDINATE_ARC_CAPACITY];
};
void coordinateArcClear(out CoordinateArcSet value){value.count=0;value.overflow=false;}
void coordinateArcAppend(inout CoordinateArcSet value,uint64_t start,uint64_t end)
{
    if(value.count>=COORDINATE_ARC_CAPACITY){value.overflow=true;return;}
    value.start[value.count]=start;value.end[value.count]=end;value.count++;
}
[noinline]
void coordinateArcUnion(CoordinateArcSet a,CoordinateArcSet b,out CoordinateArcSet value)
{
    coordinateArcClear(value);uint i=0,j=0;
    while(i<a.count||j<b.count)
    {
        // Stable lexicographic merge is equivalent to sorted(a+b) on the
        // canonical sorted input domain, including equal endpoints.
        bool left=j==b.count||(i<a.count&&(f64Less(a.start[i],b.start[j])||
            f64Equal(a.start[i],b.start[j])&&!f64Less(b.end[j],a.end[i])));
        uint64_t s,e;
        if(left){s=a.start[i];e=a.end[i++];}else{s=b.start[j];e=b.end[j++];}
        if(value.count!=0&&!f64Less(value.end[value.count-1],s))
        {if(f64Less(value.end[value.count-1],e))value.end[value.count-1]=e;}
        else coordinateArcAppend(value,s,e);
    }
    value.overflow=value.overflow||a.overflow||b.overflow;
}
[noinline]
void coordinateArcIntersect(CoordinateArcSet a,CoordinateArcSet b,out CoordinateArcSet value)
{
    coordinateArcClear(value);uint i=0,j=0;
    while(i<a.count&&j<b.count)
    {
        uint64_t s=f64Less(a.start[i],b.start[j])?b.start[j]:a.start[i];
        uint64_t e=f64Less(b.end[j],a.end[i])?b.end[j]:a.end[i];
        if(f64Less(s,e))coordinateArcAppend(value,s,e);
        if(f64Less(a.end[i],b.end[j]))i++;else j++;
    }
    value.overflow=value.overflow||a.overflow||b.overflow;
}
[noinline]
void coordinateArcSubtract(CoordinateArcSet a,CoordinateArcSet b,out CoordinateArcSet value)
{
    coordinateArcClear(value);uint first=0;
    for(uint i=0;i<a.count;i++)
    {
        uint64_t cur=a.start[i],e=a.end[i];
        while(first<b.count&&!f64Less(cur,b.end[first]))first++;
        for(uint j=first;j<b.count;j++)
        {
            uint64_t c=b.start[j],d=b.end[j];
            if(!f64Less(c,e))break;
            if(!f64Less(cur,d))continue;
            if(f64Less(cur,c))coordinateArcAppend(value,cur,c);
            if(f64Less(cur,d))cur=d;
            if(!f64Less(cur,e))break;
        }
        if(f64Less(cur,e))coordinateArcAppend(value,cur,e);
    }
    value.overflow=value.overflow||a.overflow||b.overflow;
}
#endif
