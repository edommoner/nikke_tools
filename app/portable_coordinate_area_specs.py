"""Static shape IR: authored angles become immutable rotation coefficients.

No distance, target selection, damage, schedule or native battle is evaluated.
Both GPU backends consume the same compiled binary64 matrix bytes.
"""
import math
from pathlib import Path
from portable_coordinate_scene_specs import bits,LAYOUT as C
LAYOUT=dict(INPUT=1056,HEADER=32,ROW_WORDS=8,ROWS=128,BASE_INPUT=107584)
MAGIC=0x43415231
def shader_schema():
    return '// Generated from portable_coordinate_area_specs.\n'+''.join(
        ('#ifdef PORTABLE_COMPOSED_ARENA\nstatic const uint CA_BASE_INPUT=107592;\n#else\n'+f'static const uint CA_{k}={v};\n'+'#endif\n')
        if k=='BASE_INPUT' else f'static const uint CA_{k}={v};\n' for k,v in LAYOUT.items())
def check_schema(root=None):assert (Path(root or Path(__file__).resolve().parents[1])/'gpu/coordinate_area_layout.slang').read_text()==shader_schema()
def rotation_coefficients(shape):
    theta=math.radians(shape.rot)
    return (1.,0.) if shape.is_circle else (math.cos(theta),math.sin(theta))
def compile_area(case,descriptors,*,explosion_ranges):
    from calculator.boss_pattern import coord_spec,DEFAULT_EXPLOSION_RANGE
    check_schema();spec=coord_spec(case['enemy'].get('coord'))
    if spec is None:raise ValueError('Coordinate shape IR requires authored coordinates')
    # Manual coordinate waypoints need their own frame caller; never ignore them.
    controls=case.get('controls',[]);controls=controls.values() if isinstance(controls,dict) else controls
    if any(w.get('aim') for w in controls):raise ValueError('Manual coordinate aim unconnected')
    words=[0]*LAYOUT['INPUT'];words[:4]=[MAGIC,1,len(descriptors['rows']),0]
    words[4:12]=sum((bits(v) for v in (*spec.auto_aim,spec.pierce_px,spec.explosion_scale)),[])
    if len(explosion_ranges)!=5:raise ValueError('Five authored weapon explosion ranges required')
    for who,value in enumerate(explosion_ranges):
        if value is not None and type(value) not in (int,float):raise ValueError('Literal weapon explosion range required')
        value=value or DEFAULT_EXPLOSION_RANGE
        if value<0:raise ValueError('Nonnegative weapon explosion range required')
        words[12+who*2:14+who*2]=bits(value)
    for index,row in enumerate(descriptors['rows']):
        shape=row['shape'];co,si=rotation_coefficients(shape);at=LAYOUT['HEADER']+row['slot']*8
        words[at:at+8]=[index+1,1 if shape.is_circle else 2,*bits(co),*bits(si),0,0]
    return words
