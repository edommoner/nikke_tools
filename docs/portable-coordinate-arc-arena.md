# 共通arc区間のresource-backed配置

Windowsの保存CUBINは `portableEvents` のSTACKが199,352 byteでした。cold／コンパイラDLLなしのcache-onlyの両方でmodule load後のlaunchがcode2となり、readbackはありません。原因は未確定ですが、巨大なthread-local配列と値コピーを減らすことを次の検証対象としました。cache-onlyだけでは解消していません。元失敗・CUBIN・claimは保持します。

`portable_coordinate_arc_arena.py` は既存Slangの区間・形状・着弾関数本体から、同じ算術式と順序を持つresource view版を生成します。CUDA／Metal専用の計算分岐はありません。変更は引数のview化、レビュー済みの生存期間ごとのslot割当、値代入のactive区間コピー、出力と入力が重複する不正なprivate呼出しの拒否です。正本・旧entry・binary64・pow・strict normalizerは変更しません。

区間1024・対象127・cut5098を保持します。8slotをcaseごとに確保し、追加32,786 uint wordsを出力bufferの末尾へ置きます。同時に生存するarcs／covered／visible、extra／shifted、plane／next、fragmentを分離。未レビューのローカル配列が増えれば生成検査を拒否します。viewの境界アクセスはsticky errorとなり、通常entryは全出力を消去して64を返します。private演算の入出力aliasもclear前に拒否します。公開の旧by-value APIは変更しません。

M5 Metalで `coordinate-arc-arena`140（通常正例126、格納安全性5、拒否9）と `coordinate-landing-arena`40（正例26、拒否14）が全word一致し、GPU禁止fresh childで独立seal済みです。旧arc135／landing40の入力とnative指紋、各logical出力と連結hashを保持しました。追加scratchの全wordも0と比較し、監査除外はありません。GPU時間はそれぞれ約0.00949／0.38911秒（単一測定、性能保証ではありません）。

開発入口は共通CLIの `package --suite coordinate-arc-arena` と `package --suite coordinate-landing-arena` です。standaloneなのでresident generation-cache／full-world compiler certificateは使いません。Windowsではsealed packageを低優先度・2GiB・短時間上限でまずcompile-onlyし、保存CUBINをoffline解析します。stack減少と現CUDA計算はまだ未実証です。旧106入力のresident戦闘は今回変更しておらず、このprobeの成功を全戦闘・全キャラ対応とは数えません。

証拠は `research/coordinate-arc-arena-evidence/` と2つのsealed goldenです。前段Windows結果は `research/cached-cuda-landing-evidence/windows/`／`resources/`。Windows native textは共有時にLF化されたため、receiptの元CRLF byte列との一致を確認し、`native-original-bytes.json` に原byteをbase64で保持しました。可読textはLF、出所JSONに両方のhashを記録しています。新しい資源観測ではありません。
