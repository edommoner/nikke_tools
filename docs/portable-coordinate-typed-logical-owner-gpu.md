# 論理所有者の共有GPU接続と証跡の復旧状態

`coordinate-typed-logical-owner` は99入力（native56／拒否43）のsealed基準です。ADD所有者のHP shield／projectileと破壊済みshieldからのcounter子fieldを共通Slangへ接続しました。元Primの完全5人・71定義・武器／成長を保持し、別宣言counter監査2効果で通常fieldのADD0と所有者ADD1を区別します。BODY／ADD0／ADD1のreceived_dmg_pctは0／0／17でした。

**現在の制限:** 成功後の環境切替で `/private/tmp` のworktreeとcaptureが見えなくなりました。原因は未確定です。Git indexからコード・golden・source certificateを回収しましたが、元raw・独立監査receipt・実行captureは回収できていません。以下の実機結果は消失前にツールで観測した履歴です。現在の保存結果の再監査はできず、GPUを再実行してrawを再構成していません。readinessも履歴成功とraw未取得を区別します。

## 実装と過去の観測

新policy `logical-owned-current-fields-v1` はheader12=3／15=2。旧BODY policy12=1と旧拒否12=2を保持し、weapon13／aim14／live11も必須です。型付きstateの直接owner kind/id/generationから既存actor poolのexact slotを解決し、counterContextAddとfield recipientが同じ所有者を使います。物理event／impact handleを保持し、未知／別世代ownerをerror64で拒否します。通常のcurrent damageはcanonical照準選択を維持します。private compilerはpredicate検査viewだけを投影し、実命令は変更しません。

`world_coordinate_typed_logical_owner_entry.slang` は既存entryをincludeします。CUDA／Metalで計算本体・定義・比較器を共用し、source監査にはstrict full-hash inverseだけを追加。backend変更は専用entryのwhitelistです。数値・正本・normalizer・CUDA compile cache本体は変更していません。入力115680word／出力2032000word／Runtime138952byteを維持します。

初回packingは旧HP probeのBODY制約でGPU前停止しました。明示weapon-only logical descriptorだけを別途許可しています。初GPU版07b9d1e3…はHP geometry受付にもBODY guardが残り、新HP2件が初期status64。projectileの保存結果subsetはCPUと一致し、旧88の全715264000byteも保持していました。新policyだけに限定したHP guard修正を加え、全99 input/native期待値は維持しました。

修正版package ID `2b99038d52f6f3fe6939c6d001062fcc55614f51d400c719bc5d43061fafc3db` のMetal通常比較は全99成功。CPU preflight327.520719秒、M5 GPU4.182172秒、library1.893278秒／pipeline94.638508秒、bounded child103.824826秒、timeoutなしでした。初版からrawが変わったのはHP正例88/90とowner世代拒否95だけで、旧88全715264000byteは完全一致していました。

拒否95は正例90とのinput差分がowner世代1→2の1wordだけ。実landing1件とcounter ready、実ADD世代1の後に64となることをreadbackで観測しました。要求2／実1の世代不一致の証明であり、実ADD再出現の戦闘証明とは区別します。

GPU禁止の別child5つで24/24/24/24/3件を独立監査し、全99/native56に成功しました。各child180秒以内、80.332103／75.472479／135.261316／119.539291／5.208292秒、総418.076018秒。同じ監査からgoldenとsource certificateを生成し、二重sealはありませんでした。GPUは初版失敗1＋修正版成功1、retry0。成功rawの観測SHAは `3612889c652450c6e40f295cefe87355aa91f2155ca7a9cf8334ca33afc35bb3` です。現在そのrawを読み直せるという主張ではありません。

最終metadata版726ddf4c…はreadiness／登録／golden／certificateの4file差分だけで、全CLI関数AST・native producer／比較器／tests／GPUを保持していました。関連117／制御517検査成功（Win専用1skip）、generation必須hitも観測しました。そのZIPも現在は回収できていません。Windows向けsource診断packageのMac CPU検査も成功しましたが、Windows／CUDA実行は0です。

## 永続領域での復旧

回収コードはコミット19df7caf。worktreeは `/Users/edo/Documents/ChatGPT/nikke_tools/.portable-recovery/runtime-resident`、今後の検証保存先は同じ `.portable-recovery/proofs/`、生成cacheは `.portable-recovery/caches/slang-generation-v1` とします。ローカルGit excludeでprimaryの通常ファイル一覧から除外し、個人設定は共有しません。

回収したgoldenは61,372byte、SHA `4dadfb36b2f6a29972532be66aaf63549f2d3f3bb539be742678c64680e2b9fa`。source certificateは27,861byte、SHA `4bf5863d9051c6578e9843cb69b67de0571346d881c3db20cbd4b43c7e11cefa`。Git blobと完全一致しています。現在の環境で新しいimmutable packageを作り、CPU検査とCUDA/MSL生成・sealed生成基準一致・永続cache必須hitを確認しました。現在のGPU計算成功やCUDA device成功とは数えません。

復旧記録は `research/portable-coordinate-typed-logical-owner-recovery.json`。失われたreceiptを元ファイルとして再作成せず、履歴観測と新しいCPU証拠の出所を明示しています。raw再監査は原本の復旧まで停止します。次の実装はADD実生死／再出現・field lifetimeを新しいCPU契約から進め、新しい実装・入力の検証成果は永続領域へ保存します。ゲーム仕様／公開GPU／現CUDA／全キャラは未完、全キャラ認定0／UI CPU／目標未達です。
