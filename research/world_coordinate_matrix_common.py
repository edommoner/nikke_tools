"""Scoped common-policy area distance; never changes the historical CPU source."""
from contextlib import contextmanager
from unittest.mock import patch
from coordinate_geometry_reference import norm, finite
from portable_coordinate_matrix_specs import coefficients


def distance(shape, px, py):
    dx, dy = px - shape.x, py - shape.y
    finite(dx, dy)
    if shape.is_circle:
        value = max(0., norm(dx, dy) - shape.r)
    else:
        co, si = coefficients(shape)
        lx, ly = dx * co + dy * si, -dx * si + dy * co
        finite(lx, ly)
        value = norm(max(abs(lx) - shape.w / 2., 0.),
                     max(abs(ly) - shape.h / 2., 0.))
    finite(value)
    return value


@contextmanager
def common_policy():
    import engine_worker
    from calculator import aim
    with patch.object(aim.Shape, 'dist', distance):
        yield
