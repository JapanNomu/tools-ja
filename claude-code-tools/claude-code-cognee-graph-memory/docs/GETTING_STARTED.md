# GETTING_STARTED — Claude Code + Cognee グラフ記憶 動作確認・使い方

このドキュメントでは、セットアップ完了後にグラフ記憶を実際に体験する手順と、自分のノウハウを投入する手順を説明します。

セットアップがまだの場合は先に `docs/SETUP.md` を参照してください。

---

## 推奨LLM・推奨環境

### 推奨LLM（強く推奨）

本システムの全機能（特に `recall` と `search(GRAPH_COMPLETION)`）を **安定して** 利用するには、Cognee の structured output を確実にこなせる **クラウドLLM API** の利用を強く推奨します。

| 種別 | LLM | 推奨度 |
|------|-----|------|
| クラウドAPI（**強く推奨**） | **Anthropic Claude API**（claude-sonnet-4-6 など）/ **OpenAI API**（gpt-4o など） | ★★★ ほぼ100%動作・公式 structured output サポート |
| ローカルLLM（条件付き可） | qwen2.5:14b / qwen2.5:32b / qwen2.5:72b / llama3.3:70b など14B以上 | ★★ GPUに余裕があれば可 |
| ローカルLLM（**非推奨**） | llama3.1:8b / llama3.2:3b / gemma4:e4b など | ★ structured output で JSON Schema 違反多発 |

ローカルLLM運用は API 課金を回避できますが、structured output の信頼性は API より明確に劣ります。本番運用や安定動作を求める場合は API を選んでください。

### 推奨環境

| 項目 | クラウドAPI運用 | ローカルLLM運用 |
|------|---------------|---------------|
| GPU | 不要 | **RTX 4070 12GB 以上**を推奨 |
| RAM | 16GB 以上 | **32GB 以上** |
| LLM | claude-sonnet-4-6 / gpt-4o 等 | **qwen2.5:32b 以上**（14B 以上ならば動作可） |

ローカルLLM運用は **GPU が RTX 4070 12GB 以上** の場合に現実的です。それ未満（例: RTX 4060 8GB）でも 14B クラスの動作は可能ですが、モデル重みが GPU メモリに収まらず一部 CPU offload となるため、**回答速度が顕著に遅くなります**（体感 2〜3 倍）。

### 動作検証実績（参考）

本配布物は以下の環境で全機能の動作を実証しています。

- 検証環境: GPU **RTX 4060 8GB** / RAM 32GB
- 検証LLM: **qwen2.5:14b**（num_ctx=8192）
- 検証結果: **20/20 成功**（remember 5/5 ✅・search(CHUNKS) 5/5 ✅・search(GRAPH_COMPLETION) 5/5 ✅・recall 5/5 ✅・JSON Schema違反 0件）
- 注意点: モデル重み 9GB に対し GPU メモリ 8GB で一部 CPU offload となり、**回答速度は遅め**（gemma4:e4b 16K 比で体感 2〜3 倍遅い）

つまり **RTX 4060 8GB / qwen2.5:14b でもギリギリ全機能を動かせる** ことが実証されていますが、快適な利用のためには上記「推奨環境」を満たすことを推奨します。

### デフォルト設定

本配布物の `config/.env.example` のデフォルトは **qwen2.5:14b**（num_ctx=8192）です。クラウドAPI を利用する場合は `LLM_PROVIDER` / `LLM_MODEL` / `LLM_API_KEY` / `LLM_ENDPOINT` を書き換えてください（詳細は `docs/SETUP.md` 参照）。

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

ローカルLLM運用時は LLM の応答が不安定で構造化出力エラーが発生し、5回リトライしても失敗することがあります（`InstructorRetryException` / `Field required` などのエラー）。失敗した場合は以下の手順で再実行してください。

```bash
# 投入済みのサンプルを削除（中途半端な状態をクリア）
src/venv/bin/python3 src/sample_src/delete_sample.py

# サンプル再投入
src/venv/bin/python3 src/sample_src/load_sample.py
```

それでも失敗が繰り返される場合は、Ollamaが応答できる状態か（`ollama list` でモデルが見えるか）、より上位のローカルLLM（例: `qwen2.5:32b` / `qwen2.5:72b` / `llama3.3:70b`）を `config/.env` の `LLM_MODEL` で試すか、**クラウドAPI（Claude / OpenAI）への切替を検討してください**。クラウドAPI 運用ならばこのエラーはほぼ発生しません。

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

> ⚠️ recall はローカルLLM（特に8B以下のモデル）では「LLMフォーマットエラー」で失敗することがあります。失敗した場合は同じ質問を `search(query, search_type="CHUNKS")` で代替してください（詳細は本ファイル末尾「トラブルシューティング」参照）。クラウドAPI または qwen2.5:14b 以上では recall も安定して動作します。

**期待される回答:**

> 「git pushはユーザーの明示的な指示がある場合のみ実行する。タスク完了・工程完了はpushの理由にならない。」

---

### 体験シナリオ B: 過去のエラーを調べる

```
search("Ollamaに接続できないエラーの対処法", search_type="CHUNKS")
```

**期待される回答:**

> 「`ollama serve` を実行してから再試行する。設定中のローカルLLM（既定: qwen2.5:14b）がDL済みかどうかも `ollama list` で確認する。」

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
→ ローカルLLM（特に8B以下のモデル）が Cognee の期待する JSON 形式で応答しない場合があります。`search(query, search_type="CHUNKS")` を代替として使用するか、より上位のローカルLLM（qwen2.5:14b 以上）または **クラウドAPI（Claude / OpenAI）** への切替を検討してください。

**ノウハウ投入で `status=errored` が出る**
→ ファイルが大きすぎる可能性があります。`split_knowledge.py` で分割してから投入してください。`import_knowledge.py` は失敗時に最大3回リトライします。
