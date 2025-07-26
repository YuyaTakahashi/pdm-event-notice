# Connpass PdMイベント通知Bot

PdM関連のconnpassイベントを自動で取得し、Slackに画像付きで通知するPythonスクリプトです。

## 主な機能
- connpassの検索URLを自動生成し、PdM関連イベントを取得
- OGP画像を取得し、Slackに大きな画像付きで通知
- 通知済みイベントIDをファイルで管理し、重複通知を防止
- 通知の冒頭に@hereを付与
- GitHub Actionsで日次自動実行

## セットアップ
### 1. 必要なPythonパッケージのインストール
```bash
pip install -r requirements.txt
```

### 2. Slack Webhook URLの設定
- `config.py` で `SLACK_WEBHOOK_URL` を設定するか、環境変数で渡してください。

### 3. ローカルでの実行
```bash
python3 main.py
```

## GitHub Actionsでの運用
1. `.github/workflows/daily-notification.yml` で日次実行が設定されています。
2. リポジトリの「Settings」→「Secrets and variables」→「Actions」で `SLACK_WEBHOOK_URL` を登録してください。
3. Actionsタブから手動実行も可能です。

## カスタマイズ
### 検索キーワードの変更方法
- `pdm-event-notice/config.py` の `SEARCH_KEYWORD` を変更してください。
  - 例: `SEARCH_KEYWORD = "AI"` や `SEARCH_KEYWORD = "Python"`
- 検索期間や地域も同じファイルで `SEARCH_DAYS`, `SEARCH_PREFECTURES` を変更できます。

### 定期実行タイミングの変更方法
- `.github/workflows/daily-notification.yml` の `schedule` セクションの `cron` を編集してください。
- 例: `- cron: '0 0 * * *'`（毎日午前9時JST）
- コメントに他の時間例も記載しています。
- 変更後はコミット＆プッシュしてください。

### Slack通知の文面や画像表示方法
- `main.py` の `post_scraped_event_to_slack` 関数を編集してください。

## ログ
- ローカル実行時は `logs/` ディレクトリに日次ログが保存されます。
- GitHub Actions実行時はActionsタブでログを確認できます。

## ライセンス
MIT License 