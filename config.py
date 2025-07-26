import os

# Slack Webhook URL（環境変数から取得）
SLACK_WEBHOOK_URL = os.getenv('SLACK_WEBHOOK_URL', "https://hooks.slack.com/services/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")

# 通知済みイベントIDを保存するファイル
NOTIFIED_IDS_FILE = "notified_event_ids.txt"

# 検索設定
SEARCH_KEYWORD = "PdM"
SEARCH_DAYS = 14  # 2週間
SEARCH_PREFECTURES = "tokyo" 