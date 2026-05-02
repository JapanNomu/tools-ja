# よくあるエラーと対処法

## Cognee: SearchPreconditionError

prune直後やデータ未投入の状態でrecall/searchを呼ぶとSearchPreconditionErrorが発生する。先にrememberでデータを登録してからrecall/searchを呼ぶ必要がある。

## Cognee: DatabaseNotCreatedError

prune後にlist_dataを呼ぶとDatabaseNotCreatedErrorが発生する。pruneはDBを完全削除するため、list_dataの前に少なくとも1件rememberを実行してDBを初期化する必要がある。

## Ollama接続エラー

import_to_graph.py実行時に「Ollamaに接続できません」エラーが出る場合、Ollamaが起動していない。`ollama serve` を実行してから再試行する。llama3.1:8bがDL済みかどうかも `ollama list` で確認する。

## recall結果が空になる

recallの結果が空（search_result: ['']）になる場合、グラフ化処理が完了していない可能性がある。rememberはバックグラウンドでグラフ化を実行するため、大量データ投入直後はcognify_statusで完了を確認してからrecallを呼ぶ。

## LLMフォーマットエラー（recall失敗）

recall使用時にLLMのJSON応答フォーマットエラーが発生することがある（llama3.1:8bがCogneeの期待するJSON形式で応答しない場合）。このときはsearch(search_type="CHUNKS")を代替として使用すると、ベクトル検索でテキストを直接取得できる。

## .envのLLM_ENDPOINTに/v1が必要

OllamaをLLMとして使う場合、LLM_ENDPOINTは `http://localhost:11434` ではなく `http://localhost:11434/v1` と設定する。/v1がないとCogneeがOpenAI互換APIエンドポイントを見つけられずエラーになる。
