import gspread
from google.oauth2.service_account import Credentials
import requests
from bs4 import BeautifulSoup
import re
import time

# 認証
JSON_PATH = 'totemic-creek-306512-640467f70542.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
creds = Credentials.from_service_account_file(JSON_PATH, scopes=SCOPES)
gc = gspread.authorize(creds)

# スプレッドシート設定
SPREADSHEET_ID = '1QtWsWnKMdC9882a-_9XWDsGyp4b-LPyK0aVZDlvcpfs'
SHEET_NAME = '駿河屋リサーチ'
ws = gc.open_by_key(SPREADSHEET_ID).worksheet(SHEET_NAME)

# A列のキーワードからB列に商品タイトル（日本語） D列に販売ページURL
keywords = ws.col_values(1)[4:]  # A5:A

# 1商品最大20件取得
MAX = 20

def get_surugaya_items(keyword):
    url = f'https://www.suruga-ya.jp/search?category=&search_word={requests.utils.quote(keyword)}&searchbox=1'
    res = requests.get(url, timeout=10)
    soup = BeautifulSoup(res.content, 'html.parser')
    items = []
    for a in soup.select('.item_detail a[href*="/product/"]')[:MAX]:
        title = a.get_text(strip=True)
        link = 'https://www.suruga-ya.jp' + a['href']
        items.append({'title': title, 'url': link})
    return items

def get_english_title(jp_title):
    # ここはDeepL APIやGoogle翻訳APIと連携可能（ここではダミー）
    return jp_title  # 英訳が不要ならそのまま返す

def get_jan_from_kaitori(title):
    # 駿河屋買取ページで検索してJAN取得
    search_url = f'https://www.suruga-ya.jp/kaitori/search_buy?category=&search_word={requests.utils.quote(title)}&searchbox=1'
    res = requests.get(search_url, timeout=10)
    soup = BeautifulSoup(res.content, 'html.parser')
    a = soup.select_one('div.item_detail a[href*="/product/other/"]')
    if not a:
        return ''
    detail_url = 'https://www.suruga-ya.jp' + a['href']
    detail_res = requests.get(detail_url, timeout=10)
    detail_soup = BeautifulSoup(detail_res.content, 'html.parser')
    m = re.search(r'\b\d{13}\b', detail_soup.get_text())
    if m:
        return m.group(0)
    return ''

all_titles = []
all_titles_en = []
all_urls = []
all_jans = []

for kw in keywords:
    items = get_surugaya_items(kw)
    if not items:
        # No hit
        all_titles.append(['該当商品なし'])
        all_titles_en.append(['No matching products'])
        all_urls.append([''])
        all_jans.append([''])
        continue
    for i, item in enumerate(items):
        all_titles.append([item['title']])
        all_titles_en.append([get_english_title(item['title'])])
        # D列：URLを直接貼り付け（スプレッドシート側で自動でリンク化される）
        all_urls.append([item['url']])
        # E列：JANコード（買取ページから取得）
        jan = get_jan_from_kaitori(item['title'])
        all_jans.append([jan])
        print(f"{kw} {i+1}件目: {item['title']} - {jan}")
        time.sleep(1.2)

# スプレッドシートに一括書き込み
if all_titles:
    ws.update(all_titles, range_name=f'B5:B{4+len(all_titles)}')
    ws.update(all_titles_en, range_name=f'C5:C{4+len(all_titles_en)}')
    ws.update(all_urls, range_name=f'D5:D{4+len(all_urls)}')
    ws.update(all_jans, range_name=f'E5:E{4+len(all_jans)}')
    print("書き込み完了！")
else:
    print("対象データなし")
