# vault-refinery

Obsidian Vault内のMarkdownファイルに対して、AI（Claude）を使って日本語・英語のタグを自動付与するPythonスクリプト。

---

## 特徴

- Markdownのfrontmatterにタグを自動追加
- 既存タグがある場合はスキップ
- Claude（Anthropic API）で最大10個ずつ日本語・英語タグを抽出
- ログ出力（logs/ ディレクトリ）
- `.env`でAPIキー管理（サンプルあり）

---

## 使い方

1. 依存パッケージをインストール

   ```sh
   pip install -r requirements.txt
   ```

2. `.env.sample` をコピーして `.env` を作成し、Anthropic APIキーをセット

   ```sh
   cp .env.sample .env
   # .env を編集して ANTHROPIC_API_KEY を自分のキーに書き換え
   ```

3. スクリプトを実行

   ```sh
   python auto_tag_markdown.py
   ```

   デフォルトで `/Users/miyakona/Obsidian Vault/` 配下の全Markdownが対象（パスはスクリプト内で変更可）

---

## .env サンプル

```
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

---

## 依存パッケージ

- keybert
- sudachipy
- scikit-learn
- sentence-transformers
- transformers
- pyyaml
- anthropic
- python-dotenv

---

## 注意

- APIキーは絶対にハードコードしないこと
- `.env`はgit管理外
- ログや`.DS_Store`もgit管理外
- タグなしディレクトリはスキップされる
- 既存タグが「clippings」以外で存在する場合もスキップ

---

## ログ

- `logs/auto_tag_info_*.log` … 正常処理ログ
- `logs/auto_tag_errors_*.log` … エラーログ

---

## 参考

- [Anthropic API](https://docs.anthropic.com/)
- [Obsidian](https://obsidian.md/)

--- 