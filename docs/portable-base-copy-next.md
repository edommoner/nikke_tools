# 次の高優先機能：基礎ATK／HPコピー

この文書は接続前の計画です。その後の共通実装・Metal481の結果は`docs/portable-base-copy.md`に記録しています。

2026-10-22のinventoryは266profile中193packing、基本134/203、110分類です。projectile_dmg_pctとshield_dmg_pctの上位分類は、参照側の実consumerを確認できておらず、効果なしでの受付はしません。次の接続候補は、単独の観測分類が2profileにあるhp_copyと、同じlifecycleを共有するatk_copyです。GPU対応はまだありません。

## 再利用する参照

`app/base_copy_runtime.py`と`app/lifecycle_specs.py`に既存の実行規約があります。pinned upstreamがもともと処理しなかったstatを、既存アプリ側の明示的なモデル補正で扱っています。この参照をportable結果に合わせて変更しません。基礎値順で選ぶ点を、表示上の最終ATK／HP順位へ置き換えません。

既存の`verify-base-copy.py`の独立8ケース／25観測をCPUだけで再確認しました。GPU呼出を禁止し、期待値と実際のBuffManagerを照合しています。証拠は`research/portable-base-copy-native-prerequisite.json`です。これはportable GPU成功ではありません。

## 共通実行器へ必要な接続

1. 生selectorは既存CopyPolicyの許可値だけを受け付け、stat85／86を64項目の数値ベクトルへ誤ってindexしない。kind、余剰field、duration_bullets、stack、sourceの不正wireも拒否する。
2. 正確な生carrierのprepare段階で、生存者の基礎ATK／HPからsourceとbasisを決める。部隊順のtie、self、同じ定義の別recipient carrierを区別する。CPUが選んだsourceをGPUへ入力しない。
3. prepare後の子イベントは準備済みbasisを観測する。HP付与は子イベント後の同一carrierにだけ行い、途中で削除・再利用されたslotへ誤って付与しない。basis、source、前回giftとcarrier世代を保持する必要がある。
4. stackに応じた現在寄与と、実発動時の前回gift差分を区別する。refreshだけで再回復しない。stack初期化は最大HPへ寄与してもHP付与なし。失効時の最大HP・HP割合同期も既存規約へ接続する。
5. 独立境界fixtureを既存world/native比較へ接続し、copy状態のGPU観測も追加する。実キャラ全定義、通常の対象処理、子によるrecipient解除、親削除→slot再利用まで含め、最後に集約regressionへ組み込む。

記憶領域はcompiler制約も考慮して選びます。今回のlazy-bank変更に便乗して配列を移すのではなく、新機能に必要な状態量と寿命を先に固定します。CUDA／Metalで同じ定義・state・event hook・fixtureを使います。

## 復活の扱い

reviveも上位ですが、HPを戻すだけでは対応になりません。pinned BuffManager.reviveはdown解除、失ったpassiveの再適用、その後の最大HP基準でのHP復帰を行います。CharState.on_reviveは行動をresetし、満弾・次射撃時刻を復帰時刻へ設定します。現portable knockDownはcarrierのrecipientを取り除き、空carrierを破棄します。復元用状態の設計と同フレームのdown通知→復活→射撃順が必要なので、基礎コピーと混ぜて簡略化しません。

## 分類の整備

未知fieldは例外のreasonとfieldsを直接渡すようにし、診断文を変更しても分類codeが変わらないテストを追加しました。全266profileでpacking、全input hash、分類codeと順位は不変。効果の文言フォールバック44→25、program27→14です。この2集計は同じ不足を重複観測するため合算しません。GPU受付は広げていません。
