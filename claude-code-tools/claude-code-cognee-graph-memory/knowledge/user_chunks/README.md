# user_chunks/

このフォルダは、`user_knowledge/` のファイルを **H2見出しごとに分割した中間ファイル** が出力される場所です。

## 自動生成されるフォルダ

- `src/knowledge_src/split_knowledge.py` を実行すると、ここに分割ファイルが生成されます
- `src/knowledge_src/import_knowledge.py` がここのファイルを Cognee に投入します
- このフォルダのファイルを **手動で編集する必要はありません**（自動生成・自動消去）

## 手動でファイルを置かないでください

`split_knowledge.py` を実行するたびに、このフォルダの内容（README.md以外）はクリアされて再生成されます。
分割元のファイルは `user_knowledge/` に置いてください。

## なぜこのフォルダがあるのか

Cognee の cognify 処理は大きいファイルで失敗することがあるため、投入前に分割が必要です。
分割元（`user_knowledge/`）と投入用（`user_chunks/`）を分けることで、編集と投入の責任を分離しています。
