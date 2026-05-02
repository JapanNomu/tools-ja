# HARNESS_GUIDE — Claude Code × Cognee 自動蓄積ハーネス導入ガイド

## 【Claude Code × Cognee ノウハウ蓄積実用ツール】

**RAG は答えだけ。Cognee は経緯ごと。** Claude Code が「なぜそう決めたか」までをグラフ記憶する。
**「また同じこと言わせるな」を、終わらせよう！**

## このハーネスは何か

**Claude Code を使えば使うほど、あなた専用のノウハウが Cognee グラフ記憶に蓄積されていく仕組み** です。

- ユーザーの発言・AI の応答は hook によって自動的にグラフ記憶へ登録される
- 次のセッション以降、AI は作業着手前に必ずグラフ記憶を検索する
- 同じミスを繰り返さず、過去の決定・経緯・関連事実が芋づる式に引き出せる

単なるベクトル検索（RAG）では「該当チャンク」だけが返ります。Cognee はグラフ構造により、その決定の根拠・経緯・関連事実までを連結して返します。「なぜそう決めたか」「いつから」「何が関連するか」までが取り出せる、実用的なノウハウ蓄積ハーネスです。

---

## 仕組みの全体像

```
┌────────────────────────────────────────────────────────┐
│ Claude Code セッション                                  │
│                                                        │
│  ユーザー発言 ─────► UserPromptSubmit hook ────┐       │
│                                                ▼        │
│                                  ~/.claude/             │
│                                  cognee_pending_        │
│                                  remembers.jsonl        │
│                                  （キュー）              │
│                                                ▲        │
│  AI 応答完了 ─────► Stop hook ────────────────┘        │
│                                                         │
│  AI が作業前に                                          │
│  search(CHUNKS) ◄─── CLAUDE.md / rules で必須化         │
└────────────────────────┬───────────────────────────────┘
                         │
                         │ flusher が定期消化
                         ▼
                ┌────────────────────┐
                │ Cognee グラフ記憶   │
                │ （永続）             │
                └────────────────────┘
```

---

## 導入手順（5ステップ）

### 前提

- 配布物本体（`docs/SETUP.md`）のセットアップが完了していること
- `claude mcp list` で `cognee` が登録済みであること
- `src/sample_src/load_sample.py` でサンプル投入が成功していること

### Step 1: ハーネスファイルを ~/.claude/ にコピー

```bash
# 配布物ルートから実行
cp harness/rules/cognee_memory_usage.md ~/.claude/rules/
cp harness/hooks/auto_remember_user_message.py ~/.claude/hooks/
cp harness/hooks/auto_remember_completion.py ~/.claude/hooks/
cp harness/hooks/cognee_remember_flusher.py ~/.claude/hooks/
chmod +x ~/.claude/hooks/auto_remember_user_message.py
chmod +x ~/.claude/hooks/auto_remember_completion.py
chmod +x ~/.claude/hooks/cognee_remember_flusher.py
```

### Step 2: ~/.claude/settings.json をマージ

`harness/settings.example.json` の内容を、既存の `~/.claude/settings.json` に手動でマージしてください。

**特に重要なマージ対象**:
- `hooks.UserPromptSubmit` — ユーザー発言を自動記録
- `hooks.Stop` — AI 応答完了時の要点を自動記録
- `permissions.allow` — Cognee MCP ツール（search / remember 等）の自動許可

既存の hooks や permissions に追記する形でマージし、上書きしないように注意してください。

### Step 3: 各プロジェクトの CLAUDE.md にルールを追記

`harness/CLAUDE_md_sample.md` の内容を、ハーネスを有効化したいプロジェクトの `CLAUDE.md` 末尾に追記してください。

これにより、その AI（Claude Code）は **作業着手前に必ず Cognee グラフ記憶を検索する** ようになります。

### Step 4: flusher の定期実行を設定（cron 推奨）

hook はキューファイルに追記するだけで、実際の Cognee 登録は flusher が行います。

**cron 設定例（5分毎）**:

```bash
crontab -e
# 以下を追記
*/5 * * * * /usr/bin/python3 $HOME/.claude/hooks/cognee_remember_flusher.py >> $HOME/.claude/cognee_flusher.log 2>&1
```

**または常駐モード**:

```bash
nohup python3 ~/.claude/hooks/cognee_remember_flusher.py --daemon --interval 60 &
```

### Step 5: Claude Code を再起動

settings.json と hook を変更したので、既に起動中の Claude Code セッションには反映されません。

- VSCode Claude Code 拡張機能を使っている場合: VSCode を `Reload Window` で再起動
- ターミナル `claude` コマンド: 一度終了して再起動

接続確認:
```bash
claude mcp list
# cognee が ✓ Connected で表示されればOK
```

---

## 動作確認

### ハーネスが効いているかの確認

1. 何らかの発言を Claude Code に送る
2. `cat ~/.claude/cognee_pending_remembers.jsonl` を実行 → 発言が追記されていればOK
3. flusher を手動実行: `python3 ~/.claude/hooks/cognee_remember_flusher.py`
4. ログ確認: `cat ~/.claude/cognee_flusher.log` → `OK: dataset=user_messages` 等が出ていればOK
5. Cognee 側で確認: Claude Code から `search("先ほどの発言の主題語", search_type="CHUNKS")` を呼ぶ → 該当ヒットがあればOK

### AI が search を呼ぶようになったかの確認

ハーネス導入前と導入後で、Claude Code に同じ作業を依頼した際の挙動を比較:

- 導入前: いきなり Edit/Bash を実行する
- 導入後: 最初に `mcp__cognee__search(...)` を呼び、その結果を踏まえて作業に入る

導入後の挙動になっていない場合は、CLAUDE.md への追記が反映されていない可能性があります。

---

## トラブルシューティング

### hook が動かない（キューファイルが更新されない）

- `~/.claude/settings.json` の `hooks.UserPromptSubmit` / `hooks.Stop` の構造が正しいか確認
- Claude Code を再起動したか確認（hook 変更は再起動必須）
- `python3 ~/.claude/hooks/auto_remember_user_message.py < /dev/null` で単独実行できるか確認

### flusher がエラーで失敗する

- `~/.claude/cognee_flusher.log` を確認
- `~/.claude/cognee_failed_remembers.jsonl` に失敗エントリが退避されているので原因調査の参考に
- 配布物ルートのパスが見つからない場合は環境変数 `COGNEE_GRAPH_MEMORY_ROOT` を設定:
  ```bash
  export COGNEE_GRAPH_MEMORY_ROOT=/path/to/claude-code-cognee-graph-memory
  ```

### AI が search を呼んでくれない

- そのプロジェクトの `CLAUDE.md` に `harness/CLAUDE_md_sample.md` の内容が追記されているか確認
- CLAUDE.md は Claude Code が毎ターン読むため、再起動不要だが、新規セッション開始で反映される
- ルールが緩すぎる可能性 → `harness/rules/cognee_memory_usage.md` を `~/.claude/rules/` に配置すると詳細版が AI に効く

### キューが大量に溜まっている

- flusher が動いていない可能性 → cron 設定 or 常駐プロセスを確認
- 1件あたり数秒〜数十秒かかるため、初回起動時は溜まっていることがある
- 手動消化: `python3 ~/.claude/hooks/cognee_remember_flusher.py`

---

## 関連ファイル

| ファイル | 役割 |
|---|---|
| `harness/CLAUDE_md_sample.md` | プロジェクト CLAUDE.md に追記するサンプル |
| `harness/rules/cognee_memory_usage.md` | `~/.claude/rules/` 配置用の詳細ルール |
| `harness/hooks/auto_remember_user_message.py` | UserPromptSubmit hook（発言キュー追記） |
| `harness/hooks/auto_remember_completion.py` | Stop hook（応答キュー追記） |
| `harness/hooks/cognee_remember_flusher.py` | キュー消化スクリプト（cron 推奨） |
| `harness/settings.example.json` | settings.json マージ用サンプル |

---

## このハーネスの効果（運用の積み上げ）

- 1日使用 → 数十件のノウハウが蓄積
- 1週間使用 → 数百件のノウハウが蓄積（過去の指摘・決定が引き出せる）
- 1ヶ月使用 → 数千件のノウハウが蓄積（あなた専用の AI ノウハウベースが完成）

**Claude Code を使えば使うほど、あなた専用の AI が育っていきます。**
