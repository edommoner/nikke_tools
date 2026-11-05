# 保存PTXの独立アセンブル

共通CLIの `assemble` は、成功済みPTX producerを再監査してから固定NVIDIA ptxasを1回だけ別プロセスで実行する診断です。Slang、NVRTC、CUDA driver、GPU計算は呼びません。既存compile cacheを変更せず、成功したELFと入力PTX・tool・options・producer receiptを束縛したassembly receiptを保存します。まだCUBIN cache/module loaderへの接続ではありません。

```powershell
& $py C:/proof/package/scripts/nikke_gpu.py assemble `
  --source-package C:/proof/v128/package --source-capture C:/proof/v128/cold `
  --ptxas C:/proof/component/nvidia/cuda_nvcc/bin/ptxas.exe `
  --capture C:/proof/offline --original-workspace C:/original/nikke_tools --timeout 60
```

パスは例示です。現物のsource package/captureを確認して指定します。producerのimmutable manifest、artifact、sealed golden、生成CUDA/Metal、PTX receipt、成功phase、元Jobの2GiB上限と終了、既存process欠落0を既存監査器で確認します。service識別unverifiedは環境保持falseのままです。

NVIDIA公開component12.4.131のwheel/EXE SHAはportable-offline-assembler-component.jsonと実装に固定。元PTX8.4/sm_86を改変せず、sm_86/O1/FMA無効/verboseを固定します。古い11.3 assembler・`.version`書換え・`-c`・他レベル・driverへのfallbackはありません。componentは隔離展開しlicenseを保持、既存SDK/PATH/driverへ変更しません。

既存のfresh Job/start gateを再利用し、harnessとptxasを合計2GiB・60秒に制限します。子waitは55秒、既存cleanupは5秒です。ptxasはbreakawayなし/BelowNormalで開始し、読み取り専用の既存Job観測器でOS親PID・作成時刻・直近Jobの正確な2PID所属を確認します。[MicrosoftのJob継承仕様](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects)と[NULL QueryInformationJobObject仕様](https://learn.microsoft.com/en-us/windows/win32/api/jobapi2/nf-jobapi2-queryinformationjobobject)に基づきます。観測失敗は成功へ繰り上げません。

`assembly-claimed-cuda.json`はcompile/module/GPU claimとは別で排他的です。失敗・partial・stdout/stderr・phase・Job・環境観測を保持し、再試行しません。audit/status/collect/exportを再利用。auditは正確な9phase順序、native argv、tool/input SHA、子所属・観測時刻、ELF SHA、外側Jobの上限・終了を再検査します。成功でもcalculation_verified=false/kernel_calls=0。exit1はassembly未確認、exit2はassembly確認済み・環境保持未確認です。ELF生成だけでdriver loadabilityや数学的一致を認定しません。

CPU故障注入14件はproducer監査、tool/PTX拒否、driverロード禁止、Job所属、timeout、partial保持、ELF拒否、argv/receipt改変、claim独立性を検査。Macの/varと/private/varという同一実体のパス差で成功auditが失敗したため、auditも実行時と同じresolveを使うよう修正しました。初回のfixture不備2件とその後のパス不具合1件はテストログへ残し、GPU結果を変更していません。Windows実機のassemblyは未実行です。

## Windows v129/v130結果

v129はCPU107件成功後、sandbox内のCIM snapshot取得失敗でgate前停止しました。Jobはpost空、assembly0。missing/serviceは観測不能で成功へ変えていません。追加CPU read-only診断でsandboxではGet-CimInstance/Get-NetTCPConnectionが失敗し、正規require_escalated経路ではprocess634/listeners74取得成功。診断SHA5e4f2efbf215f6b2578a9a700ccbc968692a4bae110a8bb258f2e37be02d79fbを根拠に、同source/packageのfresh v130へ環境条件を変更しました。v129失敗は保持しています。

v130はCPU107件、smoke Job/観測・post空・missing0まで成功。固定wheel/EXEの両SHAとlicenseを検査し、元v128 PTXを再監査して変更せず渡しました。harness116384とassembler88188のOS親/作成時刻/正確な2PID Job所属、合計2GiB上限を確認。ptxasは9.174秒で4294967295終了、Job14.272秒・peak2,147,573,760byte、timeoutなし。stderr0、ELF/partialなし、post空/missing0/cleanup・observationエラーなし。service未識別はpreservation=falseです。

非ゼロ終了と上限近傍の観測は確定ですが、stderrの診断がないため具体的な失敗原因は未確定。これをdriver常駐分だけの問題と断定しません。NVRTC/driver/module/kernel0、assembly1回、retry/fallback0。以降同条件で繰り返さず、GPU sourceのlowering/inline境界を既存codegenの証拠に基づいて検討します。CUBIN cache tier/module接続は成功artifactがないため未完了です。保存要約SHA63359a810a09e68efb249f0c68f2845cee93513a2d3c0e7e49bf6e5166690813。research/portable-world-v130-offline-assembly-sanitized.jsonはWindows最終報告からの派生記録で、Macが元captureを独立監査したものではありません。
