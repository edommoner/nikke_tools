// Generated canonical bodies with reference parameters; no arithmetic changes.
[noinline]
void coordinateLandingSubtract(inout CoordinateArcSet a,inout CoordinateArcSet b,out CoordinateArcSet value)
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
[noinline]
uint64_t coordinateLandingMeasure(inout CoordinateArcSet value)
{
    Sum sum={};
    for(uint i=0;i<value.count;i++)addSum(sum,f64Add(value.end[i],value.start[i]^F64_SIGN));
    // Same finite Neumaier finalization already used by periodicSkillInterval.
    return f64Finite(sum.correction)&&!f64Zero(sum.correction)?f64Add(sum.total,sum.correction):sum.total;
}
