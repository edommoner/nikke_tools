"""Compose existing typed weapon and original Lock On consumers in one world."""
import copy
from pathlib import Path
from portable_runtime import UnsupportedPortable
from portable_product_coordinate_lock import COORDINATE_OUTPUT,OUTPUT
INPUT=121936
WEAPON_START=170976
WEAPON_SCRATCH=220768
WEAPON_END=231152  # 1024 mixed pellets*10 +128 generations +16 notification words.


def check_schema(root):
    from portable_product_coordinate_lock import check_schema as locks
    from portable_coordinate_typed_aim_specs import HEAD,WORDS
    locks(root)
    from portable_product_typed import check_schema as physical
    physical(root)
    if not 153568+32*544==WEAPON_START<HEAD+WORDS==WEAPON_SCRATCH<WEAPON_END<262144:
        raise ValueError('Typed skill, weapon history, aim and pellet scratch overlap')
    source=(Path(root)/'gpu/product_typed_lock_battle_entry.slang').read_text()
    if '#define CTW_SCRATCH(s) DT_OUTPUT((s).resourceOutput,220768U)' not in source:
        raise ValueError('Typed weapon scratch must be disjoint from synchronous skill DFS')
    return dict(input_words=INPUT,output_words=OUTPUT,skill_capacity=2048,typed_attack_capacity=128,weapon_history_capacity=2048)


class LockReadback:
    """Only the separately checked physical banks project out of the lock view.

    Every actual output word remains in the captured raw comparison. The shared
    physical decoder checks the complete weapon history/aim; the old lock reader
    keeps strict ownership of all typed skill, target, lock and reserved banks.
    """
    def __init__(self,block):self.block=block
    def __len__(self):return len(self.block)
    def __getitem__(self,key):
        if isinstance(key,slice):
            a,b,step=key.indices(len(self));return [self[i] for i in range(a,b,step)]
        if not 0<=key<len(self):raise IndexError(key)
        if COORDINATE_OUTPUT+WEAPON_START<=key<COORDINATE_OUTPUT+WEAPON_END:return 0
        return self.block[key]


def read_result(block,metadata,names,duration):
    from portable_product_coordinate import read_result as coordinates
    from portable_product_coordinate_lock import read_result as locks
    from portable_product_typed import read_weapon_history
    from portable_specs import LIMITS as L
    from product_reference_models import combine_public
    if len(block)!=OUTPUT or block[0]!=0:raise UnsupportedPortable('Complete typed weapon/Lock On readback required')
    # Validate the complete coordinate/skill prefix without adding a second
    # declaration or exposing its internal synthetic empty logical scene.
    coordinates(memoryview(block)[:COORDINATE_OUTPUT],metadata,names=names,duration=duration)
    if any(block[COORDINATE_OUTPUT+WEAPON_END:COORDINATE_OUTPUT+262144]):
        raise UnsupportedPortable('Nonzero unowned typed weapon/Lock On tail')
    if any(block[L['COUNTER_CONTEXT_BASE']:L['COUNTER_CONTEXT_BASE']+1096]):
        raise UnsupportedPortable('Unrestored shared typed notification context')
    locked=locks(LockReadback(block),metadata,duration)
    state=locked['lock_on']['typed']
    physical=read_weapon_history(block,metadata,names,duration,state,base=COORDINATE_OUTPUT,tail_start=WEAPON_SCRATCH)
    from portable_product_typed import read_nearby_history
    nearby=read_nearby_history(memoryview(block)[:COORDINATE_OUTPUT],metadata,duration)
    if metadata['product_typed_targets']['declarations']['typed_targets'].get('nearby_rules'):physical['nearby_casts']=nearby

    info=metadata['product_lock_on'];source=info['typed_source'];name=info['typed_case']['effects'][source]['name']
    bindings=metadata['product_typed_targets']['declarations']['typed_targets']['bindings']
    for attack in state['attacks']:
        if not 0<=attack['time']<=duration:raise UnsupportedPortable('Typed skill receipt outside its battle')
        for receipt in attack['receipts']:
            slot=receipt['slot'];handle=receipt['handle']
            if (handle[0]!=2 or not 0<=slot<len(bindings) or handle[:2]!=[bindings[slot]['kind'],bindings[slot]['identity']]
                    or not 1<=handle[2]<=0x7fffffff or receipt['took']>attack['damage']
                    or not receipt['delivered'] and (receipt['took']!=0 or receipt['broken'])):
                raise UnsupportedPortable('Invalid shared typed skill receipt identity or amount')
    physical['skill_attacks']=[dict(attack_id=a['attack_id'],owner=names[a['owner']],name=name,time=a['time'],damage=a['damage'],completed=a['completed'],
        receipts=[dict(slot=q['slot'],actor=copy.deepcopy(q['handle']),delivered=q['delivered'],broken=q['broken'],took=q['took'],
            notice=dict(handle=copy.deepcopy(q['handle']),owner=copy.deepcopy(metadata['product_typed_targets']['declarations']['typed_targets']['bindings'][q['slot']]['owner']),time=a['time']) if q['broken'] else None) for q in a['receipts']]) for a in state['attacks']]
    typed=dict(schema=1,evidence='declared-model-not-game-verification',declarations=copy.deepcopy(metadata['product_typed_targets']['declarations']),typed_targets=physical)
    return combine_public([typed,locked])
