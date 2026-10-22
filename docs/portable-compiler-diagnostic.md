# コマンドフェーズのコンパイル専用パッケージ

現在の根拠は`research/portable-compiler-diagnostic-checkpoint.json`。v132のfull本体Memory allocation failureを切り分けるため、同じ共有本文のcommands側だけをコンパイルする。通常の戦闘suiteやMetal数値goldenを診断結果へ置き換えない。

## 共通CLIとキャッシュ・監査の再利用

`package --suite compiler-commands --out <new.zip>`で新しい目的`compiler-diagnostic`の固定パッケージを作る。source certificateは元full Metal796の共有source SHAを全て保持し、新しい入口1ファイルだけを追加する。元golden自身もsupport fileとして束縛する。certificateの`proof_kind=compiler-source-only`、戦闘認定false、entries空を検査し、目的の偽装を拒否する。Slang生成指紋は既存strict normalizerのまま、除外を増やさない。

入口は既存executePortableCommandsだけを呼び、Runtimeを外部stateとして扱う。初期化／受付／最終出力は呼ばない。layoutは従来と同じ247field／stride138,952／align8／48byte constant blockを両target reflectionで確認し、CUDAのsizeof/alignof assertも共通builderで追加する。これは実module/ABIや数値の成功ではない。

`run`はsmokeだけ許可し、通常戦闘／CPU-only戦闘adapter／module loadは起動前に拒否する。`compile`は明示PTX・levelなし・2GiB・最大60秒だけ受け付ける。childと保存監査も予算・artifactを再検査する。既存NVRTC compiler cache、DLL制限、phase journal、compiler監査、cache-check、standalone assembly、Job observer、結果収集を再利用し、独自の検証runnerを増やしていない。

```sh
python scripts/nikke_gpu.py package --suite compiler-commands --out /tmp/compiler-commands.zip
# Windowsではfresh展開後、CPU smoke成功・終了観測正常を先に確認
python scripts/nikke_gpu.py compile --artifact-kind ptx --memory-limit-mb 2048 \
  --timeout 60 --capture <fresh-cold> --original-workspace <original> \
  --slang-root <existing-slang> --compile-cache <dedicated-cache>
python scripts/nikke_gpu.py cache-check --capture <cold> --out <new-cache-report.json>
```

実際のWindows運用では既存のbase-Python／venv依存設定・CIM観測可能な実行経路を使う。親の環境は復元し、既存checkout・SDK・PATH・driverを変更しない。PTX・containment・cache hitが確認できた場合だけ、固定12.4.131 ptxas/sm86/O1/FMA無効で独立assemblyを最大60秒／2GiBの1回行う。普通の`assemble`に同じpackageとcold captureを渡す。driver・kernel・同条件再試行・上限拡大・RDC等の自動fallbackは行わない。

## Macでの事前確認

fresh package aaec8ca7で全CPU861件中860成功、Windows専用1skip、smoke153件成功。新規9テストは目的／battle claim偽装、source drift、子・親・保存監査の予算変更、通常起動・module拒否、実cache receiptのfile-only hitと破損拒否を確認した。nativeDLLはCPU doubleで、実NVRTC／GPUではない。

fresh共有builderでもCUDA／Metal生成指紋がcertificateと一致し、247field／stride138,952／48byteを再確認。約1.926秒、CUDA1,202,619byte、Metal1,281,869byte。新入口を除く元shared sourceはbyte不変。通常本体の数値・イベント・canonical CPU・normalizerは変えていない。MacのGPU実行0。

Windows検証はcommandsのコンパイル局所化の成否だけを判定する。成功してもfull796 CUDAや複数kernel戦闘の完成ではない。失敗ならinit/writeを追加実行せず、同条件を繰り返さずに次の構造仮説を選ぶ。service未識別はpreservation=falseのまま。全キャラGPU認定0、UI CPU、回復分配GPU未接続を維持する。

v133はsmoke153件中152成功・fixtureのpath表記1エラーで停止した。`str(relative_path)`がWindowsのバックスラッシュをartifact member名へ渡し、既存safe_nameが正しく拒否した。2箇所をas_posixへ訂正。共有runtime・compiler・normalizerは不変で、元失敗はresearch/portable-world-v133-compiler-diagnostic-sanitized.jsonへ保存した。validation Job／NVRTC／assembly／GPUは未開始なので、コンパイル局所化の判定はまだ出来ない。訂正版は新しい固定sourceでsmokeから確認し、元capture・claimを置換しない。
