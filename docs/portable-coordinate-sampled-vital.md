# 乱数戦闘の武器変更・回復

`coordinate-sampled-vital` は、武器変更・HP回復／減少・遮蔽物回復を乱数戦闘へ接続するprivate profile。共通Slangの既存実行器、効果IR、CPU観測器と比較器をCUDA／Metalで使う。固定120入力（CPU正本112／拒否8）がApple M5 Metalで全一致し、保存出力の独立監査も成功した。現在ソースのCUDA実行は未確認。全キャラ元定義の認定、全武器フラグ・全回復組み合わせと公開GPU受付は残る。

## 共通実行器への接続

新たな武器・回復の計算本体は作らず、kind2（武器変更）、kind6（HP回復）、kind7（遮蔽物回復）、kind8（現在HP割合減少）をこの乱数profileへ明示受付した。既存の武器選択、entry reload、初弾係数、弾数消費、期限・toggle・置換と、受療補正、caster最大HP基準、通知子queue、吸血、通常reload中の遮蔽物への被弾を実行する。通常damage・旧B3／opt-inの保留queueと同じMT・着弾順を使う。

新29世界はauto／charge、散弾4×総口3、charge3×総口2、初弾277→通常123、2発終了、entry待機中の期限切れ、entry reload、遅延発動、mode置換／toggle、2射手、通常skill子、両B3との混在を含む。回復はself／allies、0／負値／上限超過、受療bonus、caster最大HP基準、別caster、回復通知の子、packet吸血、損傷した遮蔽物の回復と破損後の非復活を検査する。基礎武器の値で代用せず、正本の実発射時にpellet／総口／係数を受動記録し、full-charge通知の実総口を親参照量の検査に使う。

29世界で物理457ペレット／1205packet、通常skill本体33計算、旧B3本体2計算、着弾1252packet、MT2812word、mode72射撃、HP回復handler37回、遮蔽物回復handler4回を観測した。これは記載した契約の実証であり、全キャラや全weapon_change flagの認定ではない。Runtime138952byte、入力109528／出力1769472wordと既存容量を維持し、追加容量は0。

## 失敗の保存と修正

最初のMetal実行は96/120一致。24件が整数総計ヘッダーで停止した。従来は親参照damageか通常damageスキルがある場合だけ整数総計bankを初期化しており、今回の武器／回復だけの世界は未初期化だった。保存rawの通常binary64戦闘状態は正本と一致したが、この診断を完全な合格証拠にはしない。

新しいkind2/6/7/8がある場合にも既存の整数総計を有効にするよう修正した。整数演算、damage式、期待値許容と正規化は変更しない。旧89入力に新kindはないため、従来bankのzero／記録状態も保持する。修正前のclaim・raw・比較を保存し、新しいsource/packageで1回だけ実行して120/120一致した。実GPU計2／同claim retry0。

修正版のGPU計算は0.490599秒、初回Metal PSO91.957517秒。生成cache hitでSlang呼出0、PSOは新sourceの初回miss。独立sealとcompiler source証明書の再監査はGPU0。証明書はCUDAコンパイル成功・cache hitを意味しない。旧89入力の入力word・native fingerprint・全629932032byteが同一で、従来12系統のCUDA／MSL生成コードも全byte一致した。独立した4sourceの整数ratio証拠14045入力を保持し、数値GPUは再実行しない。

作成途中のCPU失敗も保存する。手動cover sequenceは既存のpacking経路で拒否され、post-fire delayだけでは正本のcover姿勢にならなかった。遮蔽物回復ケースは実際にcover姿勢になる通常auto reload中の被弾を使用し、正本でも損傷／破損を確認した。手動cover/controlのpackingは未対応分類に残す。

## 共通CLI

`package --suite coordinate-sampled-vital --compact` と `reference --suite coordinate-sampled-vital-common` を登録した。共通CPU正本のreferenceはfull packageで実行し、packing／GPUは禁止する。開発時は `package --develop` → 新規展開 → 必要ならgenerationのみでcache準備 → 通常の `run` → GPU禁止の独立 `seal` と進める。

通常の `run` はCPUテスト・全入力のCPU preflight・容量検査を内部で通し、合格した場合だけGPU claimを取得する。同じ固定packageの `--cpu-only` を先に重ねる必要はない。`--cpu-only` はpacking／正本／テストの切り分けに使い、通常開発ではCPU検査を含む `run` を1回実行する。制御の `--cpu-only --smoke` は別のCPU検査群である。保存出力の監査・転送でGPUを再実行しない。

修正版はCPU63検査・制御421検査（Windows専用1件skip）が成功。最終packageの検査・分類・記録は `research/portable-coordinate-sampled-vital-checkpoint.json`、証拠一覧は `research/coordinate-sampled-vital-v1-evidence/inventory.json` を参照する。保護7source・core probability不変、raw削除0、完了captureの疎化は全byte／SHA／inodeを保持した。Windows新依頼0、現在CUDA／CUDA cacheは未確認。

次はsampled group owner、未検証の武器フラグと操作、回復保存／instantの混合、全キャラ元定義へ進む。全キャラ認定0／20model gap／UI CPU／public GPU closed／full goal falseを維持する。
