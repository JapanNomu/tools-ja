# 環境構築手順書

---

## 1. 前提条件

### 1-1. 動作確認済み環境

| 項目 | 値 |
|------|---|
| OS | Linux（Ubuntu 22.04以降）/ WSL2 |
| Python | 3.12以上 |
| Ollama | 最新版（https://ollama.com） |
| LLMモデル | qwen2.5:14b（`ollama pull qwen2.5:14b`） |
| Claude Code | 最新版 |

### 1-2. Ollama 起動確認

```bash
ollama serve             # バックグラウンド起動
ollama list              # モデル一覧確認
ollama pull qwen2.5:14b  # モデルが未DLの場合
```

---

## 2. 環境構築手順

### 2-1. 手順概要

| ステップ | 内容 | 所要時間目安 |
|---------|------|------------|
| 1 | リポジトリクローン | 1分 |
| 2 | .env 作成・パス設定 | 2分 |
| 3 | venv 構築・pip install | 5〜15分（FastEmbedモデルDL含む） |
| 4 | 起動スクリプトへの実行権限付与 | 1分 |
| 5 | Claude Code への MCP 登録 | 1分 |

### 2-2. 手順詳細

**ステップ1: リポジトリクローン**
```bash
git clone https://github.com/JapanNomu/tools.git
cd tools/claude-code-tools/claude-code-cognee-graph-memory
```

**ステップ2: .env 作成・パス設定**

```bash
cp config/.env.example config/.env
```

`config/.env` を開き、以下の2項目を自環境の絶対パスに変更します。

**(1) 絶対パスの取得方法**

クローンしたフォルダ内で `pwd` を実行すると、絶対パスが表示されます。

```bash
pwd
# 例の出力: /home/yourname/tools/claude-code-tools/claude-code-cognee-graph-memory
```

**(2) `config/.env` で設定する項目**

`pwd` で取得した絶対パスを使って、以下のように書き換えます。

| 設定項目 | 設定値の例 |
|---------|-----------|
| `SYSTEM_ROOT_DIRECTORY` | `<pwdの結果>/data/cognee/system` |
| `DATA_ROOT_DIRECTORY` | `<pwdの結果>/data/cognee/data` |

例えば `pwd` の結果が `/home/yourname/tools/claude-code-tools/claude-code-cognee-graph-memory` だった場合：

```bash
SYSTEM_ROOT_DIRECTORY=/home/yourname/tools/claude-code-tools/claude-code-cognee-graph-memory/data/cognee/system
DATA_ROOT_DIRECTORY=/home/yourname/tools/claude-code-tools/claude-code-cognee-graph-memory/data/cognee/data
```

**(3) 注意事項**

- 相対パス（`./data/cognee/...` など）は使えません。**必ず絶対パス（`/` から始まる）** で指定してください
- `data/cognee/system` `data/cognee/data` のフォルダは自動作成されます（手動で作る必要はありません）
- `COGNEE_DATA_PATH` は基本的にデフォルト値（`./data/cognee`）のままでOKです（必要に応じて変更）

**ステップ3: venv 構築**
```bash
cd src
python3 -m venv venv
source venv/bin/activate
pip install cognee-mcp "cognee[fastembed]"
deactivate
cd ..
```

**ステップ4: 実行権限付与**
```bash
chmod +x src/main_src/start_cognee_mcp.py
```

**ステップ5: MCP 登録**

クローンした場所の**絶対パス**で登録する。ステップ2で実行した `pwd` の出力値をそのまま使う。

例えば `pwd` の出力が `/home/yourname/tools/claude-code-tools/claude-code-cognee-graph-memory` の場合:

```bash
claude mcp add cognee --scope user /home/yourname/tools/claude-code-tools/claude-code-cognee-graph-memory/src/main_src/start_cognee_mcp.py
claude mcp list  # cognee が ✓ Connected で表示されれば完了
```

上記の絶対パスは **自分の環境のパスに置き換える**（ステップ2の `pwd` 出力値 + `/src/main_src/start_cognee_mcp.py`）。

> **絶対パスが必須な理由:** `--scope user` は全プロジェクト共通のグローバル登録。相対パス（`src/main_src/start_cognee_mcp.py` 等）で登録すると、`claude` 起動時のカレントディレクトリ基準で解決されるため、クローン先以外のディレクトリで `claude` を起動した瞬間に接続失敗する。

### 2-3. 動作確認

**重要: Claude Code を既に起動している場合は再起動が必要**

`claude mcp add` で登録した設定は、**既に起動しているClaude Codeセッションには自動的に反映されません**。以下の方法でセッションを再起動してください。

| 環境 | 再起動方法 |
|---|---|
| VSCode拡張 | コマンドパレット（`Ctrl+Shift+P`）→ `Developer: Reload Window` |
| ターミナルの `claude` コマンド | セッション終了（`Ctrl+D` または `/exit`）→ 再度 `claude` を起動 |

**接続確認の3つの方法**

- ターミナル: `claude mcp list` で `cognee: ✓ Connected` が表示されることを確認
- VSCode: Claude Codeパネルの「MCP servers」画面で `cognee: ✓ Connected` が表示されることを確認
- セッション内: `/mcp` を実行して `cognee: connected` が表示されることを確認

### 2-4. キュー処理バッチを定期起動する設定 (v0.3.0)

hook (`auto_remember_user_message.py` / `auto_remember_completion.py`) はキューファイル (`~/.claude/cognee_pending_remembers.jsonl`) への追記のみを行う。キューを実際に Cognee グラフ記憶に永続化するには、`cognee-queue-flush` skill を Claude Code セッション内で定期実行する必要がある。

**アーキテクチャ根拠**: この skill は同じ Claude Code プロセス内 ("live in the current process") で動作し、既存の MCP cognee サーバーを再利用する。新たな cognee-mcp プロセスを spawn しない。これにより BUG-008 (Ladybug DB ロック競合) を回避する。

**初期設定**: Claude Code 内で skill を定期スケジュールに登録する。以下のいずれかを選択:

| 方法 | コマンド | ライフタイム |
|---|---|---|
| `/loop` (対話的) | `/loop 5m cognee-queue-flush` | **セッション内のみ** — Claude Code 終了で消える |
| `CronCreate` (セッション内) | Claude Code 内で `CronCreate(cron="*/5 * * * *", prompt="cognee-queue-flush", recurring=true)` | **セッション内のみ** — Claude Code 終了で消える |
| `CronCreate(durable=true)` (永続) | Claude Code 内で `CronCreate(cron="*/5 * * * *", prompt="cognee-queue-flush", recurring=true, durable=true)` | **永続** — `~/.claude/scheduled_tasks.json` に保存・次回起動時に自動復元 |

推奨頻度は **5 分ごと**。必要に応じて調整。

**永続化の補足**: `/loop` および `CronCreate(durable=false)` の登録は 1 つの Claude Code セッション内でのみ有効です。Claude Code を再起動するたびに再登録が必要になります。再起動後も維持したい場合は `CronCreate(durable=true)` を使ってください。

**`/loop` は永続化できません** — スラッシュコマンドには `durable` オプションがなく、`durable=true` 形式は `CronCreate` Tool でしか実行できません。Tool は **Claude Code (AI) が呼ぶもので、ユーザーが直接タイプするものではありません**。永続化したい場合は、Claude Code のチャットで一度だけ AI に依頼してください:

> `CronCreate` を `cron="*/5 * * * *"`、`prompt="cognee-queue-flush"`、`recurring=true`、`durable=true` で呼んでください。再起動後もキューの drain が続くように。

AI が Tool を 1 回呼べば登録は保存され、以降は依頼不要です。

詳細 (1 回の起動で処理する件数チューニング `COGNEE_QUEUE_FLUSH_MAX_PER_RUN`、永続化のトレードオフなど) は `docs/HARNESS_GUIDE.md` Step 4 を参照。

**動作確認**: 設定後、Claude Code にメッセージを送信し、5 分待ってから Claude Code 内で `mcp__cognee__search(search_query="<最近の文章>", search_type="CHUNKS")` を実行する。最近の文章が取得できれば成功。

### 2-5. CLI ツール使用制約 (v0.3.0)

以下の CLI ツールは新たな `cognee-mcp` プロセスを spawn するため、**Claude Code を起動している間は実行してはならない** (BUG-008 ロック競合を引き起こす):

- `src/sample_src/load_sample.py` (同梱サンプル投入)
- `src/sample_src/delete_sample.py` (サンプルデータセット削除)
- `src/knowledge_src/import_knowledge.py` (自分のノウハウファイルの投入)

**使用ルール**: これらのツールは **Claude Code を起動する前に実行する**、または Claude Code 終了後に実行する。

**削除の代替手段**: Claude Code が起動中にデータセットを削除したい場合は、CLI スクリプトの代わりに Claude Code 内から `mcp__cognee__delete_dataset` を呼び出す。

---

## 3. 依存パッケージバージョン固定方針

| 方針 | 内容 |
|------|------|
| インストール方法 | `pip install cognee-mcp "cognee[fastembed]"` で最新版を使用 |
| バージョン固定ファイル | `src/requirements.txt`（未作成・将来対応） |
| 動作確認バージョン | Cognee 1.0.8・cognee-mcp 0.5.4・ladybug (cognee 1.0.8 同梱バージョン)・BATCH テスト全 21 件 PASSED (2026-05-07 時点・v0.3.0) |
| バージョン固定が必要な場合 | `pip install "cognee-mcp==0.5.4" "cognee[fastembed]==1.0.8"` で固定バージョンを試す |
| Ollama 利用時の必須設定 | cognee 1.0.7/1.0.8 で test_llm_connection が `/v1` なし URL を叩いて 404 になるリグレッションあり。`config/.env` に `LLM_ENDPOINT=http://localhost:11434/v1` (`/v1` 必須) と `COGNEE_SKIP_CONNECTION_TEST=true` を設定する。`.env.example` に既定値あり |

---

## 4. 移植時変更箇所

| 変更対象 | 変更内容 | 必須/任意 |
|---------|---------|---------|
| `config/.env` の `SYSTEM_ROOT_DIRECTORY` | 自環境の絶対パスに変更 | **必須** |
| `config/.env` の `DATA_ROOT_DIRECTORY` | 自環境の絶対パスに変更 | **必須** |
| `config/.env` の `COGNEE_DATA_PATH` | デフォルト値（`./data/cognee`）のまま使用可能（必要に応じて変更） | 任意 |
| `config/.env` の `LLM_MODEL` | 別のOllamaモデルを使う場合に変更 | 任意 |
| `config/.env` の `LLM_ENDPOINT` | Ollamaが別ホストの場合に変更 | 任意 |
| `config/.env` の `EMBEDDING_MODEL` / `EMBEDDING_DIMENSIONS` | 別埋め込みモデルを使う場合に変更 | 任意 |

**変更不要:** `src/main_src/start_cognee_mcp.py`（`Path(__file__)` でプロジェクトルートを自動解決）
