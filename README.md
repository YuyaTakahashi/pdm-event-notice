# Connpass Event Notification

PdM関連のconnpassイベントを自動でSlackに通知するシステム

## 機能

- 指定したキーワードでconnpassイベントを検索
- 新規イベントをSlackに通知（OGP画像付き）
- 重複通知を防止（イベントID管理）
- 動的日付範囲設定

## サーバー環境での実行方法

### 1. GitHub Actions（推奨）

1. このリポジトリをGitHubにプッシュ
2. リポジトリのSettings > Secrets and variables > Actionsで以下を設定：
   - `SLACK_WEBHOOK_URL`: Slack Webhook URL
3. `.github/workflows/daily-notification.yml`が自動で毎日午前9時（JST）に実行

### 2. サーバーでのcron実行

```bash
# 依存関係のインストール
pip install requests beautifulsoup4

# cron設定（毎日午前9時に実行）
0 9 * * * /path/to/pdm-event-notice/run_daily.sh
```

### 3. Docker実行

```bash
# Dockerfileを作成
docker build -t connpass-notifier .
docker run --env SLACK_WEBHOOK_URL=your_webhook_url connpass-notifier
```

## 設定

`config.py`で以下の設定を変更可能：

- `SLACK_WEBHOOK_URL`: Slack Webhook URL
- `SEARCH_KEYWORD`: 検索キーワード（デフォルト: "PdM"）
- `SEARCH_DAYS`: 検索期間（デフォルト: 14日）
- `SEARCH_PREFECTURES`: 検索地域（デフォルト: "tokyo"）

## ローカル実行

```bash
python3 main.py
```

## ログ

- GitHub Actions: Actionsタブで実行ログを確認
- サーバー実行: `logs/`ディレクトリに日次ログが保存 