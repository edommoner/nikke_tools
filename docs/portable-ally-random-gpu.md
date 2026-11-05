# 味方ランダム対象の共有GPU接続

`allies_random:N`（本人を除く生存者）と `allies_broken_cover_random:N`（本人を含む、生存かつ遮蔽物破壊済み）を共通Slangへ接続した。正本compilerのselector19/25を使い、復活のclass-random選択と同じ既存MT19937状態を共有する。敵用乱数には触れない。新しいRuntime fieldはなく、stride138952・CUDA定数48Bを維持した。

buffは既存の `(caster, raw target, activated_at)` 遅延cacheへ接続し、source欄の異なる同時発動も共有する。即時効果は発動ごとに候補をGPUで構築する。空・人数0は乱数stateを進めず、1人・全員選択も正本通り消費する。RECIPIENT_METAの予約3wordにtagとuint64 seedを入れ、復活seedが同居するときは一致を要求する。味方選択だけでは復活のlost-definition管理を有効にしない。

選択のpool/order/index前後を既存128件のrevival trace bankにkind3として記録する。容量超過はerror64。新入力にCPUの選択結果・発動時刻表は渡さない。名前付き状態の表示も実際のGPU順序を読む。遮蔽物破壊はGPU着弾時に既存schedule logへkind7として記録し、cover_reviveは既存の対象処理・復旧処理へ受付を接続した。数値式は変更していない。

## 検証結果

- 不変packet `/tmp/nikke-ally-random-gpu-v4`：30入力、20正例・10拒否。Apple M5で成功し、独立fresh CPU sealも成功。CPU21群127検査24.348秒、GPU0.045096秒。固定済み18契約に人数0・発動上限2の契約を加え、全戦闘項目・skill trace・選択順・完全なMT stateのSHAを照合した。
- 不変packet `/tmp/nikke-ally-random-retention-v1`：旧1234入力、980正例・254拒否。同じ116sourceで成功し、独立sealも成功。旧3familyの全entriesとraw3,881,828,352Bが全byte一致。CPU事前68.124秒＋79群449検査143.591秒、GPU10.318523秒。生成cacheは必須hit、追加Slang0。親のnative896件を再利用、84件はfresh、独立sealは再利用しない。
- 保存済み新rawへpool/order/index/MT state/sample count/復活counterの6故障を注入し、全て拒否。GPU再実行0。
- 成功済み別captureのゼロ領域割当2,159,017,984Bを回収。raw内容・SHA・長さ・パス・inodeを保持、削除0。保持実行前に非圧縮入出力約4.40GB＋14GiB予備を確認した。今回の保持rawも独立sealと全byte比較後に同じ処理を行い、さらに2,758,803,456Bを回収し、完全SHAを再確認した。

最初のCPU停止（古い未対応期待）、Metal差分、受付診断、監査用substringのCPU停止は原packet/raw/claimとともに保存した。GPU期待値や許容誤差を差分に合わせて書き換えていない。kind30追加を旧監査の検査する並びの後ろへ移し、検査点を維持した。

分類更新後の最終不変packetもCPU21群127検査に成功。Metal実証版とのsource/input/全30件native指紋を保持し、GPUの再実行はない。

## CLIと残件

```sh
python scripts/nikke_gpu.py package --suite ally-random-gpu --develop --out /tmp/nikke-ally-random-next.zip
python scripts/nikke_gpu.py unpack --archive /tmp/nikke-ally-random-next.zip --dest /tmp/nikke-ally-random-next
```

展開先から既存 `run --backend metal` を使う。既に消費したcapture/claimを再利用しない。保存結果の `seal` はGPU0。新しい実証goldenは保存したが、2suiteは `development_only` を維持し、旧golden群と本体compiler証明のpromotionはまだ行っていない。

混在するrevival/randomの順序・共有bank、ordered random buff list、debuff型、実キャラ全定義を追加検証する。遮蔽物・カメラ条件とfocus_fire marker/aimの接続は次のsource batchにまとめる。現sourceのCUDA実行は未検証。Windowsは操作0、7プロセス終了の原因unknown・保全falseを維持する。静的packingは再集計前であり、今回から全キャラ対応を認定しない。全キャラ認定0、通常UIはCPU、ゴール未達。

出所とSHA、停止記録、容量・保持検査は `research/portable-ally-random-gpu-checkpoint.json` にまとめた。
