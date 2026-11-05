"""Native-only initialization, zero-refresh and shared-recipient edge contracts."""
import json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/d) for d in ('app','scripts','tests')]
from test_target_counter_runtime import manager,NAMES

def seed(**extra):return dict(name='seed',source='스킬1',type='buff',stat='atk_pct',fixed_value=1,target='self',duration=2,max_stack=5,polarity='beneficial',trigger=dict(timing=['event:full_reload'],condition=[]),**extra)
def op(stat,value,target='self'):return dict(name='operation',source='스킬1',type='buff' if stat=='buff_max_stack_add' else 'instant',stat=stat,fixed_value=value,target=target,target_effect='seed',trigger=dict(timing=['on_attack'],condition=[]))
