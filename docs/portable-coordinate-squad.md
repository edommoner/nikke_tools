# スクワッド操作の共通実行器

`coordinate-squad` は `coordinate-policy`196入力に全体遮蔽・focus合成18worldとwire拒否8入力を加えるM5 Metal照合・独立seal済みのprivate入口。CPUで生成した操作時刻表やrecipient maskを入力せず、authoredの`t`／`focus`／`cover_all`／`duration`のみを渡す。全キャラ認定・公開GPU受付と区別する。

CPU正本の `_pump_squad_seq` はburst tickの後、カメラ調停の前に実行する。同じ時刻の操作は元リストの順序を保持して安定ソートする。`cover_all`はforced focus、なければその時点の旧ctrl_ownerを除き全員へ進入を要求する。静的cameraは除外対象の代わりにはならない。`focus`を同じtickで解除しても、まだ再調停前なので旧ctrl_ownerが除外対象になる。武器変更中・有効な武器変更effectがある対象と、cover_disabled中の対象を除く。

全体遮蔽の姿勢はカメラ維持要求を作らない。通常のsequence／policyが後から個別coverへ入った場合は、その姿勢の由来を上書きする。進入は既存 `enterManualCover`、終了・部分装填取消・充填可視状態・被弾は同じ本体を使う。スクワッド処理はchar tickの前に発生するため、個別sequenceと異なり、そのtickを消費するentryフラグは残さない。CPU正本が最後に数値cacheを無効化する順序も維持する。

追加入力136wordはheader8＋16行×8word。入力総数109792word。行は`t`binary64／kind／target／duration binary64／予約2wordで、focus=1、cover_all=2、None duration=-1のwire表現。durationの負数literalは受け付けない。操作recipientはwireに存在しない。旧196には固定の空headerを付加する。

出力総数1769856word・Runtime138952byteは維持し、前の方針出力の48word paddingを明示的にスクワッド状態へ割り当てる。先頭1769808wordからmagic/version/sequence index/count/last keep、予約3word、5人のcover_all由来フラグ、予約35word。空sequenceなら全bankをゼロにし、旧出力を保持する。比較器はこの48wordを方針比較から取り出した後、全フィールド・全予約wordを独立に照合する。カメラ・aim・全戦闘・RNGの既存比較を残す。

CPU観測器は既存simulate内の実 `_pump_squad_seq` の戻りだけを読み、追加の所有権照会や操作を発生させない。原リスト順・focus解除時の旧所有者・カメラ要求なしをpositive witnessで確認する。

```sh
python scripts/nikke_gpu.py package --suite coordinate-squad --compact --out /tmp/UNIQUE.zip
python scripts/nikke_gpu.py unpack --archive /tmp/UNIQUE.zip --dest /tmp/UNIQUE
```

展開先をcwdにCPU事前検査、固定packageから生成、実GPU、保存結果の独立監査を順に進める。新しい変更へ過去のMetal一致・旧196保持を自動適用せず、CUDA一致も別途検証する。強制burst操作は別の残件で、正本のburst controllerには`delay`・`wait_own_cooldown`・patternと次FB予測への反映が必要。これをcoverのカメラsequenceへ誤って割り当てない。

初回222入力のMetal dispatchはM5で約0.661秒、初回pipeline約92.311秒で終了。旧比較器へ方針＋squad合成を再packした1件がhost decodeで拒否され、他221入力は一致した。元capture `/tmp/nikke-squad-metal-v1` を保持し、比較器だけを共通policy-state照合へ切り出した。問題の保存rawをfresh nativeで照合し元のnative SHAを保持できたため、共通CLI replayでGPU再実行0の全入力監査へ進める。この失敗後は開発用入口を維持し、修正版の独立seal成功後に通常入口へ切り替えた。

追加のCPU観測で、武器変更が満了する同じtickのsquad操作は、そのキャラがまだ `_in_weapon_change=True` のため除外されることを確認した（duration=.3／squad t=.3）。後のt=.5操作では除外されない。この境界は現在の18worldに含めておらず、次の優先検証とする。logical mode indexだけをphysical CharStateの移行状態と同一視しない。

最終的に修正版immutable packageのCPU-only replayで222入力が全件一致し、さらにGPU禁止の別processで独立sealした。旧196入力の全1,387,567,104byte／input prefix・空拡張／native SHAは一致。初回host decode失敗・storage事前停止を保持し、実GPUは計1回、再実行0。通常CLIはsealed入口として登録。新profile専用compiler-source証明書・CUDA実機・全キャラの認定は未完了。復旧点は `research/portable-coordinate-squad-checkpoint.json`。
