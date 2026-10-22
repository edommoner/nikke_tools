共通Slangへ非座標skillのpierce／explosion到達、生成値・reach receipt、interrupt群のHP／総ダメージ外計上・吸血を接続しました。現在`parts-skill-world`46（native41／拒否5）がMetal成功・独立seal済み。生成後buff変更・複数破壊・壊れない対象・周期3tick・共有吸血を含みます。最終849と実4もMetal成功、旧849全raw約2.67GB・実4全raw・従来26入力を保持。物理interrupt・座標・deferred・実CUDA照合・CUDA生成cache改善は未完了、全キャラ認定0、Windows新規実行0です。詳細は[到達処理](portable-interrupt-reach.md)。以下は履歴です。

# 次の接続：到達interrupt packet

7bit codec単体は共通Slangで実装し、Metal154入力（正例140／拒否14）と独立sealを完了しました。128通りの巡回順（全slot×全位置）・境界・再利用・tag／membership／padding破損を全786432wordで照合しています。`interrupt-packet-codec`で固定packageを作成できます。記録は`research/portable-interrupt-packet-codec-checkpoint.json`、実装は`gpu/interrupt_packet_codec.slang`です。本体にはまだincludeせず、旧periodic表現と既存849／40のソースを維持しています。

以下は本体接続の設計候補です。到達interruptのGPU実装・数値認定は未完了です。kind6 sourceの入力・世代・期限は共通poolへ接続済みで、届くskillとphysicalは明示拒否します。canonical Impactのkind2はPROJECTILE、kind6のpublic命中カウンタは未接続です。

正本BossScript.interrupt_hitsはliveでreach内の全Targetにextra_hits／extra_dealtを加え、breakableなら全damageをdealtへ加えてから対象リストを返します。その後にtimelineが各対象の吸血を実行します。キャラtotal・accumulate_damageへは加えません。parts_skillだけではinterruptへ届かず、pierce／explosion本来のreachを別に評価します。partのcallbackが終わった後でinterruptのlive集合を取る順序を保持してください。

生成値は同じ取得済みstatsから作ります。既存の7因子に加えたno-core第3因子を再利用し、第5因子はpart補正を外してintercept補正を一度加えます。body／partとの比から逆算せず、整数化前の乗算順を維持します。rangeのsnapshotも生成時に取り、名前付き子通知やpartの吸血callbackによるbuff変更後に再計算しません。

FrameはRuntimeのmemberではなくdispatch内のローカル32要素です（event_runtime.slangのstruct Frameとdispatch内宣言）。次のmetadataはFrameへ明示的に持たせる候補です。Runtime strideやRootParamsを変える必要はありませんが、生成CUDA／Metal・局所stack・制限付きcompileの実証は別途必要です。

receiptは2048容量を減らさず、既存periodic packet38wordのversion付き表現を検討します。現在は6word prefixと128slotを8bitずつ詰めた32wordです。slot範囲0..127を7bitへ詰めると28wordとなり、4wordを確保できます。generationはslotとは別のprefixの32bit birth ordinalであり、切り詰めません。

| word | interrupt付きpacketの候補 |
| --- | --- |
| 0..5 | count・完全なbirth ordinal・128bit membershipを保持 |
| 6..33 | 128slotを7bitで保存 |
| 34..35 | 生成済みinterrupt damageのbinary64 |
| 36 | interrupt reach |
| 37 | codec version／検査tag |

この圧縮はinterrupt metadataがあるpacketだけに適用し、旧periodic definitionと旧packetのbyteを維持する候補です。at+7のlow indexと未使用high bitで明示的に区別し、通常・periodic・random最終tick・slot再使用を検査します。index127の最後7bitはword33内で終わり、metadataへ読出しがはみ出さないこと、全128slotの順序・membership・generationを独立codecで故障注入してください。modeの判別・検証を省いて既存の38wordへ上書きしてはいけません。

interrupt aggregateはpart bank終端785424以降の未使用領域へ5人分の10wordを置く候補です。全領域台帳・初期化・未使用時の旧rawゼロ保持を確認して確定してください。既存のslot別extra領域はpartとinterruptでslotが異なるため共有できます。HP適用はkind6のtotalを加えず、breakableの余剰damageを切り捨てず、extraではdirect hits／landedを増やしません。interruptにはtyped counter callbackを合成せず、正本の吸血だけへ接続します。

最初に既存5skill拒否をnative比較へ移し、非飽和吸血と総ダメージ外の計上を検査してください。physicalの拒否は実装まで維持します。source変更後の既存849・実4・現40の保持と独立seal、両生成、可能になった時点で短いCUDAだけを行います。Windows7終了の原失敗を変更したり、同じCUBIN生成を繰り返して埋め合わせたりしません。
