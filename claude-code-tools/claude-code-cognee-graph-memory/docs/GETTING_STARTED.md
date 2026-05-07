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
| ローカルLLM（**非推奨**） | qwen2.5:14b 未満のモデル（llama3.1:8b / llama3.2:3b / gemma4:e4b など） | ★ structured output で JSON Schema 違反多発 |

ローカルLLM運用は API 課金を回避できますが、structured output の信頼性は API より明確に劣ります。本番運用や安定動作を求める場合は API を選んでください。

### 推奨環境

| 項目 | クラウドAPI運用 | ローカルLLM運用 |
|------|---------------|---------------|
| GPU | 不要 | **VRAM 12GB 以上の GPU** を推奨（※ノートPC版 RTX 4070 は VRAM 8GB なので不可。RTX 4070 デスクトップ版 / 4070 SUPER / 4070 Ti / 4080 等が該当） |
| RAM | 16GB 以上 | **32GB 以上** |
| LLM | claude-sonnet-4-6 / gpt-4o 等 | **qwen2.5:32b 以上**（14B 以上ならば動作可） |

ローカルLLM運用は **VRAM 12GB 以上の GPU** の場合に現実的です。VRAM がそれ未満（例: NVIDIA GeForce RTX 4060 Laptop GPU・VRAM 8GB）でも 14B クラスの動作は可能ですが、モデル重みが GPU メモリに収まらず一部 CPU offload となります。

### 動作検証実績（参考）

本配布物は以下の環境で全機能の動作を実証しています。

- 検証環境: GPU **NVIDIA GeForce RTX 4060 Laptop GPU（VRAM 8GB）** / RAM 32GB
- 検証LLM: **qwen2.5:14b**（num_ctx=8192）
- 検証Cogneeバージョン: **1.0.8 (Ladybug DB・v0.3.0 で 1.0.5 から更新)**
- 検証結果: **35/40 成功** (v0.2.0 リリース時の cognee 1.0.5 環境での実測値) (remember 5/5 ✅・search(CHUNKS) 5/5 ✅・search(GRAPH_COMPLETION) 5/5 ✅・recall 5/5 ✅・cognify 5/5 ✅・improve 5/5 ✅・forget_memory 5/5 ✅・**save_interaction 0/5 ❌** = 既知の制限事項・後述)。v0.3.0 では cognee 1.0.8 ベースで新アーキテクチャ用 BATCH 系テスト 21 件 (UT 12 + IT 4 + ET 3 + ST 2・Claude Code 内 skill によるキュー drain を検証) を全件 PASSED で実証済
- 応答時間（Ladybug DB環境下の実測値）:
  - search(CHUNKS): 平均 3.2秒（決定論的・LLM不使用）
  - search(GRAPH_COMPLETION): 平均 14.6秒（範囲 12〜18秒）
  - recall（Q-A・TEMPORAL routing）: 20〜24秒
  - recall（Q-B・GRAPH_COMPLETION_COT routing）: 154〜156秒（Chain-of-Thought推論）
  - improve / forget_memory: 全件即時（数秒以下）

**Ladybug DB（Cognee 1.0.4で導入）により graph traversal が高速化**し、qwen2.5:14b でも GRAPH_COMPLETION・recall が実用レベルの速度で動作することが実証されました（v0.1.x の KuzuDB 環境より体感大幅改善）。

つまり **VRAM 8GB のノートPC GPU（RTX 4060 Laptop GPU）+ qwen2.5:14b + Ladybug DB** で全主要機能を実用速度で動かせることが実証されています。

### デフォルト設定

本配布物の `config/.env.example` のデフォルトは **qwen2.5:14b**（num_ctx=8192）です。クラウドAPI を利用する場合は `LLM_PROVIDER` / `LLM_MODEL` / `LLM_API_KEY` / `LLM_ENDPOINT` を書き換えてください（詳細は `docs/SETUP.md` 参照）。

---

## Step 1: 同梱サンプルで動作確認

> ⚠️ **重要 (v0.3.0)**: `load_sample.py` は新たな `cognee-mcp` プロセスを spawn する。**Claude Code を起動していない状態で実行する** (起動中だと BUG-008 ロック競合を引き起こす)。Step 1 完了後、Step 2 で Claude Code を起動できる。

ターミナルで以下を実行します。

```bash
cd <クローンしたディレクトリ>
src/venv/bin/python3 src/sample_src/load_sample.py
```

`knowledge/sample_knowledge/` 配下の5ファイルが1件ずつCogneeのグラフ記憶に投入されます。

```
2026-04-29 10:00:00 [INFO] [1/5] 01_claude_code_tips.md → dataset=sample_knowledge
2026-04-29 10:00:30 [INFO] [2/5] 02_software_dev_lessons.md → dataset=sample_knowledge
...
```

所要時間の目安: 2〜5分（Ollamaのグラフ化処理を含む）

### サンプル登録に失敗した場合

ローカルLLM運用時は LLM の応答が不安定で構造化出力エラーが発生し、5回リトライしても失敗することがあります（`InstructorRetryException` / `Field required` などのエラー）。失敗した場合は以下の手順で再実行してください。

> ⚠️ **重要 (v0.3.0)**: `delete_sample.py` と `load_sample.py` は新たな `cognee-mcp` プロセスを spawn する。**Claude Code を起動していない状態で実行する** (BUG-008 ロック競合を回避するため)。Claude Code が起動中なら一旦終了してから実行し、後で再起動する。

```bash
# Claude Code を終了済みであることを確認 (claude プロセスが残っていない)

# 投入済みのサンプルを削除（中途半端な状態をクリア）
src/venv/bin/python3 src/sample_src/delete_sample.py

# サンプル再投入
src/venv/bin/python3 src/sample_src/load_sample.py

# ここから Claude Code を起動できる
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

サンプルが不要になった場合、以下の **どちらか** の方法を選びます:

**方法 A (推奨): Claude Code 内から MCP ツール経由で削除** (Claude Code 起動中で OK)

Claude Code 内で以下のように依頼します:

```
sample_knowledge データセットを削除してください
```

Claude が `mcp__cognee__delete_dataset(dataset_name="sample_knowledge")` を呼び出します。既存の MCP cognee サーバーを使う (新プロセス spawn なし) ため、Claude Code 起動中でも安全に実行できます。

**方法 B: CLI スクリプトで削除** (Claude Code を終了する必要がある)

> ⚠️ **重要 (v0.3.0)**: `delete_sample.py` は新たな `cognee-mcp` プロセスを spawn する。**Claude Code を先に終了する** こと、さもなければ BUG-008 ロック競合を引き起こす。

```bash
# Claude Code を終了済みであることを確認 (claude プロセスが残っていない)
src/venv/bin/python3 src/sample_src/delete_sample.py

# ここから Claude Code を再起動できる
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

> ⚠️ **重要 (v0.3.0)**: `import_knowledge.py` は新たな `cognee-mcp` プロセスを spawn する。**Claude Code を先に終了する** こと、さもなければ BUG-008 ロック競合を引き起こす。スクリプト実行は Claude Code 終了中に行い、完了後に再起動する。

```bash
# Claude Code を終了済みであることを確認 (claude プロセスが残っていない)
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

**`save_interaction` が `add_rule_associations() got an unexpected keyword argument 'context'` で失敗する**
→ **v0.2.0 既知の制限事項**です。cognee-mcp 0.5.4 と cognee 1.0.5 のAPI不整合（cognee 1.0.5 で `add_rule_associations` の引数が `context` → `ctx` にリネームされたが cognee-mcp が未追従）。
代替案として `remember(data="User: 質問\nAssistant: 回答")` を使用してください。永続記憶への即時保存ができます。

**「SearchPreconditionError」が出る**
→ データ未投入の状態です。Step 1を先に実施してください。

**「recall結果が空」になる**
→ グラフ化処理中の可能性があります。`cognify_status()` で完了を確認してから再試行してください。

**「LLMフォーマットエラー」でrecallが失敗する**
→ ローカルLLM（特に8B以下のモデル）が Cognee の期待する JSON 形式で応答しない場合があります。`search(query, search_type="CHUNKS")` を代替として使用するか、より上位のローカルLLM（qwen2.5:14b 以上）または **クラウドAPI（Claude / OpenAI）** への切替を検討してください。

**ノウハウ投入で `status=errored` が出る**
→ ファイルが大きすぎる可能性があります。`split_knowledge.py` で分割してから投入してください。`import_knowledge.py` は失敗時に最大3回リトライします。

---

## 付録: v0.1.x（Cognee 1.0.3 / KuzuDB 環境）ローカルLLM比較データ（参考）

> 本セクションは v0.1.x（KuzuDB環境）でのローカルLLM比較検証データの参考記録です。v0.2.0 では Ladybug DB に置換され、qwen2.5:14b のみが動作確認対象になっています（本ファイル上部の「動作検証実績」参照）。LLM選定の参考としてください。

### 検証環境（v0.1.x）

- Cognee 1.0.3 / KuzuDB 0.11.3
- GPU: NVIDIA GeForce RTX 4060 Laptop GPU（VRAM 8GB）/ RAM 32GB
- 検証日: 2026-05-02
- 検証回数: 各LLM × 4ツール × 5回 = 20回

### LLM × ツール 結果サマリ

| LLM（num_ctx） | remember×5 | search(CHUNKS)×5 | search(GRAPH_COMPLETION)×5 | recall×5 | 合計 |
|---|---|---|---|---|---|
| llama3.1:8b（2048・初回） | 5/5 ✅ | 5/5 ✅ | 4/5 ⚠️（#1で JSON Schema 違反） | 1/5 ✅ + 2/5 ⚠️ + 2/5 ❌（Q-B 2/2 全敗） | 14/20 |
| llama3.1:8b（65536・再実証） | 5/5 ✅ | 5/5 ✅ | 2/5 ✅ + 3/5 ❌（pydantic ValidationError） | 2/5 ✅ + 3/5 ❌（Q-B 2/2 全敗継続） | 14/20 |
| llama3.2:3b（2048デフォルト） | 0/5 ❌ Timeout | （未実施） | （未実施） | （未実施） | 0/20 |
| gemma4:e4b（16384） | 5/5 ✅ | 5/5 ✅ | **5/5 ✅** | 3/5 ✅ + 2/5 ❌（Q-B 2/2 JSON Schema 違反） | 18/20 |
| **qwen2.5:14b（8192）** | **5/5 ✅** | **5/5 ✅** | **5/5 ✅** | **5/5 ✅**（Q-A/Q-B 全件正答） | **20/20** |
| claude-sonnet-4-6 | 未実施（API課金回避のため） | - | - | - | - |

### 主な観察事項（v0.1.x）

- **qwen2.5:14b（num_ctx=8192）が唯一の全勝**（20/20）。recall Q-B（理由・経緯を含む推論）でも完答できた唯一のローカルLLM
- **llama3.1:8b** は num_ctx を増やしても改善せず、recall Q-B では2/2全敗
- **llama3.2:3b** は接続テスト時点で Timeout（軽量モデルすぎてエンティティ抽出が完了しない）
- **gemma4:e4b** は GRAPH_COMPLETION で全勝するも recall Q-B で JSON Schema 違反
- 配布物デフォルトを **qwen2.5:14b** にしている根拠データ

### 検証クエリ（v0.1.x）

- Q-A: `When can I run git push?`（単純事実検索）
- Q-B: `Why is KuzuDB used in this project?`（理由・経緯を含む推論）

### num_ctx 設定の根拠

| モデル | num_ctx | 根拠 |
|---|---|---|
| llama3.1:8b | 65536 | 8B モデル重み4.7GB＋KV cache（FP16・64K）約4.0GB＝合計8.7GB。8GB GPU で一部オフロードあるが大半 GPU 動作 |
| qwen2.5:14b | 8192 | モデル重み9GBで既にCPU offload状態。num_ctx を上げると速度更に低下するため8K上限に抑制 |
| gemma4:e4b | 16384 | モデル重み5GB＋KV cache 1GB=合計6GBで完全GPU動作可能 |

### v0.2.0 でのスコープ

v0.2.0 では Cognee 1.0.5 / Ladybug DB に対応した上で **qwen2.5:14b のみ**を全機能（8ツール）で再検証しました（35/40 ✅・本ファイル上部の「動作検証実績」参照）。他LLM の v0.2.0/Ladybug DB 環境での再検証は将来の拡張余地として残しています。
