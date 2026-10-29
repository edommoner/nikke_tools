# 元profileを選択して共通実行器へ渡す

`original-catalogue` は元266profile × 発射体/HPシールド × 3/30秒の1,064名と、[元role条件4名](portable-original-catalogue-roles.md)・[実被弾4名](portable-original-catalogue-incoming.md)の計1,072名を列挙する開発入口。`cases` はmetadataだけを読み、全profileのprepare/compile/battleを実行しない。明示した1〜4件だけを準備し、元効果/owner順/実武器/育成/configを保持したまま既存の共通typed owner compilerへ渡す。明示操作を適用するrole caseは元identityの検査後に適用したことを別flagで示す。別の計算器やキャラ固有handlerは追加していない。

```sh
python scripts/nikke_gpu.py cases --suite original-catalogue --match 모더니아
python scripts/nikke_gpu.py package --suite original-catalogue --develop \
  --case 'original-catalogue/hp-shield/모더니아/favorite-0/3s' --out NEW.zip
```

未知名・重複・空選択・上限超過はprepare前に拒否する。失敗profileの消去やexpected rejectionへの変換はしない。選択順はcatalogue順へ正規化し、返された行とnative domain、全wire/packed bytesを照合する。未選択profileは準備しない。固定したcase群も同じadapter/selection protocolを使い、callerの`--case`で上書きできない。任意選択は開発専用であり、sealed suiteの基準を迂回しない。

## 完全なスキル履歴を共通実行器で保持（2026-10-28）

現行の `original-catalogue-initial` は同じ4入力をM5 Metalで全比較し、別fresh GPU禁止childの独立監査も成功したsealed群。`original-catalogue`の任意選択は引き続き開発専用。固定群は `package --suite original-catalogue-initial --out NEW.zip` → `unpack` → 固定packetの `run` で使う。goldenは独立sealの出力をそのまま登録した。

新entry `gpu/world_coordinate_typed_history_entry.slang` は既存owner entryに記録領域の宣言だけを追加する。共通`logWorldSkill`は同じ48word schema/時計/順序で書き、先頭128行を旧位置、以降1,920行を武器専用入口で未使用だったtyped skill receipt領域1,773,424..1,865,584wordへ保存する。全容量2,048行で、input115680/output2032000word、Runtime138952byteと全field reflectionは不変。新entryは既存weapon/aim/owner/current-fieldの明示flagを要求し、typed skill probeと領域を共有しない。旧entryは従来128行のままである。

比較は既存の厳密なskill行デコーダーを128行のpageごとに使い、元source binding・実HitEventのcreation identity・順序・hit/hits・2つの時刻・amount/share・全recipientとbitmapを全行照合する。全件数/最大対象数/予約header/未使用prefix/未使用continuationも検査する。その後に限り、コピーした表示を旧128行へ射影し、既存の全battle/typed/武器/乱数/通知/回復/最終状態の比較器へ渡す。元nativeの1,618行もreadbackも変更しない。短縮・trace抑制・未検査の後半切捨てはない。

固定d90c5f9a/package3edf0819…で136unit・fresh CPU全4（77.54秒）、M5実GPU1回（4.746秒）、fresh独立監査（89.35秒、GPU0）が成功。新sourceの初回PSO62.16秒、実行内Slang0・必須paired generation hit。事前のgeneration-onlyはCUDA/MSL+reflectionを2回のSlang呼出しで生成し、GPU0。履歴行数はAlice2/Modernia3秒32/Modernia30秒1618/Maid17。全4の入力とCPU指紋は前回と同一、前回成功3件の全24,384,000byteも完全一致し、前回Moderniaの失敗は保存した。別のGPU再実行やclaim再利用はない。

unitは0/127/128/129/1618/2048行、先頭/境界/最終行改ざん、件数/bitmap/予約語/未使用領域/creation欠落、2049超過を検査。実GPUで境界2048/2049をstressしたとは扱わない。新しいsource/transportの全byteを登録し、既存の厳密なinverse chainへ接続。normalizerやCPU正本、効果定義、ダメージ/着弾/時計処理は変更していない。

`original-catalogue-initial-cache-only` は同じ4入力・source・golden・比較器に既存のCUBIN/O1必須、compile cache必須とpaired generation必須を適用する。Windowsへ送る前にその固定packetの`compile-plan`を使う。新sourceは旧128件kernelと異なるため、旧sourceのCUBINを流用せずexact keyを要求する。現CUDA実機/実CUBIN hitは未確認、Windows新依頼0。既存Windows transactionは接続断で終端不明のままなので再送しない。

証跡 `research/target-count-query-evidence/metal-original-catalogue-history-v1.json`。これは宣言したBODY-owned typed worldでの元3profile/4入力の限定認定。全キャラ・全条件・任意mixed world・2,048超過・他の履歴bank・公開GPU受付は残る。次は同じ選択CLIで未実証の元profileへ展開し、model gap12件とruntime容量/対象経路の未対応を区別して進める。

## 初回128件版の失敗記録

`original-catalogue-initial` はAlice projectile30秒、Modernia shield3/30秒、Privaty Unkind Maid shield30秒の固定群。この初版は開発専用で、sealしなかった。元266profileの全recordは前回inventoryと完全一致し、静的変換254/失敗12/分類13も不変。静的受理数はGPU対応数ではない。

固定94eb6df1/package3591b6f8…で129unitと全4nativeのCPU gateが成功（77.39秒）。M5 Metalは1回実行し、3件は全比較一致したがModernia30秒はstatus8で停止したため、全体の計算成功/独立認定はFalse。失敗readback/claimは保持し、同claimの再実行はしない。GPU2.370秒、必須pipeline hit0.00297秒、paired generation hit/Slang0。生成CUDA/MSLは旧shield suiteと原byteも同一。CUDAの新実機検証/実CUBIN hitは未確認、Windows新依頼0。

Moderniaの元weapon_changeは通常攻撃扱いのMGであり、`weapon_mode_skill=True`を必須にした最初のwitnessは誤りだった。CPU正本の実射撃は4.0167秒に係数7.71→2.24、19.0167秒に7.71へ復帰する。元定義のskill levelから係数/分類を導き、変更前・変更中・復帰後を全て要求する検査へ修正した。CPU正本や武器/効果の値は変更していない。

実際の未対応は共通`logWorldSkill`の128×48word履歴bank。GPUは129件目で停止し、同じ30秒nativeは1,618件を生成する。新しいcatalogue native検査はこの実件数超過をpackage/runのCPU gateで拒否するため、同じ容量不足でGPUを消費しない。0/127/128受理、129/2048拒否・入力履歴不変を含む15unit成功。共通CLIの既存controller49検査も成功。これは容量対応そのものではなく、未対応を実行前に検出する変更である。

当時は**全1,618件の履歴を保持・照合できる共通bank/記録器/decoder**への拡張を次の優先課題とした。現在は上節のとおり独立sealまで完了した。秒数短縮、traceMode抑制、先頭128件だけの照合では解消しない。既存のphysical全件SHA/保持prefix方式を再利用できるか検討し、全rowのsemantic schemaと順序を明示する。旧出力・reserved領域とstrict source ledgerを保持し、新sourceは別packageでMetalを実証してからsealする。現在のguardを成功扱いへ変換しない。

証跡は `research/target-count-query-evidence/original-catalogue-development-v1.json`。BODY所有1typed対象の宣言worldであり、実ゲーム距離規則、任意mixed world、全条件/全キャラ/公開GPU受付の認定ではない。

最終d85b55a7/package8a2bb6d4…は16群165unitとCUBIN/O1/2GiB/60秒のcompile-plan policyが成功（compiler/GPU0）。sealed packetからのpayload差分はCLIのsuite登録・追加の登録一致test・独立goldenの3ファイルだけで、全CLI関数AST、既存test、全GPU/host計算/compiler/native/比較器は同一。従ってnative/GPUの全再実行は重ねない。Metal archiveのfile-only probeもhit snapshotだが、実warm launchや現device contextの再検証とは区別する。全体model-checkは資料の揃うcheckoutで成功。詳細 `target-count-query-evidence/original-catalogue-history-final-checks-v1.json`。
# 2026-10-30 ナガ・ティアの元30秒編成と順序readback不足

共通CLIの開発専用 `original-catalogue-support` に、ナガ70定義・ティア75定義の元編成を固定した。元効果・owner・武器・設定を保持し、既存catalogue・全履歴比較器・同じCUDA/Metal計算本体を使う。本人の射撃、full burst、元partyのcast順を要求し、ティアの再突入は共通実行器のevent7として検査する。

packet `dcd89cbb…` の26群225テストとfresh CPU2戦闘が成功。Apple M5の実Metal1回は2.512415秒、冷pipeline生成62.072932秒、CPU事前照合39.367821秒。ティアは全比較一致したが、ナガは名前付きバフの受け手順がnative `[2,0]` / decoder `[0,2]` となり、全体不成功。独立seal/goldenへの昇格はしていない。全16,256,000byteのrawとclaimを保持し、再実行0。

保存rawと変更のない事前nativeによる診断では、54個のallied carrierの49番目だけがこの順序差を持つ。入力のrecipient headerは `[0,0,0]`、metadataのordered_recipientsはFalseで、旧decoderはbitmaskをスロット順に展開する。共通実行器は内部に順序を持つが、この入力ではその全順序readbackが出ていない。GPU内部の実順序を観測したとは扱わず、受け手をsortして照合を緩めない。次は選択やイベント計算を変更せず、既存の内部順序を明示した観測契約へ出す。既存revival用flagの偽装は、そのflagの厳密な受付条件を壊すため使わない。

この検証で見つかった旧監査テスト2件は、後続の厳密な逆変換を先に通すことと、旧ファイルごとの完全hash検査へ修正した。全依存mapを旧層だけとみなさない。共通CPU依存一覧にもIMPL-STATUS.mdを登録し、梱包漏れをnative前に拒否する負例を追加した。初版から3版のCPUゲート失敗と未実行の4版も保存した。

BODY-owned shieldの宣言worldの検証であり、負傷回復・遮蔽物被弾等の全条件、ゲームの距離規則、全キャラ、現在CUDA、公開GPU受付は認定していない。Windowsは既存結果のstatus取得1回だけを試みたがhost unavailable、追加実行依頼0。証跡 `target-count-query-evidence/original-catalogue-support-development-v1.json`。

## 2026-10-30 受け手順序の観測を共有実行器へ接続して解消

`original-catalogue-support` のナガ70/ティア75定義・各30秒がApple M5の実Metal1回と、GPU禁止のfresh独立sealで一致した。GPU2.509480秒、冷pipeline61.967791秒、CPU事前照合39.462326秒、独立監査46.945674秒/native2/parent再利用0。ナガの実順序は `[2,0]` だった。旧失敗rawとの比較では既存のrecipient-order bank（155648..156672word）以外の全バイトが同一、全16,256,000byteと元input/native期待も保持した。比較時にsortや順序の省略はしない。

新entryは元の `executeComposedCoordinateEvents(runtimeStates[id.x],id)` を実行し、完了後に既存 `carrierOrder` を既存bankへ書くだけ。選択・計算・効果・時計・Runtime138,952byte・容量を複製/変更しない。共有area entryの変更は標準kernelを明示的に抑止する条件1行。旧272 sourceへ戻す完全hash付きinverseを持ち、旧入口のCUDA/MSL生成も既存strict normalizerで完全一致した。ただし旧goldenのcurrent-source認定をsource-onlyの一致で昇格せず、必要な再認定は別に管理する。

初版packet51f29fc5…はkernelの二重定義でSlang生成中に停止、GPU未実行。claimと診断を保持し、修正版96816a01/packetf72077a9…で1回だけ実GPUを実行した。同claim retry0。source inverseは登録部とentry条件の前後hashを固定し、台帳/hash/hunkを同時改変して未レビュー変更を隠す負例も拒否する。normalizerと保護CPU4ファイルは変更0。

通常suiteは独立golden/source certificateへ登録済み。`original-catalogue-support-cache-only` は同じ計算・2入力・goldenでCUBIN/O1/compile cache必須hitとpaired generation必須hitを要求する。実CUDA/CUBIN hitの認定は未完了。Windowsは既存status取得がhost unavailable、追加実行依頼0。

最終41a4be5b/packet552bdb97…のcache-only固定パッケージは、29群260テストとfresh CPU2戦闘（40.991065秒）に成功、GPU追加0。CUBIN/O1/2GiB/60秒のcompile-planも成功したが、compiler/driver/Job/環境保持の実証ではない。共通準備helperへの抽出後も、実GPU認定と同じinput/native/source/goldenを保持している。

今後の元profileは `original-catalogue-ordered` で1〜4ケースを明示選択できる。既存catalogue/比較器/native referenceと同じ順序観測helperを再利用し、キャラごとのGPU entryを追加しない。この選択経路はdevelopment-onlyで、静的packingやCPU基準の生成をGPU対応数へ数えない。例の実CLI梱包は元ナガ3秒/native1を3.020471秒で準備し、GPU実行0。

```sh
python scripts/nikke_gpu.py package --suite original-catalogue-ordered --develop \
  --case 'original-catalogue/hp-shield/나가/favorite-0/3s' --out UNIQUE.zip
```

次は元編成の負傷・遮蔽物被弾・シールド/回復条件など、今回のworldで正例を観測できなかった分岐へ同じ経路を使う。実ゲームの距離規則、全条件、全キャラ、public GPUは未認定。証跡 `target-count-query-evidence/original-catalogue-support-metal-v1.json`。
