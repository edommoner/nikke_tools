# 最新Metal証拠からfull compiler packageを作る

共通CLI `compiler-certificate` を追加した。登録済みのfull-worldスイートの保存Metal結果を独立監査し、現在の共有ソース・登録goldenと一致した場合だけsource-only証明書を作る。以後は対応する `compiler-full--<suite>` を既存package/compile/cache/object/link経路で扱える。特定の古いheal-share証明書を手作業で更新する必要をなくすための経路である。

## 操作

```sh
python scripts/nikke_gpu.py compiler-certificate \
  --suite max-ammo-scaling-retention \
  --package-root /tmp/nikke-max-ammo-gpu-v2 \
  --capture /tmp/nikke-max-ammo-metal349-v2 \
  --out /tmp/new-compiler-certificate --timeout 120
```

実行CLIは現在のcheckoutまたは同じコードを固定したpackageを使う。監査対象のpackage/captureは書き換えない。出力は新しい専用directoryで、既存directoryを上書きしない。成功後、source-certificate.jsonをreportのcertificate_targetへ配置しGit追跡へ含める。今回は `research/portable-compiler-full--max-ammo-scaling-retention-source-certificate.json` を登録した。

```sh
python scripts/nikke_gpu.py package \
  --suite compiler-full--max-ammo-scaling-retention --out /tmp/current-full.zip
python scripts/nikke_gpu.py unpack --archive /tmp/current-full.zip --dest /tmp/current-full
```

compiler suiteは入力0、battle adapterなし、purpose=compiler-diagnostic。通常battleのdevelopment/case選択、通常runを受け付けない。CPU controllerだけならfresh展開先をcwdとして `run --backend cuda --cpu-only --smoke --capture <fresh>` を使う。WindowsでのPTX/object/linkは既存の専用claim・BelowNormal・Job・2GiB/60秒経路で明示的に行う。source証明書の発行がそれらを自動実行することはない。

## 何を監査するか

元packageのfile table・source/goldenとcaptureのpackage ID/backendを確認する。別suite、選択subset、CUDA capture、古いsourceは正本再計算前に拒否する。保存package自身のimports/native adapterをfresh childで使い、既存の独立comparisonを1回だけ実行する。保存の成功boolや与えられたseal JSONだけでは発行しない。sealed/developmentのMetal両方を扱い、従来のseal commandはdevelopment限定を維持する。

監査結果の全input/output/native entries、source closure、両生成指紋が登録済みMetal goldenと完全一致することを要求する。発行前に現在のsource/goldenと元package/manifest/artifacts/runのanchorを再確認し、変更を検出したらfailureを残してcertificateを発行しない。出力のmetal-golden.jsonとreportは監査の記録として保持する。

certificateはproof_kind=compiler-source-only、entries空、input_sha256=null、calculation_verified/executable_battle_verified=false。CUDA compileやcache hit、計算、資源改善の証拠には数えない。元のMetal計算証拠と明確に分ける。

## 共通cache/providerとの接続

compiler-full--suiteのsourceは登録されたbattle suiteから選び、証明書の可変文字列だけではfull/commandsを切り替えない。旧compiler-full/commandsの定義と履歴file解決は維持する。generic familyでも証明書とbaselineの全source/両生成指紋/元golden全byteのSHAが必要である。

保存CUBIN providerはgeneric full familyも扱うが、元compiler→object→linkの全監査、raw CUDA/prelude、toolchain、artifact hashとclaim/Jobを既存の共通経路で照合する。NVRTC hitへの偽装や自動fallbackはない。新旧のsourceが異なればCUBINは再利用できない。cache key・normalizer・計算本体・ABIは変えていない。

独立Metal監査済みのmax-ammo-scaling(28)、retention(349)、rosters(2)はdefaultのsealed packageを作成可能にした。これで短い実編成CUDA検証用の通常package経路へ進める。UI CPU・全キャラ認定0・private effect受付という範囲は維持する。

## 実測と検査

現行139 sourceのMetal349を新CLIで独立再監査し証明書を発行。compiler package ca71d9c09535c9eeb36891da02d65c23436cc19f21b2b2820cbb213235a20cf3(2556files/zip6400142B)をfresh展開し、共通CPU32群323件中322成功/Windows専用1skip、4.941秒。別途sealのfresh-child/既存command制限5検査も成功。13の新certificate検査、generic full compile/audit、厳密保存CUBIN受付、履歴file名変更、origin/baseline変更・subset・失敗・上書き拒否を含む。

生成cache必須のgenerationはhit、Slang0/GPU0、paired normalized baseline照合成功。保存Metal349のCUDA/Metalと両reflectionの全byteも一致した。実編成2入力の通常sealed packageは、共通CLI CPU3群16検査とnative2(1.789秒)が成功。これは新しいGPU実行ではない。

初回の広いCPU smokeは、weapon phaseの旧per-file監査が親量源の追加差分を扱えず停止した。次にquantity queryの同じ接続漏れを検出した。既存の厳密full-file deltaを先に逆変換して従来token検査へ渡し、元fixture/hashを保持した。新しい親量式・非再帰capacity読取の改変を拒否する故障注入も追加した。失敗package/captureを保持し、別packageで最終検査を行った。GPU/normalizer/期待値を書き換えて検査を通していない。

証拠はresearch/compiler-certificate-evidence/、checkpointはresearch/portable-compiler-certificate-checkpoint.json。今回のWindows command・GPU・Slang追加は0。現ソースのNVRTC/PTX/object/link/CUDA計算は未確認で、全目標は未達。次は回復蓄積29契約の共有GPU接続などを有用な固定checkpointへまとめ、必要な短いWindows検証だけを選ぶ。
