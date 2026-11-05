# ダメージ蓄積：共通GPU接続前の正本契約

共通CLI `reference --suite damage-accum --out <new.json>` に52契約を登録した。対象は `dmg_accum_dealt_atk_pct`、`dmg_accum_received_atk_pct`、`dmg_accum_rate_pct`、`accum_split_damage`。正本の計算・共通Slang・数値primitiveは変更していない。新しい蓄積系のGPU受付は閉じたままで、今回はMetal/CUDAによる新機能の計算証明ではない。

## 固定した順序と量

生成時の付与者final ATK×値/100を容量snapshotへ保存する。負容量もそのまま保持する。再付与は量と同名archiveを0へ戻す。各carrierはscalar poolで、受け手ごとのpoolではない。

正本のboss着弾で、実際のdamage creditと吸血が済んだ後の正のdamageを収集する。dealtグループ、receivedグループの順に走査し、前者はdamage付与者一致、後者は付与者を問わない。対象所属やlive条件による追加filterはない。addsへのdamageは収集しない。aimed targetの着弾は別経路で、この52契約による認定外である。

rateは同じ付与者のstat83をactive順で読む。無名の基礎率と同名の加算率は別々に順序付きで合計する。基礎率なしは100%、明示0は0%である。値field自体がない場合と空valuesの0は異なる。1e16、-1e16、1の加算順も契約に含む。lost_hp_pctは正本の_get_valueと同じく失ったHP百分率を乗じ、吸血後のHPを読む。

量は `min(current + damage * rate /100, cap)`、負率は負量を作り得る。`current >= cap -1e-9` でdoneになる。すべてのpool更新後にfull通知を配送し、通知順はdealt→receivedである。途中のcallbackが別carrierを変えても、既に捕捉した通知列の扱いを変えない。

放出はrequester/ownerを問わず、global active順で最初の同名carrierを1個だけ消費する。doneの0量carrierも後続を隠す。activeがなければbattle-globalの名前archiveを使う。取り出したcarrierを0/doneへ変え、archiveも0へ戻す。解除・down後にも名前archiveが残る場合があり、回復蓄積のowner別retentionとは異なる。

放出量が正なら現在のsplit倍率だけを加え、共通の整数切捨てへ渡す。防御・攻撃力・criticalを再適用しない。split=true、critical=falseのpacketを既存damage経路へ出し、その着弾は別poolへ収集され得る。

## 観測と検証

不変package `9a6e80f128825ab09e84e33d52584c85ffdc3580d75c74143128ba296cd1dfce` をfresh展開し、52契約が9.827秒、関連10検査が10.367秒で成功した。GPU build/executeとpackingはすべて0。既存回復系の通常CLI5群31検査も9.952秒で成功した。

観測器は正本のactivate、collect、rate、takeのcall/return、実際のfull通知とHitEventを記録する。pool/archiveはfield読取だけで、追加のATK・buff・rate照会を行わない。全52入力の完全なbattle/trace/RNGを無観測の正本と比較し、照会/callback数も検査した。量、cap、done、通知順、emissionへの故障注入は拒否される。これは宣言モデルの契約で、ゲーム内の全相互作用を実証したものではない。

初回の1900対1800の期待誤り、未移植敵carrierの観測分類失敗、refreshの2発目、散弾係数分配、adds除外を記録した。元の2発refresh入力は900の正例として残し、clip1/reload10による0の対照を追加した。nativeが使わないpost_fire_delaysで待機を変える試みは取り下げた。失敗package・診断・raw・claimを削除していない。

敵carrier観測器は、portable lowering未実装でも実際のtarget_charsに敵があれば敵所属へ分類するよう修正した。このreader変更について、旧Metal398入力(native302/拒否96)の保存rawを共通replayで再照合し、fresh childの独立sealが登録goldenと完全一致した。全entry/input/native/output指紋、143 GPU source、1,251,999,744Bのrawを保持。GPU再実行は0である。この保持確認を新しい蓄積系のGPU成功として数えない。

全266profile記録・242input SHAを保持。静的packing242/266、base182/203、未対応30分類のままで、laneはcontract extension6/model gap10/reference review14。全キャラ認定0、UI CPU、目標未達。Windows追加コマンド0、現CUDA実行未確認。過去7プロセス終了の原因はunknown、環境保全falseを維持する。利用者のゲーム/動画利用と終了を結び付ける証拠はない。

保存rawのゼロ領域だけを回収し、1,271,791,616Bの割当を解放した。raw削除0、全byte/SHA/path/inodeを保持した。証拠はresearch/damage-accum-reference-evidence/、checkpointはresearch/portable-damage-accum-reference-checkpoint.json。

## 次の共有実行器接続

既存object allocator/lifecycleへscalar蓄積carrierと独立した名前archiveを接続する。回復poolのowner別検索やdown破棄をコピーしない。active最大512＋名前最大256と既存familyが1024 object枠で共存する容量設計を先に確定し、枠不足はfail closedとする。object kind/metadata配置は未確定である。

rateには値field存在bitを持たせ、無名基礎と名前加算をsoftware binary64で別順序のまま計算する。収集はdealt/receivedの2走査とし、全更新後にevent50の通知列を既存continuationから配送する。boss着弾/部位複製では吸血の後へ接続し、adds/aimed経路を混同しない。dischargeはactive順のfirst matchとglobal名前archive、splitのみの倍率・既存int変換を使う。CPUで計算したruntime蓄積量を入力へ渡さない。

既存compilerではstat81/82、kind34、target name operand、full event50が定義済みだが、private admissionと実際のconsumerは未接続。複数敵のrecipient fanoutでscalar poolを複製しない設計も必要である。接続後に52契約＋旧398をMetalで実証し、元ドロシー/トロニーの全定義・実編成とcallback混在/容量境界を追加する。CUDAは共通生成/テストを使い、有用な固定checkpointで必要な短い検証だけを行う。
