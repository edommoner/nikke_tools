"""Opt-in common-policy lowering of authored area rotations, without an oracle.

The existing matrix ABI and shared CUDA/Metal executor are unchanged. Historical
host-libm profiles retain their original compiler and saved fingerprints.
"""
import portable_coordinate_numeric_v1 as numeric
from contextlib import contextmanager
from unittest.mock import patch
from portable_coordinate_area_specs import LAYOUT
from portable_coordinate_scene_specs import bits

PROFILE = 'coordinate-area-matrix-common-v1'


def coefficients(shape):
    if not numeric.finite(numeric.bits(shape.rot)):
        raise ValueError('Finite authored area rotation required')
    if shape.is_circle:
        return 1., 0.
    sine, cosine = numeric.sincos_degrees(numeric.bits(shape.rot))
    return numeric.number(cosine), numeric.number(sine)


def lower(words, descriptors, *, base_input):
    """Return a copy, replacing only static matrix coefficients for live rows."""
    result = list(words)
    for row in descriptors['rows']:
        at = base_input + LAYOUT['HEADER'] + row['slot'] * LAYOUT['ROW_WORDS']
        co, si = coefficients(row['shape'])
        result[at + 2:at + 6] = bits(co) + bits(si)
    return result


@contextmanager
def compiler_policy():
    """Inherited static compilers all resolve this same explicit coefficient hook."""
    import portable_coordinate_area_specs as area
    with patch.object(area, 'rotation_coefficients', coefficients):
        yield
