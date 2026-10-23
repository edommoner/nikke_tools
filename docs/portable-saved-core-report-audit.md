# 保存CUDA coreレポートのCPU監査

`saved-core-report-audit`は、共有済みの小さなレポートをGPU再実行なしで照合する共通CLI。信頼するmanifest SHAを明示し、相対パス・byte数・全payload SHA、source/input/native/output指紋、既存strict normalizerによる生成CUDA/Metalの指紋、8-byte core Runtime、cold/warm cache identityを確認する。payloadのcodeは実行しない。

```sh
python scripts/nikke_gpu.py saved-core-report-audit \
  --report-root /absolute/saved-report \
  --manifest-sha256 e7c93111b6acb67f312df3c617bc8b21dc5778fc6ae9cfcd806ef3eaf1226448 \
  --out /tmp/new-saved-core-audit.json
```

出力`passed`はレポート整合性を指す。`calculation_verified`、`CUDA_raw_independently_audited`、`compiled_CUBIN_independently_audited`はfalse。raw/CUBINを含まないsanitized copyを、独立した実行や全戦闘CUDAの証拠へ昇格させない。元の環境保持失敗とcause unknownも維持する。manifestと各JSONの環境保持主張が一致することを確認し、missingがあるのに成功とする矛盾を拒否する。

既存v4の26ファイル201,729byteは、`codex/cuda-damage-accum-core-v4-report` commit `62a173324f126771b6e6b2683652f1d2175596b9`から取得した。25payload＋manifestの全指紋、41入力の入力/native/output報告指紋、3 source、両backendの厳密生成指紋がMetal core goldenと一致した。cold1.453秒、file-only warm hit0.085秒/追加compile・GPU0のcache receiptも一致する。現在の戦闘146 sourceのCUDA検証ではない。

保存集計ではouter missing7/inner missing0、7件のinner-before/after存在0、対象parentとの一致0、pre-gate Job所属0。7件は全てouter childより前に作られ、以前の5c4bfcd7件と完全に同一のidentityは0。roleは全件unknown、CPU batch wall時刻はunavailable。内側snapshotに含まれなかったことと、終了原因の特定は別である。利用者のゲーム/動画利用を原因と断定しない。

監査はbounded manifest・payload破損・native指紋改変・cache artifact不一致・Runtime/input count・path escape・環境保持の誤昇格の故障検査を持つ。`saved-core-report-audit`検査用packageをfresh unpackし、`run --backend metal --cpu-only`で検査する。生成CUDA/Metalのfixtureも小さなsupport fileとして明示し、梱包漏れを検査した。

fixtureはmanifestでbyte単位に固定するため、対象フォルダーだけGitの改行変換とwhitespace検査を無効にする。元の生成コードのCRLF/空白を修正せず、代わりにmanifestの全byte SHAで検査する。効果コードやstrict normalizerの検査は変えない。Git indexの全26ファイルも検証済みの元byteと一致する。
