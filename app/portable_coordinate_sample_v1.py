"""Deterministic coordinate sample recipe; existing MT owns the random stream.

This is the point producer required by the sampled physical caller. It does
not certify damage, shot callbacks, or a complete sampled battle.
"""
from pathlib import Path
import hashlib,json
import portable_coordinate_numeric_v1 as n
import portable_coordinate_power_v1 as power

PROFILE='coordinate-sample-v1'
MAGIC=0x43535631
MIN_K=n.bits(2.**-16);MAX_K=n.bits(65536.)
MIN_RADIUS=n.bits(1e-9);RANDOM_SCALE=n.bits(2.**-53)
# One explicit ordered arithmetic recipe for both CPU and Slang.
RADIAL=(('inverse','div','one','k'),('radial','power','u','inverse'),('rho','mul','radius','radial'))
ANGLE=(('theta','mul','tau','v'),)
ANGULAR=(('dx','mul','rho','cosine'),('dy','mul','rho','sine'),('px','add','ax','dx'),('py','add','ay','dy'))

def valid(ax,ay,radius,k):
    return all(n.finite(v) for v in (ax,ay,radius,k)) and MIN_K<=k<=MAX_K

def random53(rng):
    # CPython Random.random: two sequential words, high 27 and high 26 bits.
    a=rng.getrandbits(32)>>5;b=rng.getrandbits(32)>>6
    return n.bits(((a<<26)+b)*n.number(RANDOM_SCALE))

def recipe(ops,env):
    for name,op,a,b in ops:
        env[name]={'add':n.add,'mul':n.mul,'div':n.div,'power':power.evaluate}[op](env[a],env[b])

def point(ax,ay,radius,k,u,v=None):
    if not valid(ax,ay,radius,k) or not n.finite(u) or u&n.SIGN or u>=n.ONE or v is not None and (not n.finite(v) or v&n.SIGN or v>=n.ONE):raise ValueError('Coordinate sample domain')
    env=dict(ax=ax,ay=ay,radius=n.bits(max(n.number(radius),n.number(MIN_RADIUS))),k=k,u=u,one=n.ONE,tau=n.TAU)
    recipe(RADIAL,env)
    if v is None:px,py=n.add(ax,env['rho']),ay
    else:
        env['v']=v;recipe(ANGLE,env);env['sine'],env['cosine']=n.sincos_radians(env['theta']);recipe(ANGULAR,env);px,py=env['px'],env['py']
    if not n.finite(px) or not n.finite(py):raise ValueError('Coordinate sample nonfinite result')
    return px,py

def sample(ax,ay,radius,rng,*,angle=True,k=2.55):
    values=tuple(map(n.bits,(ax,ay,radius,k)))
    if not valid(*values):raise ValueError('Coordinate sample domain')
    u=random53(rng);v=random53(rng) if angle else None
    return tuple(map(n.number,point(*values,u,v)))

def contract_sha256():
    return hashlib.sha256(json.dumps(dict(profile=PROFILE,radial=RADIAL,angle=ANGLE,angular=ANGULAR,min_k=MIN_K,max_k=MAX_K,min_radius=MIN_RADIUS,random_scale=RANDOM_SCALE,numeric=n.contract_sha256()),sort_keys=True).encode()).hexdigest()

def shader_schema():
    def constant(v):return f'(uint64_t(0x{v>>32:08x}U)<<32|uint64_t(0x{v&0xffffffff:08x}U))'
    def ops(rows):
        out=[]
        for name,op,a,b in rows:
            call='coordinateUnitPower' if op=='power' else {'add':'f64Add','mul':'f64Mul','div':'f64Div'}[op]
            out.append(f'    uint64_t {name}={call}({a},{b}'+(',status' if op=='power' else '')+');')
        return '\n'.join(out)
    return f'''// Generated {PROFILE}; contract {contract_sha256()}.
#ifndef PORTABLE_COORDINATE_SAMPLE_V1
#define PORTABLE_COORDINATE_SAMPLE_V1
uint64_t coordinateRandom53(uint rng)
{{
    uint a=mtNext(rng)>>5,b=mtNext(rng)>>6;
    return f64Mul(f64FromI64((uint64_t(a)<<26)+b),{constant(RANDOM_SCALE)});
}}
bool validCoordinateSample(uint64_t ax,uint64_t ay,uint64_t radius,uint64_t k)
{{return f64Finite(ax)&&f64Finite(ay)&&f64Finite(radius)&&f64Finite(k)&&k>={constant(MIN_K)}&&k<={constant(MAX_K)};}}
[noinline]
void coordinateSamplePoint(uint rng,uint64_t ax,uint64_t ay,uint64_t radius,uint64_t k,bool angle,out uint64_t px,out uint64_t py,out uint64_t u,out uint64_t v,out uint status)
{{
    status=0;px=0;py=0;u=0;v=0;
    if(!validCoordinateSample(ax,ay,radius,k)){{status=64;return;}}
    radius=f64Less(radius,{constant(MIN_RADIUS)})?{constant(MIN_RADIUS)}:radius;
    u=coordinateRandom53(rng);uint64_t one=ONE,tau=coordinateTau();
{ops(RADIAL)}
    if(status!=0){{status=64;return;}}
    if(!angle){{px=f64Add(ax,rho);py=ay;}}
    else
    {{
        v=coordinateRandom53(rng);uint64_t sine,cosine;
        {ops(ANGLE)}
        coordinateSinCosRadians(theta,sine,cosine);
{ops(ANGULAR).replace('uint64_t px=','px=').replace('uint64_t py=','py=')}
    }}
    if(!f64Finite(px)||!f64Finite(py))status=64;
}}
#endif
'''

def check_schema(root=None):
    root=Path(root or Path(__file__).resolve().parents[1]);n.check_schema(root);power.check_schema(root)
    assert (root/'gpu/coordinate_sample_v1.slang').read_text()==shader_schema(),'Coordinate sampler schema drift'
