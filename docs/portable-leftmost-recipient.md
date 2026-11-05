# 属性・武器種で選ぶ左端の生存者

`allies_code_weapon_leftmost:CODE:WEAPON:N` の共通GPU実行を、開発専用入口
`gpu/world_leftmost_entry.slang` に接続した。候補の属性と武器種は既存正本コンパイラが
固定する。発動時の生死判定と左からN人の選択はCUDA／Metal共通Slangで行う。
正本は `buff_manager.py:_resolve_target` の `_alive(_code_weapon(...))[:int(n)]`。
先に候補をN人へ削ると、左端の戦闘不能者を飛ばした後の生存者が不足するため、
GPUも生存者を順に数えてから打ち切る。

既存selector24の候補maskと人数を使用し、0〜5人を受付する。形式不正、6人、
先頭0付き人数、負数、全角数字を受付しない。lazy group・順序指定・状態名・
除外flag・mask範囲外などの不正wireはGPU側でも拒否する。buffとinstantの双方で使う。
候補は元の編成metadataであり、途中の武器変更を候補表へ逆反映しない。

共通コードの変更は `gpu/recipient_runtime.slang` のprivate macro内13行と新入口だけ。
旧入口の生成CUDA/MSLは以前の出力と全byte一致した。新入口のRuntime反射も旧実証と
完全一致し、stride138,952 bytes、入力104,400／出力786,432 wordsを保持した。
CPU正本、binary64演算・整数変換・pow、normalizer、Windows wrapperは変更していない。
新しい厳密差分ledgerを既存監査の前へ接続し、従来コードを逆投影する。
許可する差分以外はhashと故障注入で拒否し、正規化規則を追加していない。

## 検証結果

- 合成13契約：0／1／2／5人、候補なし、武器種の穴、左端の戦闘不能、発動間の死亡、
  生存者不足、instant回復、battle_start。対象が違えば防御力またはHPに差が出る。
  既存のbattle・trace・get_buffs／target解決／random.sample回数を保持した。
- 実編成6契約：トリナ全定義を含む3編成を3／30秒で検証。候補なし、2人から左端、
  最後の枠だけが候補の3通り。編成の定義数は76／76／78、正本の対象解決は計22回、
  物理射撃は計2,768回。GPU比較は既存の全状態と容量内履歴であり、全射撃・全対象選択の
  個別GPUtrace認定ではない。1,018射の入力など、既存履歴の省略数も既存比較器で検査する。
- 共通CLIのMetal74入力が一致：正本59／拒否15。新21＋実編成6＋旧持続時間47を合成。
  Apple M5のGPU時間4.338秒、生成cache hit、追加Slang起動0。
  旧47の147,849,216 bytesと新21の66,060,288 bytesは以前のrawと全byte一致。
- 最終不変packageでCPU8群41検査（skip0）、単体合計4.838秒、native事前比較7.917秒。
  保存Metal出力の独立seal74も成功し、再監査中のGPU呼出0。

静的inventoryは235／266（base175／203）。既存234入力のSHAと残る分類の順をすべて保持し、
トリナが新たにpacking可能になった。対象指定に由来する3分類が消え、残り44分類。
packingは全キャラ実戦認定ではない。UIはCPU、全キャラ認定0、development_onlyを維持する。
旧1,612入力全体を新private入口で再実行した証拠はまだない。

## 保存結果の修復と再利用

初回21入力ではGPU完了後、比較器の既存healing_storage decode接続不足で停止した。
比較器を修正して元rawをreplayし、独立sealした。初回74入力では合成アダプターが
拒否15件のdomainをNoneにせず、CLIが成功status0を期待して停止した。
既存のstride検査付きcombinerへ委譲し直した。

後者はnative baselineの拒否メタデータだけが変わるため、既存CLIの明示migration経路へ
`leftmost-rejection-domains-v1` を追加した。固定package
`831de07363be74bf457240464fb810568c95984e9de83355862ee2f79f8e3964` と、旧／新adapterの
正確なhash、74行中の固定15行だけを対象とする。`{rejected:true}` を既存CLIの
`{status:64}` 表現へ訂正し、59正例のnative期待値・全入力・GPU・transport・正本を変更できない。
生のstatus64、生成物、元実行claim／制御結果を再監査する。これは汎用の差分免除ではない。
元の失敗、raw、claimはすべて保存した。GPUの同条件再試行は0。

```sh
# 不変packageのrootをcwdとして実行する
python scripts/nikke_gpu.py reference --suite leftmost --out /tmp/leftmost-reference.json
python scripts/nikke_gpu.py reference --suite leftmost-rosters --out /tmp/leftmost-real-reference.json
python scripts/nikke_gpu.py package --suite leftmost-retention --develop --out /tmp/leftmost.zip
python scripts/nikke_gpu.py unpack --archive /tmp/leftmost.zip --dest /tmp/leftmost-package
# cd /tmp/leftmost-package 後、まず --cpu-only で検査。Metal実行は固有captureで一度だけ行う。
```

今回の作業checkoutにはskillの `storage-check` サブコマンドがないため、実行前に
`shutil.disk_usage` で全74入力／出力263,686,276 bytes＋14GiBの予備を明示確認した。
記録は `research/leftmost-gpu-evidence/storage.json`。削除や圧縮率は空き予算に含めていない。

実装・失敗・再監査・inventory・保持比較は `research/leftmost-gpu-evidence/`、
現在の境界は `research/portable-leftmost-gpu-checkpoint.json` に記録した。
Windows操作は今回0。現在sourceのCUDA実機一致、広い復活／nested list混在、
新入口の全保持検証、残る44分類と全カタログ実戦が残る。
以前のWindows7プロセス終了は原因unknown、preservation_verified=falseのまま。
