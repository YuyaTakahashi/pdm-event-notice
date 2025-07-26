# -*- coding: utf-8 -*-

import json
import requests
import time
from bs4 import BeautifulSoup

BASE_URL = "https://connpass.com/api/v1/event/"

def search(**kwargs):
    params = kwargs
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json'
    }
    try:
        # レート制限を避けるため、少し待機
        time.sleep(1)
        res = requests.get(BASE_URL, params=params, headers=headers, timeout=10)
        res.raise_for_status()  # HTTPエラーをチェック
        print(f"Status Code: {res.status_code}")
        print(f"URL: {res.url}")
        print(f"Response Text: {res.text[:200]}...")  # 最初の200文字を表示
        return res.json()
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        print(f"Response content: {res.text}")
        return None

def printd(d):
    if d is None:
        print("データが取得できませんでした")
        return
        
    print("results_returned:\t%s" % d["results_returned"])
    print("results_available:\t%s" % d["results_available"])
    print("results_start:\t%s" % d["results_start"])

    for event in d["events"]:
        print("event_id:\t%s" % event["event_id"])
        print("title:\t%s" % event["title"])
        print("catch:\t%s" % event["catch"])
        print("event_url:\t%s" % event["event_url"])
        print("started_at:\t%s" % event["started_at"])
        print("ended_at:\t%s" % event["ended_at"])

def fetch_events_from_search_url(search_url):
    """
    connpassの検索結果URLからイベント情報をスクレイピングして取得する。
    Args:
        search_url (str): connpassの検索結果ページのURL
    Returns:
        List[dict]: イベント情報のリスト（タイトル・日時・場所・URL）
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html'
    }
    time.sleep(1)  # レート制限対策
    res = requests.get(search_url, headers=headers, timeout=10)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, 'html.parser')

    events = []
    event_area = soup.find('div', class_='event_area event_closure_list')
    if not event_area:
        print('イベントリストが見つかりませんでした')
        return events
    print(f'イベントリスト要素が見つかりました')
    event_boxes = event_area.find_all('div', class_='event_list vevent')
    print(f'イベントボックス数: {len(event_boxes)}')
    for event_box in event_boxes:
        title_tag = event_box.select_one('p.event_title a')
        schedule_area = event_box.select_one('div.event_schedule_area')
        place_tag = event_box.select_one('p.event_place.location span.icon_place')
        
        title = title_tag.get_text(strip=True) if title_tag else None
        url = title_tag['href'] if title_tag and title_tag.has_attr('href') else None
        
        # 日時の取得
        date_parts = []
        if schedule_area:
            year = schedule_area.select_one('p.year')
            date = schedule_area.select_one('p.date')
            time_elem = schedule_area.select_one('p.time')
            if year:
                date_parts.append(year.get_text(strip=True))
            if date:
                date_parts.append(date.get_text(strip=True))
            if time_elem:
                date_parts.append(time_elem.get_text(strip=True))
        date_str = ' '.join(date_parts) if date_parts else None
        
        place = place_tag.get_text(strip=True) if place_tag else None
        
        # サムネイル画像の取得
        thumbnail_tag = event_box.select_one('p.event_thumbnail img.photo')
        thumbnail = thumbnail_tag['src'] if thumbnail_tag and thumbnail_tag.has_attr('src') else None
        
        event_info = {
            'title': title,
            'url': url,
            'date': date_str,
            'place': place,
            'thumbnail': thumbnail
        }
        events.append(event_info)
        print(f'取得したイベント: {event_info}')
    return events

if __name__ == "__main__":
    # より一般的な検索条件でテスト
    print("=== 基本的な検索テスト ===")
    d = search(count=5)  # 最新の5件を取得
    printd(d)
    
    print("\n=== キーワード検索テスト ===")
    d2 = search(keyword="Python", count=3)  # Pythonキーワードで3件取得
    printd(d2)

    print("\n=== 検索URLスクレイピングテスト ===")
    search_url = "https://connpass.com/search/?q=PdM&start_from=2025%2F07%2F25&start_to=2026%2F01%2F25&prefectures=tokyo&selectItem=tokyo&sort="
    events = fetch_events_from_search_url(search_url)
    for event in events:
        print(event)