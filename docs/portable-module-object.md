# 元PTX全体の再配置可能オブジェクト診断

`module-object`は、保存済みproducerの**元PTX全byteを変更せず**、固定ptxas12.4.131／sm86／O1／FMA無効／`--compile-only`で1回処理する明示実験。最大関数focusの0.315660秒・ret0と、元moduleのwhole-program assembly失敗は、入力範囲とcompile modeの両方が異なる。本実験はfocusと同じcompile modeで元module全体を比較する。結果が出る前に原因や必要メモリを断定しない。

```sh
python scripts/nikke_gpu.py module-object \
  --capture /path/to/new-module-object \
  --source-package /path/to/original-producer/package \
  --source-capture /path/to/original-producer/cold \
  --cache-entry /path/to/original-producer/cache/KEY.json \
  --phases /path/to/original-producer/cold/phases.jsonl \
  --ptxas /path/to/pinned/ptxas.exe \
  --original-workspace /path/to/original-workspace --timeout 60
python scripts/nikke_gpu.py audit --capture /path/to/new-module-object
```

固定sourceから共通`compiler-commands` packageを作成・fresh unpackし、CPU/Jobの`run --smoke`を1回だけ実施する。同じCPU検査を先行`--cpu-only --smoke`でも重複実行しない。元producer／元cache／phaseは保存済みのものを使い、NVRTC再生成・通常battleを実行しない。

## 共通経路と分離したidentity

focusと同じ`portable_partition_object.run`、tool SHA／PTX8.4／sm86検査、CUDA ELF検査、Job inspector、`run_job`、startgate、BelowNormal、2GiB／60秒、55秒wait＋cleanup5を使う。既存のjournal stage名`partition_object_*`も共通だが、source purpose、requestの`source_kind`、run mode、argv、tool／input／artifactの全identityでfocusとmoduleを区別する。別のrunnerやCUDA／Metalの計算本体は追加しない。

- 元producerは元immutable certificate／基準hash／全record／source closure／生成物／compile receipt／元Jobを読み取り監査する。現在のbattle基準と同一と偽らない。
- 元cacheのkey／bytes／SHA／phase receiptを照合し、そこから読んだPTX全byteとproducerの`compiled.ptx`を直接比較する。PTX分割・linkage変更・function削除・state移動・version書換えは行わず、`source_partitioned=false`／`source_bytes_unchanged=true`を記録する。
- `--candidate`を受け取らない。focus requestとmodule request、child flag、audit modeを混同するとcompiler前に拒否する。
- 専用`module-object-claimed-cuda.json`を排他的に作る。同一packageでの再実行・cap拡大・flags変更・通常assembleからのfallbackはない。失敗・partial・claimを保持する。
- 出力は`module.ptx`／`module.o.partial`／検証後`module.o`。identityは`diagnostic-module-ptxas`／`diagnostic-module-relocatable-object`で、通常PTX／CUBIN cacheへ登録しない。
- 親・子・事後監査で元入力を再確認する。結果監査は元argv、ret0、tool、入力・ELF全SHA、親子PID／作成時刻／Job所属、時系列・cap・終了後Job空を別々に検査する。

## 成立しても残る事項

`object_verified`は元moduleのオブジェクト生成とその保存証拠の検証に限る。対応版nvlink候補は公式archiveのSHA・member／LICENSEをMacで確認しただけで、実行・link互換性は未確認。ここからlinkやdriver／kernelへ自動移行しない。サービス未識別はpreservation=false／exit2、link／計算／full battle成立はfalseである。

元v135はcommands診断で、初期化／writeを持つfull battle entryではない。仮に本実験が成功しても本体CUDA全体、現在のMetal849、全キャラ／全特殊効果の計算証明にはならない。元moduleのobject化が成立すれば、PTX分割を増やす前に、元の定義・初期値を保つ単一object＋同版linkerの経路を優先して調べる。


## Windowsの保存結果

固定e909395のclean package `29839066123eb347d27ef19f98ea13fa554be349f16753362ec1d53fe977a65f`／2008 file tableがMacと一致。元PTX5,666,316byteの全byte一致gate、CPU193全成功、Job smokeも成功した。

ptxas12.4.131の1回は5.500616秒／ret0／stderr空。元PTX全体から3,327,472byteのET_REL／EM_CUDA、CUDA format124／755sectionsを生成し、共通CPU auditでも`object_verified=true`になった。SHAは`c92550d36a7bc5892ffcb9f002c297227b34f7184a74827394996c2afe44b79c`。Job26.855570秒／peak219,258,880byte／2GiB、BelowNormal・gate・親子所属・post空／欠落0／cleanupと観測エラーなしを確認した。service未識別はpreservation=false／CLIとauditはexit2のまま。原本・過去の失敗・partial・claims・CPU回収receipt・親環境は保持した。

追加ptxas1、NVRTC／link／driver／GPU0、再試行・fallback0。完全object／captureはWindowsに残し、Macは`research/portable-world-v135-module-object-peer-report.json`のpeer summaryまでで独立原本監査ではない。

この入力では、オブジェクト生成のためにPTXを分割する必要はなかった。ただしwhole-program assemblyの失敗原因・全実行器の性能／メモリは断定しない。次は保存済み単一objectを同版nvlinkで扱う明示実験を準備し、元object監査とidentity／Job監査を保持する。新しいptxasやNVRTCを再実行する理由にはしない。link後もcommands-onlyと現在のfull battle entry／CUDA数値比較を区別する。
