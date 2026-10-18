"""Describe only the production v36 results that have actually passed."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
normal=json.loads((ROOT/'research/detail-normal-acceptance.json').read_text(encoding='utf-8'));assert normal['passed'] and normal['tests_run']==108 and not normal['skipped']
for path in ('research/detail-survival-scaling-api-verification.json','research/detail-survival-scaling-browser-verification.json'):
    assert json.loads((ROOT/path).read_text(encoding='utf-8'))['passed']
p=ROOT/'README.md';text=p.read_text(encoding='utf-8');assert '## GPU詳細計算 v36' not in text
section='''## GPU詳細計算 v36

通常画面の「GPU詳細（対応編成）」と「GPU詳細＋CPU照合」で、残HPに比例する効果量、遮蔽物の復活、破壊済み遮蔽物からの対象抽選、生存中の遮蔽物を条件にする効果を計算します。モラン・ビスケットを含む実スキルの検証を追加しました。所持・装備・スキル・配置と仮ATK/HP/DEFは従来と同じ画面から反映できます。

専用28ケースと実スキルを保持した12ケースをnative／PTXそれぞれで照合し、既存のHP・戦闘不能・復活88ケースもPTXで確認しました。被弾のストレス検証では専用の不屈効果を追加するケースを含みます。通常画面の検証データにはその追加を行いません。部隊合計・5人の整数ダメージ・バースト・HP/遮蔽物の推移・最終乱数状態を比較します。通常経路の108テストと、API／画面からのGPU単独実行・CPU照合も通過しました。

`research/detail-survival-scaling-checkpoint.json` に受け入れ結果をまとめています。`research/detail-survival-scaling-ui-fixture.json` は通常画面で読み込める架空の所持・装備データです。モランを含む5人部隊は95,753,434→仮ステータス変更後99,208,302でCPUと一致しました。これは実アカウント取り込み成功や高速化の証明ではありません。

コンパイル可能なのは通常キャラ152/203人、宝もの等の組み合わせ597/812条件です。コンパイル成功は全編成での一致を意味しません。ベイの被ダメージ分配、最大HP参照の未対応形式、回復量の蓄積、遮蔽物の制御、敵デバフ・DOT、座標などには未対応が残ります。未対応の定義はCPUへ切り替えます。

固定CPU版では復活中にHP割合を一時的に未設定とし、モランの残HP参照が例外になります。`app/survival_scaling_compat.py` は既存の復活処理が保持する予定復活割合を、その値の照会中だけ使います。元データ・固定エンジンのファイルを変更せず、HP通知を追加しません。11件の境界テストに通常時・復活外の例外・例外時の復元も含めています。CPU一致はこの互換処理を含む固定版との一致です。

'''
text=text.replace('## 起動\n',section+'## 起動\n',1);p.write_text(text,encoding='utf-8')
p=ROOT/'research/boss-gpu-integration-notes.json';j=json.loads(p.read_text(encoding='utf-8'))
j['status']='v36 lost-HP/cover-revival native/PTX40 each, PTX legacy88, boundary11, production108 and API/browser acceptance passed. Full objective incomplete.'
j['current_boundary']['gpu_compiler']='v36 dynamic lost-HP values, cover revival/random broken-cover recipients and live cover-alive gates, plus earlier incoming/down/revive and HP crossing notifications. Unsupported definitions still reject.'
j['current_boundary']['verification']='Independent whole-squad integers, member damage, bursts, both RNG streams, every-frame HP/cover/control and HP event order; explicit CPU revival condition/value bridges. CPU traces never enter GPU inputs.'
j['next_required_work'][0]['requirements']=['Continue max_hp-based cover capacity and unsupported received_dmg_split definitions; Bay remains rejected with full raw skills.','Cover controls, heal-overcharge storage, enemy debuffs/DOT, geometry and upstream omissions remain. Compilation success is not all-battle parity.']
j['next_required_work'][1]['requirements']=['Attack-attached debuffs, enemy debuff/DOT patterns, cover controls, healing/storage/splitting and all remaining unsupported actual effects.','Resolve pinned CPU omissions before treating equal omissions as game correctness.']
j['survival_scaling_checkpoint']='research/detail-survival-scaling-checkpoint.json';j['objective_complete']=False
p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Updated v36 scope, passed evidence and explicit remaining work.')
