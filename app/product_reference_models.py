"""Explicit product CPU consumers; pinned source and default rules stay intact.

Declarations are user-authored mechanics, never inferred game constants. Each
consumer reuses its checked reference adapter and must gain a matching shared
GPU producer before GPU admission. No dynamic CPU state is a GPU input.
"""
import copy
from contextlib import contextmanager

WARNING='宣言した敵回復モデルを使用しています。実ゲームの回復量・対象規則を確認した意味ではありません。'

def normalize(value):
    if value is None:return {}
    if type(value) is not dict or set(value)-{'enemy_healing'}:
        raise ValueError('reference_modelsには接続済みのenemy_healingだけを指定してください。')
    result={}
    if 'enemy_healing' in value:
        from enemy_healing_model import normalize as healing
        result['enemy_healing']=healing(value['enemy_healing'])
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

@contextmanager
def execution(declarations):
    """Install for one fresh product request, restoring aliases on all exits."""
    if not declarations:
        yield None
        return
    from enemy_healing_model import enemy_healing
    result=dict(schema=1,evidence='declared-model-not-game-verification',declarations=copy.deepcopy(declarations))
    with enemy_healing(declarations['enemy_healing']) as data:
        yield result
    result['enemy_healing']=healing_public(data)
