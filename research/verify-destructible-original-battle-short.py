"""Original skill table and burst notification using the same battle adapter."""
import array,importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
from destructible_original_battle_cases import fixtures
s=importlib.util.spec_from_file_location('original_battle_shared',ROOT/'research/verify-destructible-battle-short.py');battle=importlib.util.module_from_spec(s);s.loader.exec_module(battle)
suite=battle.suite;cross=battle.cross
native_reference=battle.native_reference
compare=battle.compare
validate_rejection=battle.validate_rejection

def prepare():
    rows=[];packed=array.array('I')
    for c in fixtures():
        w,domain=battle.compile_case(c);rows.append((c['name'],w,domain))
    packed.append(len(rows))
    for _,w,_ in rows:packed.extend(w)
    if sys.byteorder!='little':packed.byteswap()
    return rows,packed.tobytes()
