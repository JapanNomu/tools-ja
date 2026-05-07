---
name: cognee-queue-flush
description: hook が溜め込んだ Cognee remember キューを定期的に処理する skill。Claude Code の loop / CronCreate スケジューラで起動して、~/.claude/cognee_pending_remembers.jsonl の各エントリを既存の MCP cognee サーバー (mcp__cognee__remember) で 1 件ずつ登録する (新たな cognee-mcp プロセスを spawn しない)。Ladybug DB ロック競合エラー (Could not set lock on file) を回避する。
---

# cognee-queue-flush

`auto_remember_*.py` hook が溜め込んだ Cognee remember キューを 1 件ずつ処理する。

## なぜこの skill が存在するか

2 つの `auto_remember_*.py` hook (UserPromptSubmit / Stop) はキューファイルにエントリを追記する:

- キュー: `~/.claude/cognee_pending_remembers.jsonl`
- 各行: `{"timestamp": "...", "session_id": "...", "dataset_name": "...", "data": "..."}`

hook は **キュー追記のみ** を行う・cognee は呼ばない。hook 内で cognee を呼ぶと、AI のターン開始が遅延するか、新しい cognee-mcp プロセスを spawn して Ladybug DB ロック競合エラー `Could not set lock on file` を引き起こす。よって別途バッチ処理が必要となる。

この skill がそのバッチ処理である。**現在の Claude Code セッション内** で動作する (loop / CronCreate スケジューラで起動) ため、既存の MCP cognee サーバープロセスを共有する — 新たな cognee-mcp を spawn しないので、ロック競合は発生しない。

## いつ起動するか

| 方法 | 説明 |
|---|---|
| `/loop 5m cognee-queue-flush` | 現セッション内で 5 分ごとに繰り返し実行 |
| `CronCreate(...)` | cron 形式で定期実行をスケジュール |
| 手動 `/cognee-queue-flush` | 1 回だけ実行 |

skill は 1 回のキュー処理が終わると終了する。次のスケジュールトリガーで再起動される。

## この skill の動作内容

起動されたら、Claude (あなた) は以下の手順に従う:

### Step 1: キューファイルを読む

`Read` ツールで `~/.claude/cognee_pending_remembers.jsonl` を読む。ファイルが存在しなければキューは空 — 即終了する。

### Step 2: 各行を JSON パース

空でない各行は `data` と `dataset_name` を含む JSON オブジェクト。パースに失敗した行は破損データなのでキューから削除する (再投入し続けるとループするため)。

### Step 3: 1 回の起動で最大 N 件だけ処理する

1 回の起動で処理する上限件数 **N** を決める:

- 環境変数 `COGNEE_QUEUE_FLUSH_MAX_PER_RUN` を読む
- 未設定または正の整数でない場合はデフォルト値 **3** を使う

> **デフォルト値 3 は控えめな初期値です。** 1 回のスケジュール間隔内に何件処理できるかは
> **ユーザー環境** (CPU/GPU・VRAM・選択した LLM・cloud LLM の場合はネットワーク遅延) に
> 完全に依存します。まずはデフォルト値で動かして 1 回の処理時間を観察し
> (skill のサマリで報告されます)、**`COGNEE_QUEUE_FLUSH_MAX_PER_RUN` を自分の環境に合わせて
> 調整してください**。下表はあくまで初期値選びの目安です。

キューの先頭から N 件を取り出す (元の順序を保つ)。N 件を超える残りはキューに残し、次回のスケジュール起動で処理する。この上限を設ける理由は、`mcp__cognee__remember` 1 件あたり数秒〜数十秒かかり (LLM や PC スペックに依存)、1 回の drain がスケジュール間隔 (デフォルト 5 分) を超えると次回の発火と重なるため。

**初期値の目安** (必ず自分の環境に合わせて調整してください):

| 構成 | 推奨 N |
|---|---|
| Cloud LLM (Claude / OpenAI / Gemini) | 10 〜 20 |
| ローカル Ollama・qwen2.5:14b・GPU (VRAM 8GB+) | 3 〜 5 (デフォルト 3) |
| ローカル Ollama・qwen2.5:14b・CPU のみ | 1 〜 2 |
| ローカル Ollama・小型モデル (qwen2.5:7b など) | 5 〜 10 |

先頭の N 件それぞれについて以下を呼ぶ:

`mcp__cognee__remember(data=entry["data"], dataset_name=entry.get("dataset_name", "main_dataset"))`

この呼び出しは **既存の MCP cognee セッション** を使う — 新プロセスを spawn しない。

3 重失敗判定を適用する:

1. **is_error 判定**: 結果に `is_error=True` があれば失敗
2. **Error テキスト判定**: いずれかの `content[*].text` が `"Error:"` で始まれば失敗 (cognee-mcp upstream 欠陥対策: is_error=False のまま失敗を返すケースを捕捉)
3. **例外判定**: 呼び出し中に例外発生で失敗

3 つすべての判定を通過すれば成功。

### Step 4: キューと失敗エントリファイルを更新

Step 3 で処理した N 件について:

- 各 **成功** エントリ: キューから削除する
- 各 **失敗** エントリ: キューに残す + `~/.claude/cognee_failed_remembers.jsonl` にコピー追記 (後で人間がレビューできるように)

先頭 N 件を超える未処理分はキューにそのまま残し、次回起動で処理する。

### Step 5: 書き戻し

- 残るキューエントリ (今回の失敗 + 先頭 N 件を超える未処理分) を元の順序を保ったままキューファイルに書き戻す
- キューが空ならファイル削除または空のまま残す (どちらでもよい)

### Step 6: 結果報告

結果を報告する: `(成功件数, 失敗件数, 残存件数)`。残存件数は Step 5 後にキューファイルに残っている件数 (失敗 + 未処理)。失敗件数 > 0 なら「失敗エントリは `~/.claude/cognee_failed_remembers.jsonl` にレビュー用に保存」と伝える。残存件数 > 0 が上限制御によるものであれば、次回起動で処理されることを伝える。

## 重要な設計制約 (新たな cognee-mcp プロセスを spawn しない)

- **新たな `cognee-mcp` プロセスを spawn してはならない** (`fastmcp.StdioTransport` や `subprocess` 経由含む)。Claude Code セッションには既に cognee-mcp サーバーが起動している。`mcp__cognee__remember` 経由で再利用する。
- **`claude mcp add` で新規 MCP サーバーをインストールしてはならない**。MCP cognee サーバーは既に登録済み。
- **この skill から cognee Python API を直接呼んではならない**。Ladybug DB ロックを取りに行くため、稼働中の cognee-mcp と競合する。

## この skill が **しない** こと

- サンプルデータやユーザーデータの削除
- cognee の設定変更
- `cognify` / `prune` / `improve` の実行 (これらは明示的なユーザー操作)

## 失敗時のリカバリ

`~/.claude/cognee_failed_remembers.jsonl` に失敗エントリが溜まった場合、ユーザーは以下を行う:

1. ファイルを確認する (`cat ~/.claude/cognee_failed_remembers.jsonl`)
2. 根本原因を診断する (Ollama 停止? ディスク枯渇? cognee-mcp クラッシュ?)
3. 解決後、手動でエントリをキューに戻す: `cat ~/.claude/cognee_failed_remembers.jsonl >> ~/.claude/cognee_pending_remembers.jsonl`
4. この skill を再起動する (例: `/cognee-queue-flush`)

## 関連

- hook: `harness/hooks/auto_remember_completion.py`, `harness/hooks/auto_remember_user_message.py` (キュー追記者)
- アーキテクチャ根拠: `CHANGELOG.md` の v0.3.0 エントリを参照
- 検証: この skill は別の CLI スクリプト (例: `src/sample_src/load_sample.py`) が同時に自身の `cognee-mcp` プロセスを spawn しても成功する想定です。spawn する CLI スクリプト側は Ladybug DB ロック競合エラー (`Could not set lock on file`) で失敗しますが、この skill は起動中の Claude Code セッション内で既存の MCP cognee サーバを共有して動作するため影響を受けません。
