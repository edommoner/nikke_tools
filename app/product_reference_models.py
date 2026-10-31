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

def warning(declarations):
    return ' '.join(text for key,text in [('enemy_healing',WARNING),('weighted_incoming',WEIGHTED_WARNING),('cover_defense',COVER_WARNING),('enemy_ammo',AMMO_WARNING)] if key in declarations)

def normalize(value):
    if value is None:return {}
    if type(value) is not dict or set(value)-{'enemy_healing','weighted_incoming','cover_defense','enemy_ammo'}:
        raise ValueError('reference_modelsには接続済みのenemy_healing／weighted_incoming／cover_defense／enemy_ammoだけを指定してください。')
    if 'enemy_ammo' in value and len(value)!=1:raise ValueError('Enemy magazine composition requires a combined checked native consumer')
    result={}
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
        yield result
    if healing is not None:result['enemy_healing']=healing_public(healing)
    if weighted is not None:result['weighted_incoming']=copy.deepcopy(weighted)
    if cover is not None:result['cover_defense']=copy.deepcopy(cover)
    if ammo is not None:result['enemy_ammo']=ammo_public(ammo)
