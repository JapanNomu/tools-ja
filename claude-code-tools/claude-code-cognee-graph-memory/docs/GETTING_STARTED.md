# GETTING_STARTED — Claude Code + Cognee グラフ記憶 動作確認・使い方

このドキュメントでは、セットアップ完了後にグラフ記憶を実際に体験する手順と、自分のノウハウを投入する手順を説明します。

セットアップがまだの場合は先に `docs/SETUP.md` を参照してください。

---

## Step 1: 同梱サンプルで動作確認

ターミナルで以下を実行します。

```bash
cd <クローンしたディレクトリ>
src/venv/bin/python3 src/sample_src/load_sample.py
```

`knowledge/sample_knowledge/` 配下の4ファイルが1件ずつCogneeのグラフ記憶に投入されます。

```
2026-04-29 10:00:00 [INFO] [1/4] 01_claude_code_tips.md → dataset=sample_knowledge
2026-04-29 10:00:30 [INFO] [2/4] 02_software_dev_lessons.md → dataset=sample_knowledge
...
```

所要時間の目安: 2〜5分（Ollamaのグラフ化処理を含む）

### サンプル登録に失敗した場合

LLM（llama3.1:8b）の応答が不安定で構造化出力エラーが発生し、5回リトライしても失敗することがあります（`InstructorRetryException` / `Field required` などのエラー）。失敗した場合は以下の手順で再実行してください。

```bash
# 投入済みのサンプルを削除（中途半端な状態をクリア）
src/venv/bin/python3 src/sample_src/delete_sample.py

# サンプル再投入
src/venv/bin/python3 src/sample_src/load_sample.py
```

それでも失敗が繰り返される場合は、Ollamaが応答できる状態か（`ollama list` でモデルが見えるか）、別のモデル（例: `llama3.1:70b`）を `config/.env` の `LLM_MODEL` で試してください。

---

## Step 2: Claude Codeを起動してMCPツールを呼び出す

新しいClaude Codeセッションを開きます（投入とは別のセッションでOKです）。

チャットに以下を入力して、グラフ記憶からノウハウを引き出してみましょう。

---

### 体験シナリオ A: Claude Code の使い方を聞く

**あなたが入力する質問:**

```
search("git pushのタイミングについて教えて", search_type="CHUNKS")
```

または自然な質問形式で：

```
recall("git pushはいつ実行していいの？")
```

> ⚠️ recall は llama3.1:8b では「LLMフォーマットエラー」で失敗することがあります。失敗した場合は同じ質問を `search(query, search_type="CHUNKS")` で代替してください（詳細は本ファイル末尾「トラブルシューティング」参照）。

**期待される回答:**

> 「git pushはユーザーの明示的な指示がある場合のみ実行する。タスク完了・工程完了はpushの理由にならない。」

---

### 体験シナリオ B: 過去のエラーを調べる

```
search("Ollamaに接続できないエラーの対処法", search_type="CHUNKS")
```

**期待される回答:**

> 「`ollama serve` を実行してから再試行する。llama3.1:8bがDL済みかどうかも `ollama list` で確認する。」

---

### 体験シナリオ C: 設計の根拠を引き出す

```
search("なぜKuzuDBを使っているのか", search_type="CHUNKS")
```

**期待される回答:**

> 「Pythonネイティブ・インプロセス実行・Cogneeに内蔵されており追加インストール不要。ローカル完結・費用ゼロ要件を満たす唯一の選択肢だった。」

---

### 体験シナリオ D: 開発の教訓を聞く

```
search("テストの期待値はどこから導出するか", search_type="CHUNKS")
```

**期待される回答:**

> 「単体テストの期待値はIF仕様書から導出する。実装コードを読んで期待値を決めることは禁止。」

---

## Step 3: 自分のノウハウを登録する（その場で1件）

Claude Codeのチャットで `remember` ツールを呼び出して、自分のプロジェクトで得た知見を登録できます。

```
remember("今日わかったこと: Djangoのmigrate実行前にbackupを取ること。migrate後にrollbackができないテーブル変更があった。", dataset_name="my_lessons")
```

次のセッションで：

```
recall("Djangoのmigrateで気をつけることは？")
```

と聞くと、先ほど登録したノウハウが返ってきます。

> ⚠️ recall が「LLMフォーマットエラー」で失敗した場合は `search("Djangoのmigrate", search_type="CHUNKS")` で代替できます。

---

## Step 4: ユーザー自身のノウハウを大量に投入する

既存のノウハウファイル（.md形式）をまとめて投入したい場合の手順です。

### Step 4-1: サンプルデータを削除（任意）

サンプルが不要になった場合：

```bash
src/venv/bin/python3 src/sample_src/delete_sample.py
```

`sample_knowledge` データセットだけが削除されます。

### Step 4-2: ノウハウを user_knowledge/ に配置

`knowledge/user_knowledge/` 配下に、ノウハウファイル（.md）を配置します。
カテゴリごとにサブフォルダを作ってもOKです。

```
knowledge/user_knowledge/
├── プロジェクト管理/
│   └── タスク管理.md
├── 設計/
│   └── DB設計.md
└── 教訓/
    └── 過去の障害.md
```

### Step 4-3: ノウハウを分割

```bash
src/venv/bin/python3 src/knowledge_src/split_knowledge.py
```

`user_knowledge/` の各 .md がH2見出しごとに分割され、`knowledge/user_chunks/` に出力されます。

### Step 4-4: ノウハウを投入

```bash
src/venv/bin/python3 src/knowledge_src/import_knowledge.py
```

`user_chunks/` の分割ファイルが1件ずつCogneeに投入されます（cognify失敗時はリトライ）。

所要時間: 1ファイルあたり数十秒〜数分。100ファイルなら数十分〜数時間程度。

### Step 4-5: 投入結果を確認

```bash
src/venv/bin/python3 src/knowledge_src/import_knowledge.py --dry-run
```

dry-runで投入対象一覧を事前確認できます。

---

## ツール一覧

| ツール | 用途 | 例 |
|-------|------|---|
| `remember(data, dataset_name)` | ノウハウ・決定・教訓を登録 | `remember("...", dataset_name="lessons")` |
| `recall(query)` | グラフ構造＋LLM要約による意味検索（失敗時は `search` で代替）| `recall("過去の失敗事例は？")` |
| `search(search_query, search_type="CHUNKS")` | ベクトル検索でテキストを直接取得 | `search("エラーの対処法", search_type="CHUNKS")` |
| `list_data()` | 登録済みデータセット一覧を確認 | `list_data()` |
| `prune()` | 全データをリセット | `prune()` |

---

## トラブルシューティング

**「SearchPreconditionError」が出る**
→ データ未投入の状態です。Step 1を先に実施してください。

**「recall結果が空」になる**
→ グラフ化処理中の可能性があります。`cognify_status()` で完了を確認してから再試行してください。

**「LLMフォーマットエラー」でrecallが失敗する**
→ llama3.1:8bがCogneeの期待するJSON形式で応答しない場合があります。`search(query, search_type="CHUNKS")` を代替として使用してください。

**ノウハウ投入で `status=errored` が出る**
→ ファイルが大きすぎる可能性があります。`split_knowledge.py` で分割してから投入してください。`import_knowledge.py` は失敗時に最大3回リトライします。
