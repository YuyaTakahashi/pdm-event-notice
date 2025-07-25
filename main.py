import requests
import json
import os

# --- 設定項目 ---
# GitHubのSecretsからWebhook URLを読み込む
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL")

# 検索キーワードと検索タイプ
# AND検索: ["Python", "AI"] / OR検索: ["Python,AI"] など
SEARCH_KEYWORDS = ["Python", "機械学習", "AI"]
SEARCH_TYPE = "OR" # "AND" または "OR"

# 通知済みイベントIDを保存するファイル
NOTIFIED_IDS_FILE = "notified_event_ids.txt"
# -----------------

def get_notified_ids():
    """通知済みのイベントIDをファイルから読み込む"""
    if not os.path.exists(NOTIFIED_IDS_FILE):
        return set()
    with open(NOTIFIED_IDS_FILE, "r") as f:
        return set(line.strip() for line in f)

def save_notified_ids(ids):
    """通知済みのイベントIDをファイルに保存する"""
    with open(NOTIFIED_IDS_FILE, "w") as f:
        for event_id in sorted(ids, key=int):
            f.write(str(event_id) + "\n")

def post_to_slack(event):
    """イベント情報をSlackに通知する"""
    message = f"""
    新しいconnpassイベントが公開されました！ :tada:
    *<{event['event_url']}|{event['title']}>*
    *日時*: {event['started_at']}
    *場所*: {event['address']} ({event['place']})
    """
    payload = {"text": message}
    requests.post(SLACK_WEBHOOK_URL, data=json.dumps(payload))

def fetch_new_events():
    """connpass APIから新しいイベントを取得して通知する"""
    if not SLACK_WEBHOOK_URL:
        print("エラー: SLACK_WEBHOOK_URLが設定されていません。")
        return

    base_url = "https://connpass.com/api/v1/event/?order=2&count=50"
    if SEARCH_TYPE.upper() == 'OR':
        params = '&'.join([f'keyword_or={kw}' for kw in SEARCH_KEYWORDS])
    else:
        params = '&'.join([f'keyword={kw}' for kw in SEARCH_KEYWORDS])
    
    api_url = f"{base_url}&{params}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'
    }

    try:
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        events_data = response.json().get('events', [])
        
        notified_ids = get_notified_ids()
        new_events = []
        
        for event in events_data:
            event_id = str(event['event_id'])
            if event_id not in notified_ids:
                new_events.append(event)
        
        if not new_events:
            print("新規イベントはありませんでした。")
            return

        # 時系列の古い順に通知
        for event in sorted(new_events, key=lambda x: x['event_id']):
            print(f"新規イベントを発見: {event['title']}")
            post_to_slack(event)
            notified_ids.add(str(event['event_id']))
        
        save_notified_ids(notified_ids)
        print(f"処理完了。{len(new_events)}件の新規イベントを通知しました。")

    except requests.exceptions.RequestException as e:
        print(f"APIリクエスト中にエラーが発生しました: {e}")

if __name__ == "__main__":
    fetch_new_events()
