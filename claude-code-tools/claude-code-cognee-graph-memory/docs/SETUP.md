# 環境構築手順書

バージョン: 1.0

---

## 1. 前提条件

### 1-1. 動作確認済み環境

| 項目 | 値 |
|------|---|
| OS | Linux（Ubuntu 22.04以降）/ WSL2 |
| Python | 3.12以上 |
| Ollama | 最新版（https://ollama.com） |
| LLMモデル | llama3.1:8b（`ollama pull llama3.1:8b`） |
| Claude Code | 最新版 |

### 1-2. Ollama 起動確認

```bash
ollama serve             # バックグラウンド起動
ollama list              # モデル一覧確認
ollama pull llama3.1:8b  # モデルが未DLの場合
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

---

## 3. 依存パッケージバージョン固定方針

| 方針 | 内容 |
|------|------|
| インストール方法 | `pip install cognee-mcp "cognee[fastembed]"` で最新版を使用 |
| バージョン固定ファイル | `src/requirements.txt`（未作成・将来対応） |
| 動作確認バージョン | Cognee 1.0.3・fastmcp 3.2.4（2026-04-27時点） |
| バージョン固定が必要な場合 | `pip install "cognee-mcp==0.5.4" "cognee[fastembed]==1.0.3"` で固定バージョンを試す |

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
