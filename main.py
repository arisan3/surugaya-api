import gspread
from google.oauth2.service_account import Credentials
import requests
from bs4 import BeautifulSoup
import time
import re

# Googleサービスアカウントの設定
JSON_PATH = 'totemic-creek-306512-640467f70542.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
creds = Credentials.from_service_account_file(JSON_PATH, scopes=SCOPES)
gc = gspread.authorize(creds)

SPREADSHEET_ID = '1QtWsWnKMdC9882a-_9XWDsGyp4b-LPyK0aVZDlvcpfs'
SHEET_NAME = '駿河屋リサーチ'
ws = gc.open_by_key(SPREADSHEET_ID).worksheet(SHEET_NAME)

def search_surugaya_products(keyword, max_count=20):
    url = f'https://www.suruga-ya.jp/search?category=&search_word={requests.utils.quote(keyword)}&searchbox=1'
    res = requests.get(url, timeout=10)
    soup = BeautifulSoup(res.content, 'html.parser')
    items = []
    for a in soup.select('.item_detail .title > a')[:max_count]:
        title = a.get_text(strip=True)
        href = a.get('href')
        if not href.startswith('http'):
            href = 'https://www.suruga-ya.jp' + href
        items.append((title, href))
    return items

def get_jan_code(product_url):
    try:
        res = requests.get(product_url, timeout=10)
        soup = BeautifulSoup(res.content, 'html.parser')
        # JANコードは商品詳細テーブル内に出現
        text = soup.get_text()
        m = re.search(r'\b\d{13}\b', text)
        if m:
            return m.group(0)
        return ''
    except Exception as e:
        return ''

# 検索キーワード取得（A列5行目以降）
keywords = ws.col_values(1)[4:]
all_titles = []
all_urls = []
all_jans = []

for keyword in keywords:
    if not keyword.strip():
        continue
    print(f'キーワード「{keyword}」検索中…')
    results = search_surugaya_products(keyword, max_count=20)
    if not results:
        all_titles.append(['該当商品なし'])
        all_urls.append([''])
        all_jans.append([''])
        continue
    for title, url in results:
        all_titles.append([title])
        all_urls.append([url])    # URLのまま
        jan = get_jan_code(url)
        all_jans.append([jan])
        time.sleep(1.0)  # 負荷対策

# スプレッドシートへ一括書き込み
if all_titles:
    ws.update('B5:B{}'.format(4+len(all_titles)), all_titles)
if all_urls:
    ws.update('D5:D{}'.format(4+len(all_urls)), all_urls)
if all_jans:
    ws.update('E5:E{}'.format(4+len(all_jans)), all_jans)

print('全て完了！')
