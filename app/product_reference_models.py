"""Explicit product CPU consumers; pinned source and default rules stay intact.

Declarations are user-authored mechanics, never inferred game constants. Each
consumer reuses its checked reference adapter and must gain a matching shared
GPU producer before GPU admission. No dynamic CPU state is a GPU input.
"""
import copy
from contextlib import contextmanager,ExitStack

WARNING='宣言した敵回復モデルを使用しています。実ゲームの回復量・対象規則を確認した意味ではありません。'
WEIGHTED_WARNING='宣言したダメージ配分モデルを使用しています。実ゲームの配分比率を確認した意味ではありません。'
COVER_WARNING='宣言した独立遮蔽DEFモデルを使用しています。実ゲームの遮蔽基礎DEF・レベル曲線を確認した意味ではありません。'
AMMO_WARNING='宣言した敵弾倉モデルを使用しています。実ゲームの弾数・再装填規則を確認した意味ではありません。'
LOCK_WARNING='宣言したLock OnのBODY優先・ADD出現順と生存凍結対象モデルを使用しています。実ゲームの距離順位・失効時の再対象化を確認した意味ではありません。'
RANGE_WARNING='宣言した名前付き範囲・対象数モデルを使用しています。実ゲームの基礎半径・形状・距離順位を確認した意味ではありません。'
COORDINATE_WARNING='宣言した座標・共通命中サンプリング規約を使用しています。実ゲームの位置・命中分布を確認した意味ではありません。'
MOVEMENT_WARNING='宣言したADD移動・座標モデルと共通サンプリング規約を使用しています。実ゲームの位置・範囲・移動優先規則を確認した意味ではありません。'

def warning(declarations):
    return ' '.join(text for key,text in [('coordinate',COORDINATE_WARNING),('enemy_healing',WARNING),('weighted_incoming',WEIGHTED_WARNING),('cover_defense',COVER_WARNING),('enemy_ammo',AMMO_WARNING),('enemy_movement',MOVEMENT_WARNING),('named_range',RANGE_WARNING),('lock_on',LOCK_WARNING)] if key in declarations)

def combine_public(models):
    """Join independent checked readbacks without overwriting any consumer."""
    result=dict(schema=1,evidence='declared-model-not-game-verification',declarations={})
    envelope={'schema','evidence','declarations'}
    for model in models:
        if (type(model) is not dict or type(model.get('schema')) is not int or model['schema']!=1
                or model.get('evidence')!=result['evidence'] or type(model.get('declarations')) is not dict
                or not model['declarations'] or set(model)-envelope!=set(model['declarations'])):
            raise ValueError('Complete independent declared-model readback required')
        if set(result['declarations'])&set(model['declarations']):
            raise ValueError('Declared-model consumers cannot overwrite one another')
        result['declarations'].update(copy.deepcopy(model['declarations']))
        result.update({k:copy.deepcopy(v) for k,v in model.items() if k not in envelope})
    return result

def normalize(value):
    if value is None:return {}
    if type(value) is not dict or set(value)-{'coordinate','enemy_healing','weighted_incoming','cover_defense','enemy_ammo','enemy_movement','named_range','lock_on'}:
        raise ValueError('reference_modelsには接続済みのcoordinate／enemy_healing／weighted_incoming／cover_defense／enemy_ammo／enemy_movement／named_range／lock_onだけを指定してください。')
    if 'coordinate' in value and set(value)-{'coordinate','cover_defense'}:raise ValueError('Coordinate composition requires a matching checked consumer wire')
    if 'enemy_ammo' in value and set(value)-{'enemy_ammo','cover_defense'}:raise ValueError('Enemy magazine composition requires a combined checked native consumer')
    if 'enemy_movement' in value and set(value)-({'enemy_movement','named_range','cover_defense'} if 'named_range' in value else {'enemy_movement','cover_defense'}):raise ValueError('Movement composition requires a combined checked native consumer')
    if 'named_range' in value and set(value)-({'named_range','enemy_movement','cover_defense'} if 'enemy_movement' in value else {'named_range','cover_defense'}):raise ValueError('Named range composition requires a combined checked native consumer')
    if 'lock_on' in value and set(value)-{'lock_on','cover_defense'}:raise ValueError('Lock composition requires a combined checked native consumer')
    result={}
    if 'coordinate' in value:
        from product_coordinate_model import normalize_product
        result['coordinate']=normalize_product(value['coordinate'])
    if 'enemy_healing' in value:
        from enemy_healing_model import normalize as healing
        result['enemy_healing']=healing(value['enemy_healing'])
    if 'weighted_incoming' in value:
        from weighted_incoming_battle_model import WeightedIncoming
        spec=copy.deepcopy(value['weighted_incoming'])
        WeightedIncoming(spec,['1','2','3','4','5'])
        result['weighted_incoming']=spec
    if 'cover_defense' in value:
        from cover_defense_battle_model import normalize as cover
        spec=value['cover_defense']
        if type(spec) is not list or any(type(r) is not dict for r in spec):raise ValueError('Explicit five-owner cover bases required')
        cover(spec,[r.get('name') for r in spec])
        result['cover_defense']=copy.deepcopy(spec)
    if 'enemy_ammo' in value:
        from enemy_ammo_model import normalize as ammo
        result['enemy_ammo']=ammo(value['enemy_ammo'])
    if 'enemy_movement' in value:
        from product_movement_model import normalize as movement
        result['enemy_movement']=movement(value['enemy_movement'])
    if 'named_range' in value:
        from product_named_range_model import normalize as named_range
        result['named_range']=named_range(value['named_range'])
    if 'lock_on' in value:
        from product_lock_model import normalize as locks
        result['lock_on']=locks(value['lock_on'])
    if 'enemy_movement' in result and 'named_range' in result:
        for key in ('coord','logical_geometry'):
            if result['enemy_movement'][key]!=result['named_range'][key]:
                raise ValueError('Movement and named range require identical declared coordinate geometry')
    return result

def healing_public(data):
    """Product quantities only; private observers retain their full diagnostics.

    Neither backend reconstructs past carrier lists for the public response.
    The same formatter preserves all actual healing/HP/score quantities.
    """
    keys=('node','source_generation','time','target','base_amount','actor','status',
          'max_hp','multiplier','requested','dealt_before','dealt_after','applied',
          'effective_gain','hits_before','hits_after','hp_before','hp_after')
    summary=copy.deepcopy(data['public_summary'])
    return dict(receipts=[{k:copy.deepcopy(row[k]) for k in keys if k in row} for row in data['receipts']],
        sources=copy.deepcopy(data['sources']),final_adds=copy.deepcopy(data['final_adds']),
        final_scored_damage={n:data['final_scored_damage'].get(n,0.) for n in summary['add_char_total']},
        final_overkill=data['final_overkill'],public_summary=summary)

def ammo_public(data):
    return {k:copy.deepcopy(data[k]) for k in ('generations','final','charges','reloads','attempts')}

@contextmanager
def execution(declarations,names=None):
    """Install for one fresh product request, restoring aliases on all exits."""
    if not declarations:
        yield None
        return
    from enemy_healing_model import enemy_healing
    result=dict(schema=1,evidence='declared-model-not-game-verification',declarations=copy.deepcopy(declarations))
    with ExitStack() as stack:
        if 'coordinate' in declarations:
            from product_coordinate_model import execution as coordinates,public as coordinate_public
            stack.enter_context(coordinates(declarations['coordinate'],configure_run=True))
            result['coordinate']=coordinate_public(declarations['coordinate'])
        healing=stack.enter_context(enemy_healing(declarations['enemy_healing'])) if 'enemy_healing' in declarations else None
        if 'weighted_incoming' in declarations:
            from weighted_incoming_battle_model import weighted_incoming
            weighted=stack.enter_context(weighted_incoming(declarations['weighted_incoming'],names))
        else:weighted=None
        if 'cover_defense' in declarations:
            if weighted is not None:raise ValueError('Weighted allocation and independent cover DEF composition requires a combined checked landing contract')
            from cover_defense_battle_model import cover_defense
            cover=stack.enter_context(cover_defense(declarations['cover_defense'],names))
        else:cover=None
        if 'enemy_ammo' in declarations:
            from enemy_ammo_model import enemy_ammo
            ammo=stack.enter_context(enemy_ammo(declarations['enemy_ammo']))
        else:ammo=None
        if 'enemy_movement' in declarations:
            from product_movement_model import execution as movement_execution
            movement_runtime=stack.enter_context(movement_execution(declarations['enemy_movement'],expose_runtime=True))
            movement=movement_runtime.data
        else:movement=None;movement_runtime=None
        if 'named_range' in declarations:
            from product_named_range_model import execution as range_execution
            def geometry_provider(manager,boss,t):
                if movement_runtime is None or movement_runtime.manager is not manager or movement_runtime.boss is not boss or movement_runtime.last_time!=t:
                    raise ValueError('Named range must consume its owning current movement frame')
                return movement_runtime.geometry.spec if movement_runtime.geometry is not None else []
            named=stack.enter_context(range_execution(declarations['named_range'],coordinate_context=movement_runtime is None,geometry_provider=geometry_provider if movement_runtime is not None else None))
        else:named=None
        if 'lock_on' in declarations:
            from product_lock_model import execution as lock_execution
            locks=stack.enter_context(lock_execution(declarations['lock_on'],names))
        else:locks=None
        yield result
    if healing is not None:result['enemy_healing']=healing_public(healing)
    if weighted is not None:result['weighted_incoming']=copy.deepcopy(weighted)
    if cover is not None:result['cover_defense']=copy.deepcopy(cover)
    if ammo is not None:result['enemy_ammo']=ammo_public(ammo)
    if movement is not None:
        from product_movement_model import public
        result['enemy_movement']=public(movement)
    if named is not None:
        from product_named_range_model import public
        result['named_range']=public(named)

    if locks is not None:result['lock_on']=copy.deepcopy(locks)
