# 手動モード移行を共通GPUへ接続

`weapon_mode_swap` をowner別の静的入力として共通reload adapterへ接続しました。
GPUで条件付き `event:full_reload` のweapon_change候補を原文順に調べ、
既存 `beginReload` と完了通知dispatcherを使います。CPUの移行時刻や戦闘状態を入力しません。

reloadヘッダの既存領域に5bitフラグと専用tagを格納します。false／省略は元の全byteと同一です。
非zeroフラグにはtagを必須とし、旧「reserved領域に1」の負例をそのまま拒否します。
不正な型、mask範囲、孤立／欠落tag、残るreserved値を拒否します。
Runtime追加field0、stride138952、CUDA定数48B。GPU変更はevent macro、weapon phase、reload runtimeの3ファイルです。
正本CPU／既存CUDA／binary64／整数変換／pow／strict normalizerは変更していません。

## 判定と順序

- 正本と同じ位置で、無限弾薬のreload取消と装弾補正の後、通常click／sequenceより前に確認します。
- フラグ有効・モード外・通常reloadとpost-reload待機が非正なら、当人の条件付きfull_reload候補を確認します。
- 満弾でも開始し、そのtickは射撃せず、既存チャージを中断します。reload時間は既存のfixed／speed処理でラッチします。
- readinessでは発動上限を検査せず、完了通知のdispatcherが条件・上限を再検査します。開始後の条件失効や上限到達後の再試行も正本どおりです。
- 重複timing descriptorを保持し、条件成立時点で先頭の候補からreturnします。モード中は新しい手動reloadを挿入しません。
- フラグがfalseの旧経路を維持し、trueの場合は同じ補正を重複実行しません。

既存監査のhashを置き換えず、新3ファイルの有限deltaを逆投影して数値／weapon phase／query監査を再利用します。
hook除去、種別・条件・演算・範囲・順序の変更を故障注入で拒否します。

## 検証範囲

共通CLIの新suiteは `manual-swap`（30入力、native23／拒否7）、
`manual-swap-rosters`（全定義の実編成2）、`manual-swap-retention`（旧1137）です。
合計1169入力、native927／拒否242。成功した保存結果を別プロセスで独立sealしました。
旧1137の全input/native/output entriesとraw3,576,692,736Bを全byte保持しました。

CPUの24契約のうちcover sequenceを含む1例は、共通cover操作の未対応としてhostで明示拒否を継続しています。
GPU正例23へ紛れ込ませたり、no-opで受付したりしていません。
基本契約はflag有無、別owner、条件・通知のfilter、条件成立／失効、満弾開始、0／負reload時間、
チャージ中断、SRモード、再突入、発動上限、候補順、重複descriptorを含みます。

実シンデレラ：クリスタルウェーブは全定義と `weapon_mode_swap=True` を保持しました。
3秒は未成立対照、30秒では約16.483333秒の移行と、その後の値40の原文効果8dispatchを含む
全native結果・スキルtrace・物理履歴がMetalと一致しました。
物理履歴は112／1425件、省略0です。以前のフラグfalseのMG対照とは別の実行経路です。
旧レム／キロ／ギロチン等の既存履歴省略は保持したままで、解消したという意味ではありません。

入力とsourceは不変packageで固定しました。最初のv1はweapon_changeのwire種別番号を取り違え、
候補が抽出されなかったため不一致でした。保存rawをCPUで調べてkind2と確認し、入力／nativeを
変えず、修正した別v2で全件一致しました。種別対応の検査を追加し、旧失敗package／claim／rawを保持しています。
同じclaimの再実行、許容誤差やnormalizer除外の追加は0です。

旧範囲のCPU preflightは64.373秒、回帰67群389件は117.387秒（worker全体117.703秒）、
親の独立比較は68.299秒、GPUは10.748800秒でした。時間の中心はCPU確認です。
新30のGPUは0.054446秒、実2は2.594525秒。新sourceの初回Slang2回、後続2検証は生成cache必須・追加Slang0回。
full116／commands117 certificate14検査、最終sealed packageのCPU78検査、CPU専用reference26契約が成功しました。
詳細なpackage／seal指紋、CPU回帰数・時間、GPU時間、生成cacheの実績は
`research/portable-manual-swap-gpu-checkpoint.json` を参照してください。
両生成cacheはSlang前段の再利用であり、実NVRTC cache hitやCUDA戦闘一致の証明ではありません。

静的packingはGPU認定ではありません。全キャラ認定0、通常UI CPU、全ゴール未達を維持します。
Windows追加照会・native・compile・GPUは0。7プロセス終了はunknown・環境保全false・サービス未確認で停止継続です。
次は残る制御と未対応70分類を正本consumerに結び、共有CLIの契約・実行器を拡張します。

今後の効率化では、同一親プロセスの事前CPU照合結果を再利用できるか検討します。
入力／sourceの同一性、改変検出、独立sealを維持する必要があり、本変更では監査回数を削減していません。
