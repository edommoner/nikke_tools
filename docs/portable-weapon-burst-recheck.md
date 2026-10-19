# 武器変更・散弾・バースト再突入の再確認

2026-10-20、固定版 `76e0c08aea7185ca00091a7a2efccdbda32181bb` を再実行しました。本体は `b0f1cf3` と同じで、CUDA／Metalの共通Slang・定義・fixtureを変更していません。依頼された接続は既存の共通実行器に存在します。

- Apple M5：1131正例・206拒否、実GPU時間0.4825秒。
- Windows RTX 3070 Ti：同じ1131正例・206拒否、BelowNormalの1回、ラッパー全体65.3478秒、120秒上限内。
- 両者の共通ソース・入力・全出力・status・検証コード・既存CPU参照リストは確定済みv45と一致しました。Metalでは読み戻した全resultsとcasesも直接比較しています。Windowsは保存済みv45との全出力SHA等の比較で、巨大な結果の再転送や追加GPU実行を省きました。
- Windowsの元HEAD・作業状態・サービスを保持し、残存検証プロセスは0です。リモートの実行と報告転送も終了しました。
- portable単体127件が成功しました。

共通の追加fixture23件では、時間・発数・トグルでの武器終了、子からの再入、装填通知内の切替、ペレットと実弾・銃口の分離、ペレットごとの丸め、発射中の対象／武器変更、バースト再突入とクールダウン、ゼロ値・失効・起動時の再突入状態を確認します。今回の追加検査は、再突入など7件でCPU BurstControllerが公開する全比較フィールドをGPUの保存済み読み戻しと照合しました。CPU結果はGPU入力に使いません。

証跡は `research/portable-weapon-burst-recheck.json` と `research/windows-portable-combat-v46-recheck.json` です。54MiBのMetal全読み戻しはGitで重複保存せず、`local-data/validation/portable-combat-v46-recheck-metal.json` に保持しています。元の確定済み報告・checkpoint・証跡ハッシュは保持しました。

再現する場合は、明示したPython環境で共通検証の後に保存済み結果を監査します。

```sh
.venv/bin/python scripts/verify-portable-combat.py --backend metal
.venv/bin/python research/verify-weapon-burst-recheck.py --report research/portable-combat-metal.json
```

## CPUに対する比較範囲と残作業

上記の合格は既存の共通契約に対するものです。古い武器変更fixture8件へ、補正していないCPU controller observerを追加適用すると、1件が全比較フィールド一致、7件に残弾・発数・待機時計の差分があります。うち1件は既に `research/portable-mode-session-contract.json` に明示した、終了直後の新セッションに対する差分です。残る6件は今回の調査結果として全差分を `exploratory_raw_mode_audit` に保存しました。CPU観測側の投影と実行器の挙動を区別して調べる必要があり、CPU側の不具合ともGPU側の正しさとも断定しません。期待値や実装を変更して差分を消していません。

既存のモード16件・武器87件のCPU参照検査と、新しい7件のcontroller照合は成功していますが、旧武器変更fixture全件のCPU完全一致へは読み替えません。全キャラ・全変種の認証は0/203体、通常画面はCPUです。全効果の接続と上記差分の調査は継続中です。
