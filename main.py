import requests
import json
import os
import time
import sys
sys.path.append(os.path.join(os.path.dirname(__file__)))
from connpass import fetch_events_from_search_url
import datetime

# --- 設定項目 ---
# サーバー環境用の設定を読み込み
try:
    from config import SLACK_WEBHOOK_URL, NOTIFIED_IDS_FILE, SEARCH_KEYWORD, SEARCH_DAYS, SEARCH_PREFECTURES
except ImportError:
    # ローカル環境用のデフォルト設定
    SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/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"
    NOTIFIED_IDS_FILE = "notified_event_ids.txt"
    SEARCH_KEYWORD = "PdM"
    SEARCH_DAYS = 14
    SEARCH_PREFECTURES = "tokyo"
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

def get_event_id_from_url(url):
    """URLからイベントIDを抽出"""
    import re
    match = re.search(r'/event/(\d+)/', url)
    return match.group(1) if match else None

def post_scraped_event_to_slack(event):
    """スクレイピングで取得したイベント情報をSlackに通知（OGP画像対応）"""
    from ogp_extractor import extract_ogp_image
    
    # OGP画像を取得
    ogp_image = extract_ogp_image(event['url'])
    
    if ogp_image:
        # OGP画像がある場合は、ブロック構造で大きな画像を表示
        payload = {
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn", 
                        "text": f"新しいconnpassイベントが公開されました！ :tada:\n*<{event['url']}|{event['title']}>*\n*日時*: {event['date']}\n*場所*: {event['place']}"
                    }
                },
                {
                    "type": "image",
                    "image_url": ogp_image,
                    "alt_text": event['title']
                }
            ]
        }
    else:
        # OGP画像がない場合は、テキストのみ
        message = f"""
        新しいconnpassイベントが公開されました！ :tada:
        *<{event['url']}|{event['title']}>*
        *日時*: {event['date']}
        *場所*: {event['place']}
        """
        payload = {"text": message}
    
    print(f"Slack通知を送信中: {event['title']}")
    response = requests.post(SLACK_WEBHOOK_URL, data=json.dumps(payload))
    print(f"Slack通知レスポンス: {response.status_code}")
    if response.status_code != 200:
        print(f"Slack通知エラー: {response.text}")

def fetch_and_notify_scraped_events(search_url):
    """検索URLからイベントをスクレイピングし、新規イベントのみSlack通知（notified_event_ids.txtで管理）"""
    events = fetch_events_from_search_url(search_url)
    notified_ids = get_notified_ids()
    print(f"通知済みID数: {len(notified_ids)}")
    print(f"取得したイベント数: {len(events)}")
    new_events = [e for e in events if e['event_id'] and e['event_id'] not in notified_ids]
    print(f"新規イベント数: {len(new_events)}")
    if not new_events:
        print("新規イベントはありませんでした。")
        return
    for event in new_events:
        print(f"新規イベントを発見: {event['title']}")
        post_scraped_event_to_slack(event)
        notified_ids.add(event['event_id'])
    save_notified_ids(notified_ids)
    print(f"処理完了。{len(new_events)}件の新規イベントを通知しました。")

if __name__ == "__main__":
    # API経由の通知（従来）
    # fetch_new_events()

    # 検索URLを実行日から設定された期間後までで自動生成
    today = datetime.date.today()
    end_date = today + datetime.timedelta(days=SEARCH_DAYS)
    start_str = today.strftime("%Y/%m/%d")
    end_str = end_date.strftime("%Y/%m/%d")
    search_url = f"https://connpass.com/search/?q={SEARCH_KEYWORD}&start_from={start_str}&start_to={end_str}&prefectures={SEARCH_PREFECTURES}&selectItem={SEARCH_PREFECTURES}&sort="
    print(f"検索URL: {search_url}")
    fetch_and_notify_scraped_events(search_url)
