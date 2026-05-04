# Cognee グラフ記憶の利用ルール（絶対ルール）

このファイルは `~/.claude/rules/` 配下に配置することで、すべてのプロジェクトで共通的に適用される。

## 1. 検索順序（絶対ルール・例外なし）

作業着手前は必ず以下の順序で関連知識を調べる。

```
1. Cognee グラフ記憶: mcp__cognee__search(query, search_type="CHUNKS")
   ↓ 該当なし
2. ~/.claude/skills/ 配下の関連 reference.md を Read
   ↓ 該当なし
3. ユーザーに確認
```

## 2. 適用対象（必ず検索する場面）

以下のいずれかに該当する応答の前は、検索をスキップしてはならない。

- ファイルの編集・作成・削除（Edit/Write/NotebookEdit）
- コマンド実行（Bash）
- 設計判断・方針決定の発言
- 障害対処・問題解決の方針提示
- ユーザーへの提案・選択肢提示

## 3. 適用対象外（検索不要）

- 単純な Yes / No 回答
- ユーザーの質問の意図確認
- エコー応答（ユーザーが言ったことの繰り返し確認）

## 4. Why（なぜこの順序で必ず検索するのか）

### Cognee を最優先する理由

- Cognee は **このユーザー固有の最新の経験・教訓・決定事項** が蓄積された記憶
- skills は汎用・静的・全プロジェクト共通のノウハウ
- 「具体的・新しい・このユーザー固有」の知識を優先することで、過去のミスの繰り返しを防ぐ
- skills は「Cognee に該当がない」ときの補完として読む

### 「例外なし」にする理由

- 「明らかに知っている」と思った内容ほど、過去に同じミスをしている可能性が高い
- スキップ判断自体がミスの温床
- 検索コストは数秒、ミスのリカバリコストは数時間〜数日
- 「気をつける」では守れない。物理的に毎回検索する運用で防ぐ

### 「作業前」と限定する理由

- 全応答前に検索すると過剰（雑談や意図確認まで巻き込まれる）
- 一方、ファイル編集・コマンド実行・方針判断は **取り返しがつかない** 可能性がある作業
- 取り返しがつかない作業の前だけは、絶対に検索を挟む

## 5. 検索クエリの作り方

### 基本

ユーザーの指示・質問の主題語を1〜3個取り出してそのまま投げる。

| ユーザーの指示 | 検索クエリの例 |
|---|---|
| 「Django のマイグレーションで気をつけることは？」 | `search("Django migrate 注意", search_type="CHUNKS")` |
| 「このテストが失敗してるんだけど」 | `search("テスト 失敗 原因", search_type="CHUNKS")` |
| 「git push していい？」 | `search("git push タイミング", search_type="CHUNKS")` |

### バリエーション

- 1回目: 主題語だけ（例: `Django migrate`）
- 2回目: ユーザーの言い回しそのまま（例: `Django のマイグレーションで気をつけることは`）
- 3回目: 関連語を加える（例: `Django migrate ロールバック バックアップ`）

3回試して該当がなければ skills へ進む。

### エラー対処時のクエリ

エラー文字列（メッセージの主要部分）をそのまま投げる。

```
search("LLMAPIKeyNotSetError Status 422", search_type="CHUNKS")
search("ModuleNotFoundError pydantic", search_type="CHUNKS")
```

## 6. 記録は hook が自動で行う（AI は能動的に呼ばなくてもよい）

ユーザーの発言・AI の応答要点は `harness/hooks/` の hook によって自動的に
`mcp__cognee__remember` で Cognee に登録される。

- AI が能動的に `remember` を呼ぶ必要はない（呼んでもよい。重複は許容する）
- AI が「これは重要だから記録したい」と判断したときは能動的に `remember` を呼んでもよい
- データセット名は用途に応じて使い分ける:
  - `feedback` — ユーザーからの指摘・フィードバック
  - `incidents` — 障害・不正行為・エラー対処
  - `decisions` — 設計決定・方針決定
  - `lessons` — プロジェクトを通じた教訓
  - 指定しない場合は `main_dataset`（既定値）

## 7. recall は使わず search(CHUNKS) を使う

`mcp__cognee__recall` は qwen2.5:14b 以外のローカルLLM では LLM フォーマットエラーで失敗することがある。
配布物の動作確認では search(CHUNKS) を使うことが推奨されている。

- 検索は基本的に `search(query, search_type="CHUNKS")` を使う
- recall を使いたい場面でも、まず search(CHUNKS) を試す

## 8. 実証経緯（このルールが生まれた背景）

- 2026-05-02 ユーザー指示「Cognee 優先で、なかったら skills」
- 同日 ユーザー指示「作業前に必ず調べることね」
- 同日 ユーザー指示「対象外のパターンはそれでいいよ。それ以外は調べる」
- 同日 ユーザー指示「MEMORY があるならそれ最優先なんじゃないの？」
  → 配布物利用者は MEMORY 機能を使っているとは限らないため、
    配布物のルールでは「Cognee → skills → ユーザー」の3段階とする
    （MEMORY 機能を使っている利用者は、自分の CLAUDE.md で
    「MEMORY → Cognee → skills → ユーザー」の4段階に拡張すればよい）

## 9. 共同納得の記録

- AI（Claude Code）: 当初「重要なものだけ Cognee に登録」と提案
- ユーザー: 「グラフ記憶肥大化しても必要な検索すれば抽出できるだろ？そのためのグラフ記憶なんだけど」
- AI: 認識修正「全部入れるのが正しい運用」
- 両者合意: **記録は迷ったら入れる・検索は作業前に必ず行う**

---

## 関連ファイル

- `harness/CLAUDE_md_sample.md` — 各プロジェクトの CLAUDE.md に追記するサンプル
- `harness/hooks/auto_remember_user_message.py` — UserPromptSubmit hook
- `harness/hooks/auto_remember_completion.py` — Stop hook
- `harness/settings.example.json` — hook 登録の設定例
- `docs/HARNESS_GUIDE.md` — 全体導入手順
