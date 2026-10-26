通常M5検証は修正版58daee47…の全106入力で成功しました（GPU4.240秒／子72.407秒）。独立sealは固定パッケージ内CLIから進行中です。wireの初回失敗・CPU監査失敗・controller更新による独立監査中断を保存し、修正版のみ新しいclaimで実行しました。全byteの保持監査はtrace絶対参照20語のstride移動を検証し、残る旧861,567,920byteと追加tail全0を確認。詳細は[共通wireと監査](portable-wire-preflight.md)。以下の実装時点の記録は履歴です。

# 共通resident実行器のarc tail

`coordinate-resident-arc` は既存logical-owner／ADD寿命／実HP死亡までの全106入力（native63、拒否43）を保ち、着弾の区間配列を独立したGPU buffer領域へ置く開発profileです。現在はCPU検査とpaired Slang生成を通過し、通常Metal検証を実行中です。sealedと全キャラ対応はまだ認定していません。

既存出力2,032,000語を移動・縮小せず、末尾へ32,786語の8slotを追加します。新strideは2,064,786語。CF武器bank、Geometry cache、typed対象、historyの各領域を保持し、共通 `arena-check --profile coordinate-resident-arc-v1` が既存ownerとの非重複を検査します。Runtimeの追加fieldはなく、CUDA／Metal reflection全体が旧保存Runtimeと一致します（stride138,952byte、同じ3buffer／48byte CUDA constant ABI）。

新entryは既存のcomplete event executorをそのまま呼びます。rootの前後と各着弾呼出しの前後でscratchを消去するため、早期拒否でも新tailが残りません。CPU比較は旧2,032,000語全体を旧アダプターで照合し、新tailの全wordも0と照合します。省略・ignored regionはありません。

区間処理はstandaloneでMetal検証済みの同じ生成bodyです。resident版の追加変更はGPU-owned inputのcommands→resultsとscratch offsetだけ。算術、評価順、1024区間／127対象／5098cutは維持します。新wireは新entryだけが受付し、旧entry／不足入力／旧strideとの混同を拒否します。旧profileの計算branchは条件付きで保持し、厳密なsource-delta逆写像は歴史監査専用です。GPU normalizerやCPU正本の変更には使いません。

関連140検査・共通制御555（Windows専用1skip）が成功し、固定package ae70b296…で再計算した106入力のinput/native指紋は旧版と全一致しました。初回package作成中に監査定義の不足を修正してしまったため、その作成は中止・記録を保存しました。以後はCPUゲート完了後に固定し直しています。新GPUの計算一致・独立seal・旧raw logical-prefixの保持は現在の検証対象です。

Windowsでは既定PowerShellと明示pwshの両方でprocesses段階が同じ数値codeで失敗しました。queryそのものとrow変換を分け、有限type ID／error-family IDと数値codeだけを記録するCPU診断を追加しました。queryを繰り返すfallbackやゲート省略はありません。新診断は `coordinate-arc-arena` のsealed packageを輸送用に使い、CLI `snapshot-check` だけを実行します。GPU sourceの6file closureと既存arc goldenは不変で、追加GPUは不要です。16故障検査と共通制御559（Windows専用1skip）が成功。PowerShell failureを解消するまでは新CUBINのstack量・CUDA実行結果は未取得です。

証拠は `research/resident-arc-arena-evidence/`、Windowsの保存診断は `research/coordinate-arc-arena-evidence/` にあります。現UIはCPU、全キャラ・全特殊効果対応は未完了です。
