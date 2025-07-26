import requests
import json
import os
import time
import sys
sys.path.append(os.path.join(os.path.dirname(__file__)))
from connpass import fetch_events_from_search_url
import datetime
import hashlib

# --- 設定項目 ---
# GitHubのSecretsからWebhook URLを読み込む
SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/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"


# 検索キーワードと検索タイプ
# AND検索: ["Python", "AI"] / OR検索: ["Python,AI"] など
SEARCH_KEYWORDS = ["Python", "機械学習", "AI"]
SEARCH_TYPE = "OR" # "AND" または "OR"

# 通知済みイベントIDを保存するファイル
NOTIFIED_IDS_FILE = "pdm-event-notice/notified_event_ids.txt"
# -----------------

def get_notified_ids():
    """通知済みのイベントIDまたはURLハッシュをファイルから読み込む"""
    if not os.path.exists(NOTIFIED_IDS_FILE):
        return set()
    with open(NOTIFIED_IDS_FILE, "r") as f:
        return set(line.strip() for line in f)

def save_notified_ids(ids):
    """通知済みのイベントIDまたはURLハッシュをファイルに保存"""
    with open(NOTIFIED_IDS_FILE, "w") as f:
        for event_id in sorted(ids):
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

    base_url = "https://connpass.com/api/v1/event/"
    
    # より適切なヘッダーを設定
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json',
        'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8'
    }
    
    # パラメータを設定
    params = {
        'order': 2,  # 開催日順
        'count': 50
    }
    
    if SEARCH_TYPE.upper() == 'OR':
        params['keyword_or'] = ','.join(SEARCH_KEYWORDS)
    else:
        params['keyword'] = ','.join(SEARCH_KEYWORDS)
    
    print(f"API URL: {base_url}")
    print(f"Parameters: {params}")
    
    try:
        # レート制限を避けるため、少し待機
        time.sleep(2)
        
        response = requests.get(base_url, params=params, headers=headers, timeout=15)
        print(f"Status Code: {response.status_code}")
        print(f"Response URL: {response.url}")
        
        response.raise_for_status()
        events_data = response.json().get('events', [])
        
        print(f"取得したイベント数: {len(events_data)}")
        
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
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response Status: {e.response.status_code}")
            print(f"Response Text: {e.response.text[:500]}...")
    except json.JSONDecodeError as e:
        print(f"JSONデコードエラー: {e}")
        print(f"Response Text: {response.text[:500]}...")

def url_to_hash(url):
    """URLをSHA256ハッシュ値に変換"""
    return hashlib.sha256(url.encode('utf-8')).hexdigest()

def post_scraped_event_to_slack(event):
    """スクレイピングで取得したイベント情報をSlackに通知（サムネイル画像対応）"""
    message = f"""
    新しいconnpassイベントが公開されました！ :tada:
    *<{event['url']}|{event['title']}>*
    *日時*: {event['date']}
    *場所*: {event['place']}
    """
    if event.get('thumbnail'):
        payload = {
            "blocks": [
                {
                    "type": "image",
                    "image_url": event['thumbnail'],
                    "alt_text": event['title']
                },
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": message}
                }
            ]
        }
    else:
        payload = {"text": message}
    requests.post(SLACK_WEBHOOK_URL, data=json.dumps(payload))

def fetch_and_notify_scraped_events(search_url):
    """検索URLからイベントをスクレイピングし、新規イベントのみSlack通知（notified_event_ids.txtで管理）"""
    events = fetch_events_from_search_url(search_url)
    notified_ids = get_notified_ids()
    print(f"通知済みID数: {len(notified_ids)}")
    print(f"取得したイベント数: {len(events)}")
    new_events = [e for e in events if e['url'] and url_to_hash(e['url']) not in notified_ids]
    print(f"新規イベント数: {len(new_events)}")
    if not new_events:
        print("新規イベントはありませんでした。")
        return
    for event in new_events:
        print(f"新規イベントを発見: {event['title']}")
        post_scraped_event_to_slack(event)
        notified_ids.add(url_to_hash(event['url']))
    save_notified_ids(notified_ids)
    print(f"処理完了。{len(new_events)}件の新規イベントを通知しました。")

if __name__ == "__main__":
    # API経由の通知（従来）
    # fetch_new_events()

    # 検索URLを実行日から2ヶ月後までで自動生成
    today = datetime.date.today()
    two_months_later = today + datetime.timedelta(days=62)  # 2ヶ月=約62日
    start_str = today.strftime("%Y/%m/%d")
    end_str = two_months_later.strftime("%Y/%m/%d")
    search_url = f"https://connpass.com/search/?q=PdM&start_from={start_str}&start_to={end_str}&prefectures=tokyo&selectItem=tokyo&sort="
    print(f"検索URL: {search_url}")
    fetch_and_notify_scraped_events(search_url)
