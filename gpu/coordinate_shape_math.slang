// Pure shape math shared by full battle selection and the bounded CUDA probe.
uint64_t coordinateShapeMax(uint64_t a,uint64_t b){return f64Less(a,b)?b:a;}
bool coordinateShapeMatrixValid(uint kind,uint64_t co,uint64_t si)
{
    uint64_t one=uint64_t(0x3ff00000U)<<32;
    if(!f64Finite(co)||!f64Finite(si)||f64Less(one,f64Abs(co))||f64Less(one,f64Abs(si)))return false;
    uint64_t norm=f64Add(f64Mul(co,co),f64Mul(si,si));
    if(f64Less(uint64_t(0x3ce00000U)<<32,f64Abs(f64Add(norm,one^F64_SIGN))))return false;
    return kind!=1||(f64Equal(co,one)&&f64Zero(si));
}
uint64_t coordinateShapeDistance(uint kind,uint64_t x,uint64_t y,uint64_t radius,uint64_t width,uint64_t height,uint64_t co,uint64_t si,uint64_t ax,uint64_t ay)
{
    uint64_t dx=f64Add(ax,x^F64_SIGN),dy=f64Add(ay,y^F64_SIGN);
    if(kind==1)return coordinateShapeMax(0,f64Add(coordinateHypot(dx,dy),radius^F64_SIGN));
    uint64_t lx=f64Add(f64Mul(dx,co),f64Mul(dy,si)),ly=f64Add(f64Mul(dx^F64_SIGN,si),f64Mul(dy,co));
    uint64_t two=uint64_t(0x40000000U)<<32;
    uint64_t ex=coordinateShapeMax(f64Add(f64Abs(lx),f64Div(width,two)^F64_SIGN),0),ey=coordinateShapeMax(f64Add(f64Abs(ly),f64Div(height,two)^F64_SIGN),0);
    return coordinateHypot(ex,ey);
}
bool coordinateShapeContains(uint64_t distance,uint64_t grow)
{
    uint64_t touch=(uint64_t(0x3e112e0bU)<<32)|0xe826d695U;
    return !f64Nan(distance)&&!f64Less(f64Add(grow,touch),distance);
}
