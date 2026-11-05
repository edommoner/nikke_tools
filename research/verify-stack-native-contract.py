"""Native-only contract audit before admitting new common GPU effect kinds."""
import copy,json,math,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/d) for d in ('app','scripts','tests')]
from test_target_counter_runtime import manager,NAMES

def base(polarity='beneficial',cap=5):
 return dict(name='stack',source='스킬1',type='buff',stat='atk_pct',fixed_value=1,target='self',duration=2,max_stack=cap,polarity=polarity,trigger=dict(timing=['battle_start'],condition=[]))
