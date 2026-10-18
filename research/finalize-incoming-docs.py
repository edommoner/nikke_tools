"""Update review documentation only after the v33 acceptance reports pass."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
checks=[('research/detail-incoming-native-verification.json','cases',80),('research/detail-incoming-ptx-verification.json','cases',80),('research/detail-incoming-long-verification.json','cases',4),('research/detail-incoming-lifecycle-verification.json','cases',4),('research/detail-normal-acceptance.json','tests_run',86)]
for path,key,n in checks:
 r=json.loads((ROOT/path).read_text(encoding='utf-8'));assert r['passed'] and (len(r[key]) if key=='cases' else r[key])==n,path
 assert all(hashlib.sha256((ROOT/f).read_bytes()).hexdigest()==h for f,h in r['source_sha256'].items()),'stale '+path
api=json.loads((ROOT/'research/detail-incoming-api-verification.json').read_text(encoding='utf-8'));assert api['passed'] and api['incoming_hits_verified'] and api['compute']['backend']=='cuda_detail'
p=ROOT/'README.md';text=p.read_text(encoding='utf-8')
paragraph='敵からの攻撃を既存の部隊シミュレーションへ組み込むv33を追加しました。敵専用の乱数列で全体・位置・ランダム・攻撃力順の対象を選び、隠れ身・挑発、最終防御力と被ダメージ補正、シールド→遮蔽物→分身→HP、不屈・無敵・被ダメージ分配、被弾からのスキル発動をGPUで処理します。遮蔽物の回復対象は、その場の残率で選び、破壊済みを除外します。戦闘不能・復活はまだ未対応で、致死ダメージになった戦闘のGPU結果全体を破棄し、通常画面では理由付きでCPUへ切り替えます。敵のデバフ・継続被弾、座標などの移植も残っています。'
proof='v33はネイティブ80条件・PTX80条件、180秒の実スキル部隊4件、行動の繰り返しと同一フレームの対象変更4件でCPUと照合しました。追加で通る10体は実スキルを残した部隊で被弾あり・なしを検証しています。ダメージの整数出力とバースト履歴は一致し、被弾履歴の量は小数6桁に正規化して一致、毎フレームの内部HP・遮蔽物HPは相対1e-12／絶対1e-6の許容差で比較します。通常経路の86テスト、APIのGPU計算・CPU照合・まとめ計算・キャッシュ分離も通過しました。作業領域は1部隊1,039,256バイトです。コンパイル可能なのは収録203体中145体、愛用品段階の812条件中569条件であり、全キャラ・全組み合わせの検証完了ではありません。記録は`research/detail-incoming-checkpoint.json`、通常画面へ読み込める架空データは`research/detail-incoming-ui-fixture.json`です。保存データのUIパーサーは検証済みですが、この段階でブラウザー操作を再検証したという主張ではありません。実アカウント読込や高速化率は証明していません。'
if paragraph not in text:
 marker='## 詳細GPU版の実装・CPU照合\n\n';assert marker in text;text=text.replace(marker,marker+paragraph+'\n\n'+proof+'\n\n',1)
old='ロザンナは別の未対応効果「隠れ身」が残るため、敵バフ解除の対応だけでキャラ全体のGPU対応完了には数えていません。'
if old in text:text=text.replace(old,'v32時点ではロザンナの「隠れ身」が未移植だったため、敵バフ解除だけではキャラ全体の対応に数えていませんでした。v33では隠れ身と実スキルの部隊計算を検証しています。',1)
text=text.replace('これは次の移植のための参照であり、GPUで敵の攻撃や生存処理を実装済みという証拠ではありません。','このCPU側19条件の記録自体は、GPU実装の証拠ではありません。v33の実行証跡は上記の別記録です。',1)
text=text.replace('詳細は`research/detail-boss-buffs-checkpoint.json`に記録しています。','v32当時の記録とソースは`research/ports/v32`に保存しています。',1)
text=text.replace('GPUで対応するボス行動はcore／move／idle／groggy／buffです。','GPUで対応するボス行動はcore／move／idle／groggy／buff／attackです。',1).replace('ABIは`detail_boss_buffs_v32`、1部隊のGPU作業領域は639,216バイトです。','ABIは`detail_incoming_v33`、1部隊のGPU作業領域は1,039,256バイトです。',1).replace('座標による命中、個別パーツの移動、敵からの攻撃・遮蔽物・戦闘不能などは未対応です。','座標による命中、個別パーツの移動、戦闘不能・復活、敵からのデバフなどは未対応です。',1)
text=text.replace('新しいボス条件はnative／PTX計40ケース、','v31のボス条件はnative／PTX計40ケース、',1)
p.write_text(text,encoding='utf-8')
notes=ROOT/'research/boss-gpu-integration-notes.json';r=json.loads(notes.read_text(encoding='utf-8'));r['status']='v33 incoming runtime verified on native/PTX80 each, long4, lifecycle4, normal86 and ordinary API. Full all-effects objective remains incomplete.'
r['verification_v33']={'native_cases':80,'ptx_cases':80,'long_raw_squads':4,'lifecycle_cases':4,'normal_tests':86,'api_total':api['total'],'compiled_characters':145,'catalog_characters':203,'compiled_favorite_contexts':569,'total_favorite_contexts':812,'browser_interaction_verified':False,'objective_complete':False}
notes.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('v33 review documentation updated; full GPU objective remains incomplete.')
