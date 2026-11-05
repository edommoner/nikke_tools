"""Area/physical mixed worlds with axis, adjacent, negative and huge rotations."""
import copy
import math
from portable_coordinate_core_cases import fixtures as cores


def fixtures():
    base = cores()[-1]
    angles = [0., -0., 30., 45., 90., -90., 180., -180.,
              math.nextafter(90., 0.), math.nextafter(90., math.inf),
              math.nextafter(-180., -math.inf), 360., 720.25, -720.25,
              1e20, float.fromhex('0x1.fffffffffffffp+1023')]
    rows = []
    for index, angle in enumerate(angles):
        case = copy.deepcopy(base)
        case['name'] = 'coordinate-core/common-matrix-' + str(index)
        # Both shapes are live for skill selection and expected physical fire.
        for target in case['patterns'][0]['targets']:
            target.pop('r')
            target.update(w=10., h=2., rotation=angle, hp=1e30)
        rows.append(case)
    for outside in (False, True):
        case = copy.deepcopy(base)
        case['name'] = 'coordinate-core/common-matrix-touch-' + str(outside)
        case['enemy']['coord']['auto_aim'] = [0., 0.]
        edge = 11. + 1e-9
        case['patterns'][0]['targets'] = [dict(name='front', hp=1e30,
            x=math.nextafter(edge, math.inf) if outside else edge,
            y=40., w=100., h=2., rotation=90., z=1)]
        rows.append(case)
    return rows
