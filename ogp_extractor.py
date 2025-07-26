import requests
from bs4 import BeautifulSoup
import re

def extract_ogp_image(url):
    """イベントURLからOGP画像を取得"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # OGP画像を探す
        og_image = soup.find('meta', property='og:image')
        if og_image and og_image.get('content'):
            return og_image['content']
        
        # Twitter Card画像を探す
        twitter_image = soup.find('meta', attrs={'name': 'twitter:image'})
        if twitter_image and twitter_image.get('content'):
            return twitter_image['content']
        
        # 通常の画像タグを探す
        img_tags = soup.find_all('img')
        for img in img_tags:
            src = img.get('src')
            if src and ('logo' in src.lower() or 'image' in src.lower() or 'thumb' in src.lower()):
                # 相対URLを絶対URLに変換
                if src.startswith('/'):
                    from urllib.parse import urljoin
                    return urljoin(url, src)
                elif src.startswith('http'):
                    return src
        
        return None
        
    except Exception as e:
        print(f"OGP画像取得エラー ({url}): {e}")
        return None

def test_ogp_extraction():
    """OGP画像取得をテスト"""
    test_urls = [
        "https://henry.connpass.com/event/361765/",
        "https://product-people-united.connpass.com/event/358694/",
        "https://globis.connpass.com/event/360665/"
    ]
    
    for url in test_urls:
        print(f"\n--- {url} ---")
        ogp_image = extract_ogp_image(url)
        print(f"OGP画像: {ogp_image}")

if __name__ == "__main__":
    test_ogp_extraction() 