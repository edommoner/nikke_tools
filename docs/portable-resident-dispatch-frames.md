# 共通イベントフレームのGPU所有領域

`coordinate-resident-frames` は、既存resident arcの全106入力／native63／拒否43と、入力115680word・出力2064786word・全出力比較器を保持するsealed profileです。効果・計算式・処理順序を変えず、dispatch内の32個のFrameの保存場所だけをRuntime bufferへ移します。全106のMetal通常実行とfresh独立監査に成功しています。CUDAの物理stack測定は未完了です。

各ケースのRuntime末尾へ1024個のuint（4096byte）を追加します。CUDA／Metalのreflectionはともにstride143048、既存fieldの後のoffset138952で一致しました。commands／results／runtimeStatesの3資源、48byteのCUDA引数形式、既存入力・出力bankと容量は同じです。従来のローカルFrame配列経路も残ります。

共通の `dispatch_frame_type.slang` を実行器と境界probeが使います。`DispatchFrameRef` はケース番号とslot番号を持つviewで、個々のfieldのget/setがGPU所有のuint領域を読み書きします。Frame全体の読み出し・push時の保存は明示helperを使い、回復分配の既存inout consumerにも同じFrame値を渡します。[Slangのget/set accessor](https://docs.shader-slang.org/en/latest/external/slang/docs/language-reference/types-struct.html)で実装しています。

uint64は上下32bitで保存し、signed argumentはbitcastします。floatへ変換しません。paddingは全Frame保存時にゼロにします。index32以上の読み書きはerror1として隣接領域へ書かず、既存pushのdepth31制限も維持します。手動の32段イベントstackの順序・分岐・通知を変更しません。

## 実証済み範囲

共通CLIのsealed `dispatch-frame-storage` は5入力。32slot全部、NaN payload／signed zeroを含むraw64bit、符号付きargument、ケース間guard、field更新、既存Frameへのinout更新、範囲外読み／書きを検査します。M5で20800byte全部がCPU期待値と一致しました（GPU0.000112秒）。別fresh childの独立監査も成功し、追加GPU実行は0です。これはbit／領域のprobeであり、63件のnative battleや全キャラの認定ではありません。

従来のresident arc経路を再生成し、保存済みCUDA2684200byteとMetal2843972byteが全byte一致しました。共通initializerも従来と一致しています。全106の新しいCPU基準では、入力・native fingerprintが旧106とすべて一致しました。

## 厳密監査と次の検証

Frame移動のGPU source変更は専用の `portable-dispatch-frame-source-delta.json` で、current本文・SHAと旧baseline本文・SHAを固定します。旧監査を呼ぶ前にこの明示逆変換を行い、既存baselineやstrict生成コードnormalizerを変えません。追加dependencyやfieldの未登録変更も拒否します。定義を切り出した後の改変拒否テストは、新しい共通定義の実ファイルを検査します。

最初の共通制御の停止記録（未登録のsource逆変換と旧定義位置を読むテスト）は保存しています。GPU結果を成功へ書き換えず、監査修正を含む別固定packageで再検査します。全106のMetal実行・fresh独立seal・既存出力保持を確認した後、Windowsで必要な短い新sourceのコンパイル／資源測定を行います。物理stack削減や既存CUDA起動失敗の解消は、その実測前に主張しません。

## 全106のMetal通常実行

固定package `full106-frames-v2` で28群176テスト、fresh native63件／拒否43件、M5実GPU106件が成功しました。GPU4.103676秒、pipeline60.329996秒、含まれる子実行74.991052秒／180上限、再実行0。Runtimeの既存247fieldと3資源／48byte形式も保持しました。CPU preflightは410.717786秒で、比較では同じlive parentの63件を再利用しfresh追加計算0。保存CPU結果や独立監査への再利用はありません。

旧版と新版の875,469,264byteを8MiBずつ直接比較し、全部一致しました。SHA256は `4ecc755e4f17e2eaaa9c9eb013bbcaa2fb27422893982f910894287df96ced09`。全106の入力・native・output各fingerprintも旧版と一致しました。

fresh独立監査は同じ固定package自身のCLI／cwdで完了しました。新規GPU禁止childが全106を1回ずつ比較し、同じ監査からgoldenとcompiler certificateを生成しました。このMetal検証段階でのWindows追加実行は0回です。

## 独立sealの完了

6個の新規GPU禁止childで20/20/20/20/20/6入力を1回ずつ比較し、全106／native63が成功しました。合計513.541770秒、最長group134.245456秒／各180秒上限、live parentの再利用false、追加GPU0。同じ監査からgoldenとcompiler certificateを生成し、`coordinate-resident-frames` をsealed登録しました。既存全875MBのraw、失敗記録、元packageは保持しています。

compiler診断用の `compiler-full--coordinate-resident-frames --compact` を明示登録しました。実装・GPU source・upstream・fixture・goldenは保持し、選択外のPython研究／testだけを除く従来のprojectionです。全106のbattle packet自体はcompactへ拡張していません。Windowsではこの固定compiler packetのCPU検査・generation・短いPTX／object／link経路を使い、物理resourceを確認してから実計算へ進めます。

## 短いCUDA接続用の別profile

`resident-frames-device` は先頭4入力のsealed profileです。元のprefix選択器、全106と同じFrame source・native provider・全出力比較器をそのまま使います。全106のsuiteや認定範囲を置き換えません。選択55テストとMac CPU正本4件、M5 GPU4件（0.411577秒／pipeline cache hit）、fresh独立監査4件（17.404445秒／追加GPU0）が成功しました。33,036,576byte全体が保存済み全106の先頭4出力と同一です。

固定配布は `research/windows-source-packets/resident-frames-device-v1.json` と同名ZIP。compactは3574→2143ファイルで、除去は選択外Pythonだけ、保持した全ファイルとgoldenがfull版と同一。Macで再度55テスト／正本4件と共通591テストを通しました。

Windowsは既存の `gpu-linked` 経路と、全106 sourceから生成した保存CUBINを使います。full producer／PTX／object／linkの出所検査とfresh選択test／native4を維持し、生成cacheを必須にします。追加compile・fallback・retryはせず、2GiB／BelowNormal／外180秒・GPU child60秒を守ります。CUDA実計算の成功はまだ確認していません。


## 2026-10-29 更新前scalar／配列index修正後の全106再認定

現sourceのpackage964297f3はM5全106入力／native63／拒否43を1回実行し、全旧input/output/native指紋を保持した。GPU4.133649秒、cold pipeline62.416137秒、CPU正本430.231123秒、unit28群114.828383秒。14個のfresh GPU禁止childで全106を独立比較し582.646344秒、追加GPU0、live parent再利用false。新v2 goldenと、同じfresh監査のgoldenから既存helperで作ったsource-only certificateを登録し、旧基準は保持した。

約875MBの全出力は保存した。独立監査を起動する時にTMPDIRの指定が抜けていたため、終了後の全14群log／aggregateを永続proof rootへコピーし、全byte照合した。元tempと失敗記録は削除しない。現full CUDA計算は未認定。別のappend9契約のCUDA成功から全106へ外挿しない。証跡research/target-count-query-evidence/resident-append-full106-metal-v1.json。
