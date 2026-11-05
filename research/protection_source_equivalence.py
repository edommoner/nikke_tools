"""Allow exactly one unsupported-API-test sentinel edit, never runtime changes."""
import hashlib,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1]
API='scripts/verify-portable-api.py'
BEFORE=b"invalid['effects'][1]['effect']['stat']='shield_from_max_hp_pct'"
AFTER=b"invalid['effects'][1]['effect']['stat']='taunt'"
def equivalence(before,after=None):
 args=['git','diff','--name-only',before]+([after] if after else [])+['--','app','scripts','gpu','tests'];changed=subprocess.check_output(args,cwd=R,text=True).splitlines()
 if not changed:return dict(passed=True,changed_paths=[],runtime_unchanged=True)
 assert changed==[API],changed
 old=subprocess.check_output(['git','show',before+':'+API],cwd=R);new=subprocess.check_output(['git','show',after+':'+API],cwd=R) if after else (R/API).read_bytes()
 assert old.count(BEFORE)==1 and old.replace(BEFORE,AFTER)==new
 return dict(passed=True,changed_paths=changed,runtime_unchanged=True,change='Only the unsupported API rejection sentinel changes from newly supported shield to unported taunt.',before_sha256=hashlib.sha256(old).hexdigest(),after_sha256=hashlib.sha256(new).hexdigest())
