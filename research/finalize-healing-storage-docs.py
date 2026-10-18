"""Document accepted v40 reserve semantics, evidence and remaining full goal."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
focused=json.loads((ROOT/'research/detail-healing-storage-production-verification.json').read_text(encoding='utf-8'));assert focused['passed'] and focused['tests_run']==11 and not focused['skipped']
for path in ('research/detail-healing-storage-api-verification.json','research/detail-healing-storage-browser-verification.json'):assert json.loads((ROOT/path).read_text(encoding='utf-8'))['passed']
p=ROOT/'README.md';s=p.read_text(encoding='utf-8');assert '## GPU詳細計算 v40' not in s
section='''## GPU詳細計算 v40

余剰回復を保存する `heal_overcharge_store` をGPUで処理します。通常HP・最大HP・HP条件判定とは別の保存枠として持ち、超過した体力回復/吸血で蓄積し、体力に届く攻撃や現在HP消費で先に使います。遮蔽物・シールド・デコイ・無敵が防いだ分では消費しません。期限切れで失われ、復活や最大HPの付与自体では補充しません。

固定CPU版には保存処理がなかったため、`app/healing_storage_compat.py` でCPU参照モデルも補完しています。容量は発動時の発動者の最終最大HPを使うスナップショット、再付与は新容量以下で残量維持、異なる保存枠は新しい発動順・同時刻は保持順で扱うというモデルです。これら全相互作用を実機で検証したという意味ではありません。マルチャーナの同時発動は、[保存の付与後にスキル2で回復する説明](https://wiki3.jp/nikke/page/3640)に合わせ、該当するスキル3保存/スキル2回復の定義順をCPU/GPU共通で補正しました。数量のCPU再生をGPUへ渡す処理ではありません。

基本8、追加16（重複/同時刻、容量スナップショット、期限切れ再利用、遅延/重複対象、回復補正、戦闘不能/復活、HP条件、デコイ/無敵など）、実スキルを省かない5部隊、既存124を、native/PTXそれぞれ153ケースで照合しています。部隊合計・5人のダメージ・バースト・基礎値・HP/遮蔽物推移・両乱数状態などを比較し、保存用の29ケースでは名前別残量・容量・保持数も毎フレーム比較します。実キャラはメイドアンカー、センチ通常/宝もの3段階、ソラ、マルチャーナです。センチ通常では保存が付かない負の対照を保持し、ソラにはパーツ破壊用の刺激を追加しています。同じバーストのスキル2回復でマルチャーナの保存が満たされることも別に確認しました。

独立したCPU参照21件、CPU部隊13件、保存前の固定されたv39部隊合計124件との完全一致、境界7件を確認しました。通常経路の重点11テスト（153部隊ケースと境界7件）、API/画面のCPU照合付き/GPU単独、Node26件も通過しています。全通常テストの再実行という記録ではありません。1部隊の作業領域は実際のGPUシンボル/APIで1,078,280バイトを確認しています。

`research/detail-healing-storage-checkpoint.json` に検証範囲を保存します。`research/detail-healing-storage-ui-fixture.json` は架空の所持・装備データです。マルチャーナ/ヒーリングキューブLv4/スキル7・5・9/複数枠のオバロを含み、30秒・ゲージ実蓄積で、89,771,061から仮ATK＋12,000/HP＋100,000/DEF＋250で92,423,691となります。実アカウント取り込みと高速化は未検証です。

固定版データの通常159/203人、宝もの等627/812条件が変換可能です。この集計は全編成での一致を意味しません。ATKを上限に回復を累積・放出する別機構、回復量の分配、シールド関連効果、被ダメージ分配、敵デバフ/DOT、座標やCPUモデルの不足などが残っています。全キャラ・全特殊効果のGPU化は継続中です。

'''
needle='## GPU詳細計算 v39\n';assert needle in s;s=s.replace(needle,section+needle,1);p.write_text(s,encoding='utf-8')
p=ROOT/'research/boss-gpu-integration-notes.json';j=json.loads(p.read_text(encoding='utf-8'));j['status']='v40 overheal reserve and same-cast storage/S2 ordering: native/PTX153 each, CPU21 and13, historical CPU totals124, boundary7, production11, API/browser and Node26 passed. Full objective incomplete.'
j['current_boundary']['gpu_compiler']='v40 supports separate overheal reserve capacity, fill/spend/expiry/refresh, source snapshots, ordered overlap, same-cast S3-storage/S2-heal normalization, and prior paths. Other unsupported effects still reject.'
j['next_required_work'][0]['requirements']=['Continue ATK-based heal_overcharge_store_atk_pct/discharge and heal_split with explicit CPU/GPU models and source-based mechanics research.','Continue shield_dmg_pct/Misato, received_dmg_split/Bay, cover controls, enemy debuffs/DOT, geometry and CPU/model omissions.']
j['healing_storage_checkpoint']='research/detail-healing-storage-checkpoint.json';j['objective_complete']=False;p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print('Documented verified v40 storage scope and full unfinished objective.')
