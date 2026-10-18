"""Publish current scope only after ordinary production and browser acceptance."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
tests=json.loads((ROOT/'research/detail-normal-acceptance.json').read_text(encoding='utf-8'))
api=json.loads((ROOT/'research/detail-survival-api-verification.json').read_text(encoding='utf-8'))
browser=json.loads((ROOT/'research/detail-survival-browser-verification.json').read_text(encoding='utf-8'))
assert tests['passed'] and tests['tests_run']==87 and not tests['skipped']
assert api['passed'] and api['compute']['backend']=='cuda_detail' and api['compute']['cpu_verification']['matched']
assert browser['passed'] and browser['browser_interaction_verified']
path=ROOT/'README.md';s=path.read_text(encoding='utf-8')
heading='## 詳細GPU版の実装・CPU照合\n\n'
assert heading in s and 'v34では戦闘不能・復活' not in s
addition='''v34では戦闘不能・復活を部隊シミュレーション内でGPU処理します。受けた効果の解除、復活時に残す効果、パッシブの復元、個人カウンターのリセットと部隊共通カウンターの継続、継続ダメージ・回復の既存タイマー、武器変更中の行動停止、復活後の弾数・チャージ・バースト再開を扱います。ラプンツェル、アン：ミラクルフェアリー、マナなどを実スキルを残した部隊で照合しています。回復量アップ効果の対象確定漏れも、ダメージ合計だけでなく各フレームのHPを比較して修正しました。

最終版ではネイティブ／PTXそれぞれ、回復3ケースと戦闘不能・復活49ケースを照合しました。ネイティブ版では、致死攻撃を繰り返す180秒の実スキル部隊4件も確認しています。整数のダメージ・バースト履歴・乱数状態・戦闘不能状態は一致、内部HP・遮蔽物HP・最終行動状態は相対1e-12／絶対1e-6の許容差で比較しています。CPUが復活中のHP条件判定で例外になる問題は、固定した上流ファイルを変更せず、明示した互換処理で修正しています。通常経路の87テストには、バースト段階・再入場のネイティブ56ケースも含みます。通常APIでのGPU実行とCPU照合、所持・装備と仮ステータスを復元したブラウザーからの計算も確認しました。記録は `research/detail-survival-checkpoint.json`、画面で試せる架空データは `research/detail-survival-ui-fixture.json` です。

バースト候補の順序と待機、段階変更の効果が切れた後の停止、戦闘不能のバーストⅠを含む編成条件はCPU版の規則に合わせました。最後の編成条件は4秒の戦闘で正負の条件と復活の有無を確認し、実際の効果発動も観測しています。修正前の不一致とコードは `research/ports/v34-production-before-burst-wait-fix`、`research/ports/v34-before-b1-ally-fix` に残しています。

現在のコンパイル対象は203体中149体、愛用品の812条件中585条件です。これは全組み合わせの戦闘一致を示す数ではありません。HP閾値をまたいだ発動、敵のデバフ・継続被弾、座標や一部の特殊効果は残っており、未対応条件はCPUへ切り替えます。実アカウントからの取得成功や、高速化率を保証する検証ではありません。以下のv33以前の記録は各版の検証範囲です。

'''
s=s.replace(heading,heading+addition)
s=s.replace('戦闘不能・復活はまだ未対応で、','v33時点では戦闘不能・復活が未対応で、')
s=s.replace('ABIは`detail_incoming_v33`、1部隊のGPU作業領域は1,039,256バイトです。','ABIは`detail_survival_v34`、1部隊のGPU作業領域は1,049,568バイトです。')
s=s.replace('座標による命中、個別パーツの移動、戦闘不能・復活、敵からのデバフなどは未対応です。','座標による命中、個別パーツの移動、HP閾値イベント、敵からのデバフなどには未対応の条件が残っています。')
path.write_text(s,encoding='utf-8')
path=ROOT/'research/boss-gpu-integration-notes.json';notes=json.loads(path.read_text(encoding='utf-8'))
notes['status']='v34 down/revive and blocked-stage correction verified on native/PTX; normal87 and ordinary API/browser acceptance passed. Full all-effects objective remains incomplete.'
notes['objective_complete']=False
notes['current_boundary']['gpu_compiler']='core/move/idle/groggy/buff/attack; live incoming layers and true down/revive, passive restoration/persistence, down-aware recipients, original burst candidate order and waits. Unsupported HP-edge/debuff/geometry and other definitions remain fail-closed.'
notes['current_boundary']['verification']='Whole-squad integer results, burst logs, both random streams, down masks, read-only HP/cover frame witnesses and final action state are compared to the pinned CPU engine with the explicit revival HP-condition bridge. CPU traces never enter GPU input.'
notes['verification_v34']=dict(abi='detail_survival_v34',archive='research/ports/v34-survival-final-staged-verified',native_survival_cases=49,ptx_survival_cases=49,native_burst_cases_in_normal_suite=56,heal_cases_per_backend=3,native_repeated_lethal_long=4,normal_tests=87,previous_extended_matrix_archive='research/ports/v34-burstfix-staged-verified',previous_matrix_is_before_final_b1_predicate_fix=True,api='research/detail-survival-api-verification.json',browser='research/detail-survival-browser-verification.json',rejected_normal_acceptance='research/detail-survival-rejected-normal-acceptance.json',objective_complete=False)
notes['down_revive_gpu_followup']=dict(implemented=True,scope='Authored supported definitions and tested rosters; not every effect/character combination.',reports=['research/detail-survival-b1-native-full.json','research/detail-survival-b1-ptx-full.json','research/detail-survival-b1-native-repeated-long.json'])
notes['next_required_work']=[x for x in notes['next_required_work'] if x['area']!='Actual down/revive runtime']
notes['next_required_work'].insert(0,dict(area='HP-edge triggers and remaining survival effects',requirements=['Port threshold crossings, counted crossings, squad/adjacent observer order and reentrancy guards; preserve the no-edge-on-revive sentinel. CPU-only eight-case groundwork is research/detail-hp-edge-cpu-reference.json.','Extend independent whole-squad acceptance to remaining revival characters/variants and resolve all unsupported effect/data/model omissions.']))
path.write_text(json.dumps(notes,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Updated current v34 documentation after production/API/browser acceptance.')
