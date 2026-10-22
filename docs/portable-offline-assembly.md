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
