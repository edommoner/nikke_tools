// Ordered shared binary64 movement step. No native double or fused arithmetic.
// Actor, field lifetime, spatial selection and world clock belong to callers.
bool enemyMovementStep(uint64_t x,uint64_t y,uint64_t vx,uint64_t vy,
    uint64_t cx,uint64_t cy,uint64_t dt,bool disabled,bool forced,uint precedence,
    out uint64_t ox,out uint64_t oy)
{
    ox=x;oy=y;
    if(disabled&&(!forced||precedence==0))return true;
    if(forced){ox=cx;oy=cy;return true;}
    ox=f64Add(x,f64Mul(vx,dt));oy=f64Add(y,f64Mul(vy,dt));
    return f64Finite(ox)&&f64Finite(oy);
}
