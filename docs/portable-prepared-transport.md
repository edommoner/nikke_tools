# 検証済み入力の共通転送とPTXコンパイル

CPUゲートが生成した入力をCUDA/Metalの子プロセスで再利用する。`prepared-v1` はCPU比較の成功後にだけ `input.bin` と `input-preflight.json` を公開する。子は不変packageを全件検証し、入力の件数・幅・全体SHA・全行SHAとCPU成功receiptを照合する。adapterの再importと再packingは省く。独立auditも同じ照合を行う。入力不足・改変時は停止し、legacy経路へ戻さない。旧captureは従来経路を保持する。

GPUソース、18入力、数値設計、正本、normalizer、cache identityは変更していない。新経路のMetal18は全件一致し、旧readbackの56,623,104バイトと同一。子の入力確認はMac実測0.005087秒。最終readerで保存入力を再検査済み。これはWindowsでの転送時間改善の実測ではない。

固定v3 package `5972500de3f882e7defd03658a2781dabc382060e648928c72549a393b015c11` でMac/WindowsともCPU64・native13が成功。関連CPU146検査も成功。Metal実行は先行v2 package `aab5101c804ad80ba4c38d29f9efb17dc5e52fc6c3133a863bdc2b0aed81e377` で、最終v3でのGPU再実行は行っていない。

Windowsの既存制限付きpacket実行器へ `--stage compile-ptx --backend cuda` を追加した。これは既存CLI `compile --artifact-kind ptx` を呼び、内側60秒・外側最大180秒、2GiB、BelowNormal、Job/gate/終了観測を維持する。明示的な元workspaceが必要。GPU driver/context/launchは起動しない。compiler成功、数値計算成功、環境保全は別々に判定する。

WindowsでCPU stageとPTX compileを各1回だけ実施。PTXはNVRTC 22.5362061秒で成功し、4,952,590バイト・SHA256 `66b44cee89fc84b28a222d70d8f4b23ac6d435dc97eb64ec679442db38f24933`。生成cache hit/Slang追加0、driver0/GPU0。PTX cacheは完成し新claimは残らず、旧CUBIN未完claimは元SHAのまま保持した。両Jobは終了後空、既存プロセス欠落0。サービス未確認なので環境保全false、全体stage exit2を成功へ読み替えない。GPU数値は未検証。

Windows CPU stageは全体62.747秒、package検証27.207秒、CPU群26.804秒（worker検証14.395秒を含む）。compile stageは全体65.946秒、親検証15.140秒、子検証16.045秒、NVRTC22.536秒。入れ子時間は重複するため合算しない。現在の大きな準備費用は全件ファイル検証であり、GPU計算時間とは区別する。

証拠は `research/prepared-transport-evidence/`。Windows summaryは保存結果に基づくremote最終報告であり、PTX本体をMacで独立監査した証拠ではない。remote turn `01a16aa6-3ecc-7b32-ae11-0f2126820c14` はterminal、再試行0。過去の7プロセス終了は操作なしとの回答とgame/video利用の可能性だけでは因果を特定できず、cause unknownを維持する。

全キャラ対応は未達。245/266は静的packingであり、全キャラ認定0・残20分類model gap・通常UI CPUのまま。次は必要な短いCUDA数値確認と、通常戦闘の生成元・選択・迎撃/倍率の共通実行器接続。独立typed probeの成功を通常戦闘の全対応として扱わない。
