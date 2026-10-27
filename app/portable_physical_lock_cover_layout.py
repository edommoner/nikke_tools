"""Manual posture occupies disjoint padding after immutable lock snapshots."""
from portable_physical_lock_layout import INPUT,OUTPUT,END,SOURCE as LOCK_SOURCE,check as check_locks
SOURCE='gpu/world_physical_lock_cover_entry.slang'
BASE=END
WORDS=80

def shader_layout():
    return '// Generated from portable_physical_lock_cover_layout.py.\nstatic const uint PL_COVER_BASE = '+str(BASE)+'U;\n'

def check(root):
    from pathlib import Path
    legacy=check_locks(root)
    if BASE%8 or BASE+WORDS>OUTPUT:raise ValueError('Physical lock/manual posture overlap')
    if (Path(root)/'gpu/physical_lock_cover_layout.slang').read_text()!=shader_layout():raise ValueError('Physical cover layout differs')
    return dict(**legacy,manual_base=BASE,manual_words=WORDS,manual_end=BASE+WORDS)
