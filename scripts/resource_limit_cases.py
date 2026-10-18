"""Independent resource quantities shared by CPU and GPU witnesses."""
# name, initial, request, minimum, remaining, actual spend
CASES = (
    ('zero', 0, 6, 1, 1, 0),
    ('below-minimum', .5, 6, 1, 1, 0),
    ('at-minimum', 1, 6, 1, 1, 0),
    ('partial-to-minimum', 5, 6, 1, 1, 4),
    ('ordinary-remainder', 10, 6, 1, 4, 6),
    ('upper-branch', 13, 9, 0, 4, 9),
    ('all-above-minimum', 13, -1, 1, 1, 12),
    ('fractional', 2.25, 1.75, 1, 1, 1.25),
    ('all-fractional', 2.25, -1, 1, 1, 1.25),
    ('rounded-remainder-is-not-spend', 1e16, 1, 0, 1e16, 1),
    ('minimum-on-zero-request', 0, 0, 1, 1, 0),
    ('legacy-negative-request', 3, -2, 0, 5, 0),
    ('legacy-negative-resource', -1, 2, 0, 0, 0),
)
