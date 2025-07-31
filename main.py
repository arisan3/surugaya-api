import gspread
from google.oauth2.service_account import Credentials
import requests
from bs4 import BeautifulSoup
import re
import time

# Google認証
JSON_PATH = 'totemic-creek-306512-640467f70542.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
creds = Credentials.from_service_account_file(JSON_PATH, scopes=SCOPES)
gc = gspread.authorize(creds)

SPREADSHEET_ID = '1QtWsWnKMdC9882a-_9XWDsGyp4b-LPyK0aVZDlvcpfs'
SHEET_NAME = '駿河屋リサーチ'
ws = gc.open_by_key(SPREADSHEET_ID).worksheet(SHEET_NAME)

def search_surugaya_products(keyword):
    # 駿河屋の通常検索URL
    url = f'https://www.suruga-ya.jp/search?category=&search_word={requests.utils.quote(keyword)}&searchbox=1'
    res = requests.get(url)
    soup = BeautifulSoup(res.content, 'html.parser')
    items = soup.select('.item_detail')
    results = []
    for item in items[:20]:  # 最大20件
        # 商品タイトル
        title_tag = item.select_one('.product-name')
        if not title_tag:
            continue
        title = title_tag.get_text(strip=True)
        # 商品詳細URL
        link_tag = item.select_one('a[href*="/product/"]')
        url = f"https://www.suruga-ya.jp{link_tag['href']}" if link_tag else ''
        results.append((title, url))
    return results

def get_jan_from_kaitori(title):
    url = f'https://www.suruga-ya.jp/kaitori/search_buy?category=&search_word={requests.utils.quote(title)}&searchbox=1'
    res = requests.get(url, timeout=10)
    if res.status_code != 200:
        return ''
    soup = BeautifulSoup(res.content, 'html.parser')
    tds = soup.select('table.result td')
    for td in tds:
        m = re.search(r'(\d{13})', td.text)
        if m:
            return m.group(1)
    return ''

# スプレッドシートからキーワード取得
keywords = ws.col_values(1)[4:]  # A5:A

all_titles = []
all_urls = []
all_jans = []

for i, keyword in enumerate(keywords):
    if not keyword.strip():
        continue
    print(f"{i+1}件目:「{keyword}」検索中…")
    products = search_surugaya_products(keyword)
    for title, url in products:
        jan = get_jan_from_kaitori(title)
        all_titles.append([title])
        all_urls.append([url])
        all_jans.append([jan])
        time.sleep(1)  # 優しめに

# シート書き込み（B列、D列、E列）
if all_titles:
    ws.update('B5:B{}'.format(4+len(all_titles)), all_titles)
    ws.update('D5:D{}'.format(4+len(all_urls)), all_urls)
    ws.update('E5:E{}'.format(4+len(all_jans)), all_jans)
    print("全て完了！")
else:
    print('取得結果なし')
