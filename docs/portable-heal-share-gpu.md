追加のナユタ・レム実編成4件も検証済みです。定義欠落0、レム30秒の物理履歴55件省略は残るため、[実編成の範囲](portable-heal-share-real-rosters.md)を参照してください。以下は共通接続の基準849の記録です。

# 回復分配を共有実行器へ接続

現在のsealed suiteは`heal-share-regression`849入力（native676／拒否173）、goldenは`portable-world-heal-share-regression-short-expected.json`。回復分配の43 CPU契約とraw負例10件を既存796へ追加し、Metalで全件一致、独立GPU0 sealを確認した。CUDA／Metalは同じSlang、effect定義、入力、比較器を使う。本体CUDAのcompile／数値一致は未成立。

## 共通処理

canonical stat75を64項目のnumeric vectorから分け、private combat worldのbuffとして受付する。unscaledの契約を対象とし、不正kind・非finite値・enemy／health／quantity／damage属性の偽装等はraw admissionで拒否する。まだ検証していないscalingを黙って受け付けない。

`heal_share_runtime.slang`はactivation順のdistinct carrierを走査し、期限・lazy resolve・対象・runtime条件の順で5人のmembershipを採取する。damage向けのquery除外やcacheを転用せず、通常のbuff辞書queryではstat75を消費しない。重複carrierは別の重み、同一carrierのstack数と値は重みにしない。

planは既存Frameのvalueへ50bitの重み、healthValueへ元amount、repeatLeft／repeatPassiveへtotal／member数を保持する。Frame／Runtimeの配列を追加せず、mode31でportionを順に届ける。各body/storage healとHP同期の全子イベントが終わってから次へ進むため、入れ子回復やnamed removalが外側planを再計算しない。完了後、元recipientへ元heal_sourceの通知を一度だけ送る。

通常healとlifestealが同じdeliveryへ入り、元recipientの倍率は分配前に一度だけ計算する。正amountだけでplanを採取する。lifesteal rate<=0は通知せず、正rateで回復倍率0ならbody heal0と元通知を行う。単独memberはamountを直接渡し、多人数だけ`(amount * weight) / total`を共通binary64で実行する。stat75がない通常入口は従来fast pathを保持し、不要なFrame／work数の変化を避ける。

## 検証

- 最初のnormal43入力は一致した。その後、selective queryのguardとraw負例を追加した最終候補を採用し、元captureは保持した。
- `heal-share-diagnostic`53入力は全戦闘状態と既存skill traceに加え、plan・portion・shared call/return・lifesteal packet・元heal_receivedの順序を照合する。最大70記録／512上限でoverflow0、raw拒否10件のtrace0、独立GPU0 seal成功。optional CPU profilerのHP通知列自体はこの追加traceへ投影しない。旧ケースで未観測のheal_sourceだけを両側unknownへ投影し、観測済みsourceは厳密比較する。これらの範囲を隠さず、既存の全戦闘・skill trace比較は削らない。
- 集約849は全件一致。旧796の全input／native／output指紋と全2,503,999,488byteを直接比較して完全一致し、lazy bankゼロも保持した。GPU0 retainerと独立sealを再利用した。
- 共有GPU向けCPU893件中892成功・Windows専用1skip。選択batchは302件／44.664秒。最終compiler-only packetのsmoke158件は157成功・Windows1skip、更新したcertificateの9検査も成功。compiler／cache／Job／監査の別runnerは増やしていない。

実GPU実行は異なる候補／入力の3回（最初の43、診断53、集約849）。失敗の再実行や保存結果再生成ではない。storage-checkで6.5GB＋1GiB reserveを確認してから集約を実行した。Runtime247 fields／stride138,952／align8は維持。集約GPU10.326秒は単一観測で、性能改善の測定ではない。

Definitionの55 getter／型／wire loader／accessorは固定基準のまま。周辺のsource guardは、今回の意図したfeature変更を新baselineへ記録し、全43／診断53と旧796の保持を確認して更新した。数値本体・整数変換・pow・canonical CPU・厳密normalizerは変更していない。

## 使用と残件

`python scripts/nikke_gpu.py package --suite heal-share-regression --out <new.zip>`で通常の固定packetを作成し、fresh展開後は既存run／audit／seal／archiveを使う。診断だけなら`--suite heal-share-diagnostic`。未sealのnormal standalone `heal-share-world`は開発用途のまま。期待値を自動追従させない。

静的packingは216/266（base156）へ増え、ナユタ／レムが新たに入力受付できた。これは実編成の戦闘認定ではない。次はこの2人の全定義を使った3秒／30秒の実編成を検証し、履歴省略・capacity制限・未対応項目を確認する。今回の43契約は宣言済みCPUモデルの保持で、実ゲームの全相互作用の確認ではない。

Windows追加実行0、通常UI CPU、全キャラGPU認定0、最終目標未完了。本体CUDAのcompiler failureとcacheの成功artifact不足は残る。保存PTX共有の個別許可待ちであり、同条件compile・上限拡大・RDC等への自動fallbackは行わない。source certificateをMetal849へ結び直したことからCUDA成功を主張しない。

構造化記録は`research/portable-heal-share-gpu-checkpoint.json`。rawと全失敗／claimはローカルに保持し、GitHubへ含めない。
