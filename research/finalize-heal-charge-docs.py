"""Record accepted production charge behavior and its explicit model limits."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for p in ['research/detail-heal-charge-production-verification.json','research/detail-heal-charge-api-verification.json','research/detail-heal-charge-browser-verification.json']:
    assert json.loads((ROOT/p).read_text(encoding='utf-8'))['passed'],p
p=ROOT/'README.md';s=p.read_text(encoding='utf-8');needle='## GPU詳細計算 v41';assert needle in s and '## GPU詳細計算 v42' not in s
text='''## GPU詳細計算 v42

デルタ：ニンジャシーフの `heal_overcharge_store_atk_pct`・`accumulate_max_scale_pct`・`heal_overcharge_discharge` をGPUに追加しました。受けた回復を蓄積し、ATK基準の上限と名前付きの上限補正を扱い、期限終了時に全員へ同じ蓄積量を回復します。v40の「余剰回復を受け止め、被ダメージで消費する保存枠」とは別の処理です。数量や回復推移をCPUからGPUへ再生する方式ではありません。[蓄積と全体回復の説明](https://www.prydwen.gg/nikke/characters/delta-ninja-thief)を参照しています。

固定CPU版では3効果が未実装だったため、`app/heal_charge_compat.py` でCPU参照モデルも補完しています。正の体力回復は満タン時もHP上限で切る前に蓄積し、分配があれば配分後の量を使います。基礎上限は発動者の最終ATKの発動時スナップショット、名前付き上限補正は預け入れ時の有効値を使い、上限低下で既に蓄積した量は失いません。再付与で量と基礎上限を作り直します。放出は発動者と効果名を区別し、対象全員への新しい回復の前に蓄積を消費します。放出時の回復補正、回復通知、分配、余剰保存は通常の回復経路で処理します。これらの相互作用・スナップショット・上限低下の扱いは明示したモデルで、すべての実機挙動を検証済みという意味ではありません。修理・復活・最大HP付与・被ダメージはこの蓄積を増減しません。

基本16、実スキルを省かない4部隊、追加10、既存178を、native/PTXそれぞれ208ケースで照合しました。部隊合計・5人のダメージ・バースト・HP/遮蔽物・装填/チャージ・両乱数状態・HPイベント順序に加え、新しい30ケースでは名前別/発動者別の蓄積量・基礎上限・保持数も毎フレーム比較します。同一フレーム内で蓄積して放出するケースは、残量ゼロの一致だけで済ませず、受け手のHP増加を入力ATKからの手計算と照合します。独立した算術・寿命・バインド31ケース、CPU部隊20＋追加10、過去のCPU部隊合計178も確認しています。レムの分配とマルチャーナの保存が実際に有効になる編成位置を使い、発動の正の対照を保持しています。

通常版36テスト（208部隊ケース＋境界27）、Node 26テスト、通常APIとブラウザーのGPU単独/CPU照合も通過しました。架空の所持装備・ヒーリングキューブLv4・スキル7/5/9・一時加算（攻撃12,000、HP100,000、防御250）のデルタ編成は、変更前103,169,263、変更後106,676,655です。実アカウントの取り込み成功、速度向上、全通常テストの再実行を示すものではありません。

現在のコンパイル対応は162/203体、宝もの段階の文脈は639/812です。全状況での戦闘一致を保証する件数ではありません。シールド増幅、被ダメージ分配、ダメージ蓄積/放出、敵側効果、遮蔽物制御、座標やCPUモデルの不足などが残り、全キャラ・全効果GPU化は未完です。検証記録は `research/detail-heal-charge-checkpoint.json`、通常画面用の架空データは `research/detail-heal-charge-ui-fixture.json` にあります。

'''
p.write_text(s.replace(needle,text+needle,1),encoding='utf-8')
p=ROOT/'research/boss-gpu-integration-notes.json';r=json.loads(p.read_text(encoding='utf-8'));r['status']='v42 healing charge/capacity/discharge: native/PTX208 each, CPU arithmetic/lifecycle/binding31, squad20+extra10, historical totals178, production36, API/browser and Node26 passed. Full objective incomplete.'
r['current_boundary']['gpu_compiler']+=' v42 adds source-ATK healing accumulation, live named capacity modifiers, owner-scoped consumption/release, nested HP-edge release and read-only named pool frames. Other unsupported effects still reject.'
r['heal_charge_checkpoint']=dict(path='research/detail-heal-charge-checkpoint.json',abi='detail_heal_charge_v42',objective_complete=False)
r['CPU_bridge_composition_note']='Charge wraps BuffManager._dispatch_instant, knock_down, notify, apply_storage_body_heal and timeline._register_instant_handlers. Future AST clones must preserve/reapply those wrappers. _activate composes storage and charge snapshots; simulation remains the v41 shared-heal binding.'
r['next_required_work'][0]['requirements'][0]='Continue damage accumulation/discharge, shield amplification, received damage sharing and remaining source effects. Healing charge/discharge is implemented under explicit CPU/GPU model choices; in-game interaction verification remains incomplete.'
r['next_required_work'][1]['requirements'][0]='Attack-attached debuffs, enemy debuff/DOT patterns, cover controls and all remaining unsupported actual effects.'
p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print('Updated v42 production documentation; full goal incomplete.')
