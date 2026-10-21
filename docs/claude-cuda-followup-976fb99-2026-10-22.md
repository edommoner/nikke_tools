# CUDA成立に向けた限定レビューの照合

ユーザー依頼のClaude Codeレビューを、固定976fb99の武器分割・Windows v128失敗・全件転送メモリへ絞って継続しました。Claudeは提供抜粋だけをsafe-mode／tools無効／MCP無効／session保存無効で読み、204.171秒・exit0で回答しました。prompt101,658byte、個人設定・認証情報・rawを渡していません。指摘は以下の通り実ソースへ照合し、レビュー回答をそのまま設計の正本にはしていません。

## 採用する結論

**打ち切りpeakから資源改善量は分からない。** v128の観測peakは2GiB上限に達した値で、必要量の全体ではありません。武器rootのvirtual宣言70と最大executePortableCommands10927は、次の観察対象を選ぶ情報に留めます。PTX総量は約8.75MBのままで、単なる文分割を繰り返す根拠は増えていません。

**次はcompilerの段階を分離する。** 保存PTXをdriverとは別のoffline ptxasプロセスへ渡す案を優先候補にします。成功しても、toolkit／driver内compilerの版やオプションが違うため、「原因はdriver常駐分」とは断定しません。whole失敗後にrelocatable試験を自動追加する案も採用せず、失敗結果から新しい仮説を決めます。各段階2GiB／60秒、同条件再試行・上限拡大はしません。

**全件の転送と監査には固定上限のバッファが必要。** CUDAのzero／readback各2.50GBとoutput.rawの追加copy、親監査の全体readはソースで確認できました。796件・全出力・比較を維持したまま、転送と親監査をstream化する必要があります。これはmodule成立とは別の未実装項目です。native再利用はCPU oracle closure／input／Python runtimeへ束縛し、decodeと実field比較・独立sealを維持できる設計が出来るまで採用しません。

## 不採用または未確認の指摘

**scratchのcuMemAlloc後にmemsetがないことは、未初期化値依存の証拠ではありません。** executePortableEventsはresident／非resident双方でinitializeRuntimeを呼んだ後にinitializePortableProgramへ進みます。runtime_init.slangは共通mutable宣言から既存canonical generatorで生成し、その完全一致をCPU検査しています。例外のprivate teamEventはinitializeWorldTeam、banked fieldsは既存LAZY_BANK_INITで初期化します。paddingは宣言fieldではなく、丸ごとstateを出力へコピーしていません。したがって今回、追加のscratch memsetやpoison GPU実行を必須にはしません。

**着弾マクロによるreturnは現行定義にありません。** WORLD_POOL_PHYSICAL_TARGET／WORLD_TEAM_PELLET／WORLD_FRACTION_AUTOの全6定義を確認し、展開後のCUDA／Metal landWeaponPelletsにも末尾以外のreturnがないことを保存コードで確認しました。将来の混入は実リスクなので、依存マクロも辿ってreturn／break／continueを拒否するCPU契約と直接・間接escapeの故障注入を追加し、7検査が成功しました。GPU本体は変更していません。

**readStat／collectStatsがinlineで複製された、という推測は未確認です。** いずれも既存ソースと生成CUDAでnoinlineです。f64Add／Mul／Divもnoinlineで、まとめてannotationを足す案は採用しません。一方、effectiveCharge／ammoInstantCapacity／hasInfiniteAmmoなどには非noinline境界があり、既存cuda_statisticsで実際のknown-call graphを保存しました。depth3でnoinlineを止める字句解析で、実compilerの展開量やメモリ原因の証明ではありません。

**resident inoutの別名渡しは一般的な注意点です。** 今回追加した5境界では、Runtime fieldを同じ呼出しのout/inoutへ渡さず、独立したWeapon／snapshot／scalar出力を使います。caller／formalの型・順序・inoutを契約で検査し、全796結果を保持しています。これだけで、全未対応キャラを含む既存全call siteのalias安全性を認定しません。具体的なalias対やnative反例がないため、現在のloweringを書き換える根拠にはしません。

## ツール互換性と次の入口

Windowsのread-only所在確認では、既存ptxas.exeはCUDA11.3.58、nvcuda.dllは617.14でした。保存PTXはNVRTC12.4系の8.4なので、11.3 assemblerへ渡したり.versionだけを改変したりしません。[PTX ISA8.4公式表](https://docs.nvidia.com/cuda/archive/12.4.1/pdf/ptx_isa_8.4.pdf)でCUDA11.3はPTX7.3、CUDA12.4はPTX8.4です。

対応する独立component候補は、NVIDIA公開の[nvidia-cuda-nvcc-cu12 12.4.131 Windows wheel](https://pypi.org/project/nvidia-cuda-nvcc-cu12/12.4.131/)（16,509,606byte）です。必要時はSHAを照合して隔離folderへ展開し、既存SDK・PATH・driverを変更せずに使う方針です。まだdownload／展開／offline compileはしていません。[PTX Compiler API](https://docs.nvidia.com/cuda/archive/12.8.0/ptx-compiler-api/index.html)と[NVCC ptxas仕様](https://docs.nvidia.com/cuda/archive/12.9.1/cuda-compiler-driver-nvcc/index.html)を次のCLI設計の一次資料にします。

- prompt: /tmp/nikke-review-cuda-976fb99.prompt.txt
- 送信manifest: /tmp/nikke-review-cuda-976fb99.manifest.json
- 回答: /tmp/nikke-review-cuda-976fb99.response.txt
- 回答SHA256: efc56fecc120061c84587fd66da3573f2b1f70f3f8862b756fd83470aac1afe0
- 実行記録: /tmp/nikke-review-cuda-976fb99.run.json
- 使用スキル: /Users/edo/.codex/skills/claude-code-reviewer/SKILL.md

全キャラGPU認定0、UI CPU、entry_reload cover4件・新版CUDA計算・stream転送は未完了です。

補強後の固定sealed package9ba632d9をfresh展開し、共通smoke93件中92成功・Windows専用1skip・失敗0でした。976fb99の実行済みpayloadとの差はguard／そのtests／manifestだけで、GPU source・全adapter・transportはbyte同一です。追加のMetal／CUDA実行は行っていません。
