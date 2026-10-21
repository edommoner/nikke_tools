# 共通実行器の段階分割

Windows v123ではpushFrameのnoinline境界だけでCUBINを生成できず、2GiB上限付近でptxas Memory allocation failureになりました。次の候補では計算・効果・入力を減らさず、既存の実行本体をCUDA／Metal共通の8関数へ抽出します。CPUへ時刻、状態、対象選択を移していません。

| 関数 | 役割 |
| --- | --- |
| initializePortableProgram | 既存のGPU受付検査と初期化 |
| executePortableCommands | 入力コマンドの順序付き実行 |
| writePortableQuery | コマンド中の観測出力 |
| writePortableProgram | 最終状態と全serializer |
| advanceSkillDamageFrame | スキル命中のDFS段階 |
| advanceIncomingFrame | 被ダメージとその通知のDFS段階 |
| advanceDefinitionFrame | 候補走査・予算・対象・タイマー登録 |
| applyDefinitionFrame | 効果本体と従来のHP flush |

dispatchはFrameのsnapshot、HP edge drain、work／depth上限、context保存・復帰を持ち続けます。各helperは同じRuntimeとFrame配列を参照します。単一実行のdo/while(false)で、元の外側continueを次のDFS stepへ、エラー時breakを既存の終了判定へ戻し、内側ループのbreak／continueはそのままです。受付helperはready=falseから始まり、以前returnしていた経路ではコマンドとserializerを呼びません。queryの個数はinoutで引き継ぎます。Runtimeのfield・容量・strideは変更していません。

移動した処理を再構成して旧ソースと比較し、スキル命中・被ダメージ・効果解決／適用・受付・query・コマンドloop・serializerのtoken列が一致しました。この静的証拠だけを実行同等性とは扱いません。記録はportable-phase-transplant-verification.jsonです。

## 保存結果による確認

固定development package6c90d0bdの759入力（native602／拒否157）は、GPU前に入力／native指紋を保持しました。登録CPU175検査、Metal実機1回、親比較、GPU0の独立sealが成功しました。旧pushFrame候補の全入力／全native／raw全word／lazy bankゼロを比較し、全2,387,607,552byteとSHA e9284ab0b1afb99a3d9969ec8ee2ff43d8e333608a59240ab446c323d1bc0481が一致しました。

通常入口・GPU常駐入口の両方でCUDA／Metalを生成でき、共通の関数境界を使います。生成CUDAのdispatchは163,801byteから36,086byte、最大関数は73,200byteになりました。定義数は638から646、noinlineは206から214です。これは字句上の変化で、compiler memoryや速度の改善を意味しません。portable-phases-compiler-delta.jsonを参照してください。厳密normalizer・software binary64・整数変換・pow・比較器は変更していません。

## CLIの固定パッケージ検査

新しいincludeが未追跡でpayloadから漏れる問題を、GPU前に発見しました。packageはGPU source closureが追跡対象に揃っていることをnative baseline作成前に検査し、verify_packageもgoldenのsourceとmanifestの所属・SHA一致を要求します。native baselineの作成中に別のファイルが変わった場合も、archive公開前に停止します。CPU故障注入を含むCLI39検査で確認しました。

portable系の全CPU検査をfreshな展開先で実行できるよう、追跡済みのtests/fixtures JSON、既存app CUDAソース、mode-session契約とその固定仕様文書、41入力の履歴goldenを同梱します。契約の参照先はpinned upstream内に限定し、記録SHAと照合します。個人設定、raw buffer、compiler配布物、一般の巨大レポートは含めません。公開テストデータを加えてもZIPは約5.2MBです。characterize-world-overlaysは診断出力先を自分で作成し、前の作業フォルダーの存在に依存しません。

初回に全testsを指定した実行はCUDA専用の既存検査まで含み、次のportable実行ではデータ／scratchの不足を検出しました。失敗ログとSHAは保持し、成功証拠へ数えません。CPU全検査の範囲は以下を明示します。

```sh
python -m unittest discover -s tests -p 'test_portable*.py' -v
```

最終のfresh固定パッケージでは762検査中761成功・Windows専用1skip・失敗0、54.170秒でした。構造化した結果と失敗履歴はportable-phases-development-checkpoint.jsonへ集約します。新goldenはportable-world-phases-resident-regression-short-expected.jsonです。以前のgoldenは履歴として保持し、通常UIはCPU、全キャラGPU認定0、entry_reloadはCPU契約35件まで、最終目標は未完了です。

## Windowsの検証境界

固定packageでCPU事前検査と生成指紋照合を行い、必要なCUBIN O1 compiler-onlyを60秒／2GiB・fresh BelowNormal Jobで1回だけ実行します。成功時だけ必須cacheのCPU読取を確認します。driver／context／kernelは禁止し、同条件retry・上限拡大・fallbackはしません。CUBIN成立とCUDA計算一致は別の判定です。

v124は固定1c4908e／package7026b44d、全1,935ファイルとgolden一致・CPU73検査成功後に1回実行しました。NVRTC28.921秒、全体40.056秒でptxas Memory allocation failureへ終了し、CUBIN0・cache-check未実行・driver／context／kernel0。Job peak2,148,511,744byte、post空、既存process欠落0、サービスは未識別です。構造分割によるcompiler資源改善を実証できていません。原失敗と構造化Windows報告portable-world-v124-compiler-sanitized.jsonを保持し、Macで原artifactを独立監査した記録とは区別します。

v124後は同じコードのPTX-only（compute_86、ptxas optionなし）を、別の固定診断条件として1回だけ測りました。[NVIDIA NVRTC12.4.1の仕様](https://docs.nvidia.com/cuda/archive/12.4.1/nvrtc/index.html)ではvirtual architectureにCUBIN出力はありません。PTX生成と組立てを分けることで、前者が既定上限内で成立するかを確認する仮説です。v124のcapture／cache／claimは変更せず、同じsourceのCPU73検査は指紋を確認して再利用しました。成功してもCUBIN生成・driver JIT・CUDA計算一致の認定にはしません。メモリ上限と時間枠は維持します。

## v125のPTX生成とcache確認

同じ固定コードでCPU73検査の保存ログとソース指紋を確認して再利用し、テストを再実行せずPTX-onlyを1回行いました。NVRTC20.047秒、全体31.264秒、Job peak501,993,472byteで成功し、8,754,074byteのPTXを得ました。driver／context／kernel0、post空、既存process欠落0です。サービスは未識別なので環境保持を成功とはせず、CLI終了コード2とcompiler_verified=trueを区別します。

続くcache-checkは保存PTXとサイズ・SHAが一致し、cache hit、NVRTC compile0・GPU0でした。cache keyはb59ad6c3873b40f774fa9ab2357f86771979d6bc8847f8481e09b7ded0a36f1bです。PTX／cache本体はWindowsに保持し、構造化報告portable-world-v125-ptx-sanitized.jsonだけを共有します。Macで原artifactを独立監査したものとは区別します。

保存PTXの共通解析は215関数を観測しました。entryはlocal宣言0byte・virtual register19、dispatchはlocal宣言8,976byte・virtual register4,832です。weaponFrameBodyは38,938行・virtual register23,336という観測もあります。これらは仮想宣言であり、実register、実stack消費、ptxas失敗原因の証明ではありません。PTX解析の上位50件にentryが入らず、同じ宣言パーサでentryだけ追加参照したことも報告へ残しています。再コンパイルはしていません。

CUBINの単一Job生成は未成立ですが、PTX生成と専用cacheの読み取りは既定上限内で実証できました。次はこのPTXを必須cacheから使い、戦闘buffer確保やkernel実行に進む前に、driverのmodule load／JITだけを短いJobで確認する経路を整えます。PTX成功からCUDA計算一致を主張せず、NVRTCの再コンパイルも行いません。
