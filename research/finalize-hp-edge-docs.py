"""Publish v35 scope only after ordinary production/API/browser acceptance."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
for path in ('research/detail-normal-acceptance.json','research/detail-hp-edge-api-verification.json','research/detail-hp-edge-browser-verification.json'):
    r=json.loads((ROOT/path).read_text(encoding='utf-8'));assert r['passed'],path
    assert all(sha(p)==h for p,h in r['source_sha256'].items()),path
    if path.endswith('normal-acceptance.json'):assert r['tests_run']==95 and r['skipped']==0
    if '-api-' in path:assert r['pure_gpu_path_verified'] and r['compute']['cpu_verification']['matched']
    if '-browser-' in path:assert r['browser_interaction_verified']
p=ROOT/'README.md';text=p.read_text(encoding='utf-8');heading='## 詳細GPU版の実装・CPU照合\n\n'
assert heading in text and 'v35ではHP閾値' not in text
addition='''v35ではHP閾値の下向き通過、指定した到達回数、部隊の味方HP・隣接HPの通知、隣接キャラの満タン復帰をGPU内で処理します。HP消費・被弾・回復・最大HPの変化ごとに、その場で通知を処理してから次の対象へ進みます。発動中に回復した場合の再入防止、部隊順と登録順、同じ閾値の重複、1e-6の境界判定、復活中に余分な閾値通知を出さない規則も固定CPU版に合わせています。HP閾値通知と同じ文字列の明示的な通知は別のイベントとして扱います。

ネイティブ版とPTX版の両方で、基本24件・通知名の区別3件・実スキル部隊12件の計39件を照合しました。部隊合計と5人のダメージ、バースト履歴、乱数状態、HP・遮蔽物HPの各フレーム、最終の弾数・チャージ・戦闘不能状態を比較しています。整数結果と通知順序は一致、HP等は相対1e-12／絶対1e-6の許容差で確認しています。A2のBモード解除、ソリン：フロストチケットの回数判定、フローラの中央・両端の配置を含みます。通常経路の95テストと、通常API・ブラウザーのGPU単独／CPU照合付き計算も成功しています。記録は `research/detail-hp-edge-checkpoint.json`、再現用の架空データは `research/detail-hp-edge-ui-fixture.json` です。

現在のコンパイル対象は203体中150体、愛用品の812条件中589条件です。新たにA2が通り、これまでコンパイルできていた味方・隣接HP通知も、今回の戦闘テストで発動を確認しています。この件数は全キャラ・全編成の戦闘一致を意味しません。失ったHPへの比例、遮蔽物の復活・一部の制御、回復超過分の蓄積、敵のデバフ・継続被弾、座標などには未対応条件が残ります。実アカウントからの取得成功や高速化率を保証する検証ではありません。

仮ステータスは部隊全体を毎回計算します。今回の通常画面の例はA2の攻撃力+12,000／HP+100,000／防御力+250で、197,889,526から194,933,444へ変化し、CPU版とも一致しました。上昇分がそのまま部隊ダメージの上昇を保証するわけではありません。目標探索も候補ごとに評価します。以下はv34以前の各版時点の記録です。

'''
text=text.replace(heading,heading+addition)
text=text.replace('現在のコンパイル対象は203体中149体','v34時点のコンパイル対象は203体中149体')
text=text.replace('HP閾値をまたいだ発動、敵のデバフ・継続被弾、座標や一部の特殊効果は残っており、','v34時点ではHP閾値をまたいだ発動、敵のデバフ・継続被弾、座標や一部の特殊効果が残っており、')
text=text.replace('ABIは`detail_survival_v34`、1部隊のGPU作業領域は1,049,568バイトです。','ABIは`detail_hp_edge_v35`、1部隊のGPU作業領域は1,074,184バイトです。')
text=text.replace('座標による命中、個別パーツの移動、HP閾値イベント、敵からのデバフなどには未対応の条件が残っています。','座標による命中、個別パーツの移動、失ったHPへの比例、敵からのデバフなどには未対応の条件が残っています。')
p.write_text(text,encoding='utf-8')
p=ROOT/'research/boss-gpu-integration-notes.json';notes=json.loads(p.read_text(encoding='utf-8'))
notes.update(status='v35 HP-edge native/PTX39, pre-CUDA boundary5 and production95/API/browser acceptance passed. All-effects objective remains incomplete.',objective_complete=False)
notes['current_boundary']['gpu_compiler']='v34 live incoming/down/revive plus GPU-owned HP crossing/count and squad/adjacent/max transition notifications; synchronous recipient order and reentrancy guard. Remaining lost-HP scaling, cover revival/storage, debuffs/geometry and unsupported definitions still reject.'
notes['verification_v35']=dict(abi='detail_hp_edge_v35',workspace_bytes_per_squad=1074184,staged_archive='research/ports/v35-hp-edge-staged-verified',cases_per_backend=39,authored_cases=24,namespace_cases=3,actual_skill_squads=12,normal_tests=95,pre_CUDA_boundary_tests=5,api='research/detail-hp-edge-api-verification.json',browser='research/detail-hp-edge-browser-verification.json',compiled_characters=150,catalog_characters=203,favorite_contexts=589,favorite_total=812,objective_complete=False)
notes['next_required_work']=[x for x in notes['next_required_work'] if x['area']!='HP-edge triggers and remaining survival effects']
notes['next_required_work'].insert(0,dict(area='Remaining HP and cover effects',requirements=['Port dynamic lost_hp_pct value queries without multiplying stacks; use research/detail-lost-hp-cpu-reference.json (eight CPU-only cases).','Implement cover revival/random broken-cover targets using research/detail-cover-revival-cpu-reference.json (nine CPU-only cases); cover control and heal-overcharge storage still need implementation.','Continue remaining character/favorite contexts, enemy debuffs/DOT, geometry and upstream omissions. Compilation success is not all-battle parity.']))
p.write_text(json.dumps(notes,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Published v35 documentation after normal95/API/browser acceptance.')
