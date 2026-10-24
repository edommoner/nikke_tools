# CUDA準備の分離とコンパクトpacket

全キャラGPU認定は未達。ここでは計算本体を変更せず、Windowsの短いCUDA確認からSlang生成の準備を分離する。生成成功・コンパイル成功・GPU計算成功を混同しない。

## 実行経路

`attack-group-battle`32、`attack-group-native-route`53、`attack-group-long`60を既存 `package --compact` の許可済みsuiteへ追加した。依存投影アルゴリズムは変更しない。全GPU・全app・公開data・fixture・pinned referenceと選択CPU／全制御テストを保持する。同じsuiteのfull/compactで残るファイルの原byte指紋・goldenを全一致で検査した。初期60比較は2,840→1,559ファイル、ZIP9,278,144→7,155,905byte。最終は生成入口とテストを加えて1,561ファイル／7,159,876byte。Windowsの速度改善率は認定していない。

Windowsのv2実測はCPU32／60入力／native48成功、全stage111.939秒。内訳はpackage検証17.755秒、worker検証6.719秒、テスト21.408秒、正本比較65.091秒。別の過去の重いfull suiteとは条件が違うため速度比を出さない。

生成を既存 `scripts/run-gpu-packet.py` の `--stage generation` に接続した。必要な絶対cacheは `NIKKE_SLANG_GENERATION_CACHE` で指定する。CLIのWindows単独生成禁止を維持し、packet子だけ `--packet-stage` を介して入る。recipe/command/child/package identity・出力先・開始gateに加え、Windows APIで現在processの実Job所属、低優先度、Job全体2GiBとkill-on-closeを読み直す。既存Jobの作成・制限・終了・観測機構を再利用し、新しいJob管理器は作らない。NULL handleの現在Job照会は [Microsoft仕様](https://learn.microsoft.com/en-us/windows/win32/api/jobapi2/nf-jobapi2-queryinformationjobobject) に従う。

```powershell
# 新規固定packageをcwdとする。環境変数は実行する同じコマンド内で指定。
$env:NIKKE_SLANG_GENERATION_CACHE='C:/proof/NEW/generation-cache'
$env:NIKKE_SLANG_ROOT='C:/path/to/existing/slang'
& $basePython -B scripts/run-gpu-packet.py --stage generation --backend cuda `
  --capture C:/proof/NEW/generation --timeout 180 `
  --original-workspace 'C:/Users/owner/Documents/ChatGPT/nikke tools'
```

外側180秒／2GiB／BelowNormal／fresh Job・開始gateは維持する。NVRTCの内側60秒も変更しない。生成stageはNVRTC・driver load・GPUを禁止し、sourceとCUDA/MSLの厳密normalized hashをsealed goldenへ照合する。`generation_verified` は計算やコンパイラの証明ではない。準備成功後のcompileは別claim・別captureであり、cacheを必須にして検査する。

## 発見した問題と保存

- Windows v1は監査器の相対pathがバックスラッシュになり、承認producer一覧との一致検査で停止した。source identityを両OSでPOSIX表記へ統一。producer許可集合や拒否条件は変更しない。新テストはPureWindowsPath/PurePosixPath双方を確認する。
- v2 CPU32/native48成功後、生成stageがWindows単独禁止ガードに接続されていなかったため6.659秒で停止。Slang/NVRTC/GPUは0。上記の実Job確認を伴う限定入口で修正した。
- Mac v3制御は旧拒否メッセージ契約の不一致で停止。元記録を保持し、メッセージを既存契約へ合わせたv4を新規作成した。v4制御387件（Windows専用1skip）と生成stage成功。cache hit／Slang0、既存CUDA/MSLと一致した。

各失敗・claimは残し、同じ実行を繰り返さない。Windows v4生成専用stageは34.117秒で成功（Slang2回、生成10.719秒／検証16.086秒）。両normalized hashがMacと一致し、実Job 2GiB／flags0x2200／BelowNormalとpostJob空、missing0、観測・cleanupエラー0を確認した。サービス識別はunverified。NVRTC/driver/GPU0。

Windows v4は数値・入力・goldenがv2と同一であることを全ファイルrecord比較して、成功済みCPU/nativeを繰り返さず生成だけを依頼する。差分は6ファイル（入口、Job読取のflags追加、CLI、wrapper、2テスト）。Windows v1/v2の記録はtask最終応答由来と明記し、保存rawを独立取得した証拠に置き換えない。

## 範囲

CUDA／Metal共通Slang・software binary64・正本CPU・normalizer・GPU期待値は変更0。既存のMetal60成功を維持し、この変更でGPUを再実行しない。現CUDA本体の計算成功は未確認。サービス識別未確認ならenvironment preservationはfalseのまま。以前の7process終了原因もunknownを維持する。同じ生成cacheを必須にしたO0コンパイルを1回実施した。cache hitでSlang0、NVRTCは27.211秒でreturn code6／`ptxas fatal: Memory allocation failure`、artifactなし。内43.623秒／外58.300秒でtimeoutではない。内外とも2GiB設定・BelowNormal・gate・終了後空、missing0・観測cleanupエラー0。記録されたpeakは外2,148,503,552／内2,124,677,120byteで、どの制約が直接の割当失敗原因かは未確定。driver/GPU0、CPU再検査0、再試行0、上限変更0。次は保存生成コードと既存callgraph解析器を使い、コンパイル時メモリを削減する共通実行器の分割候補をCPUだけで調べる。

記録: `research/portable-cuda-packet-preparation-evidence/`。固定Windows v4配布は `codex/cuda-prep-v4-source` commit `2d07a5e7c1ce05b4b663fdea68ef490fa688eaea` のpackage/provenanceのみ。全体の静的245/266、base185/203、残20model gap、通常UI CPU、全キャラ認定0は変わらない。
