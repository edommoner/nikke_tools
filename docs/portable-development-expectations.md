# 開発用CPU基準の重複計算を減らす

`package --develop --native-baseline-package PATH` は、固定済みの同じCPU契約から期待ハッシュだけを引き継ぎます。パッケージ作成時のnative計算を省き、`run` 前の全CPU再計算と、新しいGPU結果の独立 `seal` を維持します。実行時の参照値・CPU結果・GPU出力・コンパイラ成果物をキャッシュする機能ではありません。

CPU契約とテストを先に固定し、その後GPU実装だけを変更する段階で使います。

```sh
# 新しいCPU契約を最初に固定する。この作成では通常どおりnativeを計算する。
python scripts/nikke_gpu.py package --suite SUITE --develop --compact --out /tmp/cpu-contract.zip
python scripts/nikke_gpu.py unpack --archive /tmp/cpu-contract.zip --dest /tmp/cpu-contract

# GPU実装を進めた後、同じCPU契約の期待ハッシュを使って新しいpackageを固定する。
python scripts/nikke_gpu.py package --suite SUITE --develop --compact \
  --native-baseline-package /tmp/cpu-contract --out /tmp/gpu-development.zip
```

既存のsealed suiteでsourceが一致している場合、最初の `package` は `--develop` を付けずに既存goldenから作成できます。baselineと候補は同じCLI、suite、選択ケース、同じpayload形式で作ってください。古いCLIや異なるcompact範囲を黙って互換扱いにはしません。

全CPUコード・テスト・データ・host transportはbyte一致が必要です。変更を許すのは `gpu/*.slang` と、既存の `tests/fixtures/*source-delta.json` のGPU部分だけです。ledgerは既知の `sources`／`added_sources` 形式を検査し、baseline本文・hash・CPU部分・key集合を保持します。GPUのcurrent本文／hashは各固定sourceの実byteと照合します。CPU関係の変更、新しいledger、入力・ケース順の不一致はnative計算を開始せず拒否します。不一致の原因を確認し、意図した新しいCPU契約なら通常の `--develop` で固定し直してください。基準を通す目的で期待値を更新しません。

新packageのgoldenは入力hash・現在のGPU source hash・各ケースのnative期待hashだけです。旧GPU出力hashと生成物hashは引き継ぎません。`native_expectation_baseline` は出所と候補payloadに結び付けたreceiptで、計算証明ではありません。出所のCLIを実行せず、現在の検証器で元packageを読み取り検査します。新packageの検証はfresh preflight／独立sealを省略するreceiptや、runtime値・出力を混ぜたgoldenを拒否します。

開発packageのCUDA実行禁止、Metal実証後の明示seal、Windowsの低優先度・2GiB・180秒上限、生成／CUDAコンパイルcacheの実行時検査は従来どおりです。CPU期待hashの引き継ぎはCUDA cache hitの証拠ではありません。

実証では35入力・22nativeのパッケージを、native基準関数を禁止した状態で3.481898秒で作成しました。通常CLIからの作成も同一package IDです。新経路の `run --cpu-only` は全22nativeを177.031370秒で再計算して一致しました。最終版の変更はledgerのUTF-8明示読取だけで、入力・計算producerとreuse／validate関数の不変性を検査し、この完了済みCPU検査へ結び付けています。関連60／最終制御488検査成功（Windows専用1skip）。CP932既定を模したUnicode ledger検査を含む8検査で境界を確認しました。この変更のGPU実行・Windows依頼は0回です。GPU計算本体は既存の独立監査済み35入力から変更していません。
