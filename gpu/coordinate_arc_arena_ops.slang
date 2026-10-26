// Generated canonical bodies with resource views; arithmetic and iteration order retained.
void arena_coordinateArcClear(inout ArcArenaView value){value.count=0;value.overflow=false;}
void arena_coordinateArcAppend(inout ArcArenaView value,uint64_t start,uint64_t end)
{
    if(value.count>=COORDINATE_ARC_CAPACITY){value.overflow=true;return;}
    value.start[value.count]=start;value.end[value.count]=end;value.count++;
}
[noinline]
void arena_coordinateArcUnion(inout ArcArenaView a,inout ArcArenaView b,inout ArcArenaView value)
{
    if(!arcArenaDistinct(a,b,value))return;
    arena_coordinateArcClear(value);uint i=0,j=0;
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
        else arena_coordinateArcAppend(value,s,e);
    }
    value.overflow=value.overflow||a.overflow||b.overflow;
}
[noinline]
void arena_coordinateArcIntersect(inout ArcArenaView a,inout ArcArenaView b,inout ArcArenaView value)
{
    if(!arcArenaDistinct(a,b,value))return;
    arena_coordinateArcClear(value);uint i=0,j=0;
    while(i<a.count&&j<b.count)
    {
        uint64_t s=f64Less(a.start[i],b.start[j])?b.start[j]:a.start[i];
        uint64_t e=f64Less(b.end[j],a.end[i])?b.end[j]:a.end[i];
        if(f64Less(s,e))arena_coordinateArcAppend(value,s,e);
        if(f64Less(a.end[i],b.end[j]))i++;else j++;
    }
    value.overflow=value.overflow||a.overflow||b.overflow;
}
[noinline]
void arena_coordinateArcSubtract(inout ArcArenaView a,inout ArcArenaView b,inout ArcArenaView value)
{
    if(!arcArenaDistinct(a,b,value))return;
    arena_coordinateArcClear(value);uint first=0;
    for(uint i=0;i<a.count;i++)
    {
        uint64_t cur=a.start[i],e=a.end[i];
        while(first<b.count&&!f64Less(cur,b.end[first]))first++;
        for(uint j=first;j<b.count;j++)
        {
            uint64_t c=b.start[j],d=b.end[j];
            if(!f64Less(c,e))break;
            if(!f64Less(cur,d))continue;
            if(f64Less(cur,c))arena_coordinateArcAppend(value,cur,c);
            if(f64Less(cur,d))cur=d;
            if(!f64Less(cur,e))break;
        }
        if(f64Less(cur,e))arena_coordinateArcAppend(value,cur,e);
    }
    value.overflow=value.overflow||a.overflow||b.overflow;
}
