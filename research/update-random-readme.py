from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];p=ROOT/'README.md';s=p.read_text(encoding='utf-8')
heading='## 詳細GPU版の実装・CPU照合\n\n'
assert heading in s and 'ランダム対象選択（v20）' not in s
text='''ランダム対象選択（v20）を戦闘カーネルへ統合しました。CPUが決めた対象や戦闘履歴をGPUへ渡さず、GPU内でCPython互換の乱数生成と順序付き抽選を実行します。「詳細条件」の「対象抽選の乱数シード」は0〜4294967295の整数で、未指定・旧保存データは0です。CPUとGPUで同じ値を使い、結果・比較基準・キャッシュ・保存JSONにも反映します。クリティカル等は引き続き期待値です。

発動回数制限の前後の抽選、空の候補、解除不能デバフの保有判定、同時付与で共有する遅延対象、元の効果が消えた後も残す対象キャッシュ、順序付きリスト、継続回復・解除、消滅時とフルバースト記録時の対象参照をCPU版に合わせました。特殊な攻撃力配布・HP変換の対象は、時刻とバフ更新ごとに再評価します。

native／PTX計244ケースで部隊合計・5人の内訳・基礎ステータス・バースト履歴・最終の乱数状態が一致しました。ココアは全スキルを維持し、検証用デバフを実際に解除する3シード×2ゲージ設定も含みます。記録は `research/detail-random-target-native-verification.json`／`research/detail-random-target-ptx-verification.json`、CPU側の正の対照は `research/detail-random-real-positive.json` です。

通常画面でも、架空育成の5人をキャラ別射撃・マスト周期・実蓄積・シード12345で計算し、GPU実行の合計243,679,868とCPU照合済み表示を確認しました。記録は `research/detail-random-ui-verification.json` です。v20の全回帰テスト118件と通常APIの追加確認は実行中です。

現在のコンパイル受理は117／203人、宝ものを含む監査は459／812条件です。全キャラ・全効果の移植は未完了で、コンパイル受理は全編成の一致を意味しません。ランダム対象キャッシュは1編成1024組までで、上限超過や未対応の効果はGPU結果全体を破棄してCPUへ切り替えます。固定の静止ボス・期待値モードの範囲であり、ボスの実パターンや生存の検証は残っています。

'''
s=s.replace(heading,heading+text)
s=s.replace('ランダムな対象選択は戦闘エンジンへ未統合で、ココア等の未対応効果を含む部隊はCPUへ切り替えます。','v19時点ではランダムな対象選択は未統合で、ココア等はCPUへ切り替えていました。v20で上記の範囲を追加しています。')
s=s.replace('戦闘エンジンへの組み込み、デバフ保有者の絞り込み、ココア等の実編成での照合はこれからです。','この独立部品の段階では戦闘へ未統合でした。v20でデバフ保有者の絞り込み、ココアの実編成の照合まで追加しています。')
p.write_text(s,encoding='utf-8');print('Documented verified v20 scope; full118/API still explicitly pending.')
