"""One ordered spread body for default and coordinate physical profiles."""
from pathlib import Path

STATEMENTS = '''    uint64_t spread = s.spreadStart[who];
    if (!f64Zero(s.spreadShots[who]))
    {
        uint64_t progress = f64Div(smaller(s.warm[who],s.spreadShots[who]),s.spreadShots[who]);
        spread = f64Add(spread,f64Mul(f64Add(s.spreadEnd[who],spread ^ F64_SIGN),progress));
    }
    uint64_t slope = uint64_t(0x3f829888) << 32 | 0xf861a60d;
    spread = larger(ONE,f64Mul(spread,f64Add(ONE,f64Mul(slope,accuracy) ^ F64_SIGN)));
    s.lastSpread[who] = spread;'''


def schema():
    return ('// Generated ordered spread body; no helper in the default profile.\n'
            '#ifndef PORTABLE_NORMAL_SPREAD_BODY\n'
            '#define PORTABLE_NORMAL_SPREAD_BODY \\\n'+
            ' \\\n'.join(STATEMENTS.splitlines())+'\n#endif\n')


def check_schema(root=None):
    root=Path(root or Path(__file__).resolve().parents[1])
    assert (root/'gpu/normal_spread_body.slang').read_text()==schema(), 'Spread body source drift'
