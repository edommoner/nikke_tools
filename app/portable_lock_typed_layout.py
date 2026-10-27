"""Preserve the entire typed arena; relocate the entire lock/manual/link arena."""
from portable_physical_lock_layout import BASE as OLD_BASE,OUTPUT as OLD_OUTPUT,check as check_locks
from portable_specs import LIMITS as L
SOURCE='gpu/world_lock_projectile_entry.slang'
INPUT=109536
TYPED_END=1048576
OFFSET=TYPED_END-OLD_BASE
LOCK_END=OLD_OUTPUT+OFFSET
OUTPUT=1310720

def check(root):
    check_locks(root)
    from portable_physical_lock_cover_layout import check as cover
    from portable_lock_packet_layout import check as packets
    cover(root);packets(root)
    if not (790000+128*1040<=940000 and 940000+L['DEPTH']*544<=TYPED_END<LOCK_END<=OUTPUT):raise ValueError('Typed/lock arenas overlap')
    return dict(input_words=INPUT,output_words=OUTPUT,typed_end=TYPED_END,lock_base=TYPED_END,lock_end=LOCK_END,offset=OFFSET,actor_sets=32,typed_targets=128,lock_snapshots=31,queue_capacity=2048)

def lock_view(block):
    """Bijective relocation of every old lock word; never discard prefix/tail."""
    if len(block)!=OUTPUT:raise ValueError('Complete composed readback required')
    if any(block[LOCK_END:]):raise AssertionError('Unowned composed tail contains data')
    return list(block[:OLD_BASE])+list(block[TYPED_END:LOCK_END])
