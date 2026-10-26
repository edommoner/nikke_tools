# 型付き所有者の寿命・世代と共有GPU検証

`coordinate-typed-owner-lifecycle` はsealed 88入力（native53／拒否35）です。既存の `coordinate-typed-owner`80をすべて保持し、同じ `gpu/world_coordinate_typed_owner_entry.slang` に8件の入力を追加しました。CUDA／Metalは同じSlang・入力・比較器を使います。今回Slangとhost transportの変更はありません。

追加ケースはprojectileのBODY所有field、生存／破壊済み同世代のHP shield・projectile、再登場した第2世代のcounter、古い世代に後からarmされたcounterの抑止、手動projectile対象です。元Primの完全5人・71定義・武器・成長を保持します。counter監査には別宣言した2効果を原本の後へ追加し、実射撃→counter完了→子fieldのBODY所有、物理kind/id/generation、damage、delivery、broken、所有者query時の生死を検査します。

世代ケースは元patternを0.5秒で終了し4回出現させます。staleケースはgeneration1向けmarkerを `every:1.25s` で実際にarmし、その後の世代への命中で完了しないことを検査します。これは古いcounterの抑止の証明です。不正な内部contextをGPUへ渡してerror64を直接確認した証明にはしていません。

## 実行と比較修正

CPU専用8契約は71.665748秒、観測wrapperの透明性を含むunit3件は20.469秒で成功しました。wrapperは既存owner query直前の生死を受動記録し、追加queryを呼びません。

実行版 `/tmp/nikke-owner-lifecycle-gpu-develop-v1` のIDは `dcd09db2434b77873a93c0f8d1109f5cbea990f9d1d49cd330d86ef8a573be67`。capture `/tmp/nikke-owner-lifecycle-metal-v1` でApple M5を1回実行しました。全88事前native照合297.821087秒、GPU4.110688秒、bounded実行7.182688秒。generation必須hit・Slang0、Metal pipeline必須hit・archive compile0、library0.005774秒／pipeline0.002903秒でした。前回と同じ入口へのdata-only追加で既存cacheを再利用できた実測です。

初比較は86/88一致でした。stale2件で、GPU decoderが残っているcounter markerを通常のenemy field／recipientとして列挙していました。実fieldの値、counter資源、epoch、世代抑止と他の戦闘値は既に一致していました。共通decoder2箇所を既存CPU `enemy_buff_plan` の分類に合わせ、counterを通常fieldから除外しました。counter資源は別の比較で引き続き全検査します。synthetic rawによる負例は実fieldの保持・counter資源不変・raw不変も検査します。GPU本体やnative計算、normalizerの変更はありません。

既存のstrict repackageに `coordinate-owner-counter-field-decoder-v1` を追加しました。元package ID、変更可能なfileとSHA、decoder関数だけのAST差分、全prepared inputと全native指紋を固定します。これはcalculation成功を認定せず、fresh全件比較を要求します。固定v3自身のCLI／fixtureを使う契約で、後のmetadata更新を無条件に許可しません。

## 全件独立監査と最終成果物

修正版 `/tmp/nikke-owner-lifecycle-replay-v3`（ID `8d9c2cf1497d3f7e846a0d86c0239de7d62880c64155434f4ec3e91659ed62e9`）から保存rawを再利用し、共通CLIのgrouped replayで全88/native53をfresh監査しました。GPU禁止の別child4つ、live parent oracleなし、各180秒上限。24/24/24/16件を79.901408／75.157454／137.231821／90.120142秒、合計384.476683秒で成功しました。同じ独立監査結果からgoldenを登録し、sealコマンドの二重実行はありません。追加GPU0、retry0です。

旧80のinput/nativeを保持し、旧readback650,240,000byteも完全一致。全88のraw715,264,000byteはSHA `c547151a3740c7d16be64e82320f69d06044caec709e303dc0ecaaac9c731201`。全reader終了後、size/SHA/inodeを保持した疎化で573,636,608byteを回収しました。raw、失敗capture、claimは削除していません。replayはhash再検査付きhardlink共有です。

最終 `/tmp/nikke-owner-lifecycle-final-v1` のIDは `1f1c15b66cf262747e47a9d625e325ffc320b13eb9b9d781b0e6185f8786b43b`。sealed登録・golden・readinessと非Mac向けfilesystem単体テストの4file差分だけです。全CLI関数AST、native producer／比較器、GPU source、全88goldenを保持。最終関連18group106検査と制御53group517検査成功（Windows専用1skip）、generation必須hit・Slang0。最終版で新しいnative preflightを実行したとは主張しません。証跡は `research/typed-owner-lifecycle-evidence/` と `research/portable-coordinate-typed-owner-lifecycle-checkpoint.json` にあります。

## 残る範囲

BODY所有の明示private policyの証明です。ADD所有、GPU内部stale context拒否の直接実証、ゲーム仕様、canonical公開consumer、移動形状・他caller／variant、残るpacking失敗とモデル、旧suiteの現source集約、現CUDAのcompile/cache/launch、全キャラ認定は未完です。全キャラ認定0、UIはCPUです。Windowsへの新しい検証依頼は本milestoneでは0。接続後の送信API再試行もidle turn不足で失敗し、CUDAは開始していません。

次は所有者規則を満たさない対象の分類・契約を先に固定し、最優先の未対応owner／対象操作を同じ共通実行器へ接続します。実行可能な新しいCUDA確認は短いケースだけを使い、Metal証明をCUDA成功へ流用しません。
