import gspread
from google.oauth2.service_account import Credentials
import requests
from bs4 import BeautifulSoup
import re
import time

# 認証まわり
JSON_PATH = 'totemic-creek-306512-640467f70542.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
creds = Credentials.from_service_account_file(JSON_PATH, scopes=SCOPES)
gc = gspread.authorize(creds)

# スプレッドシート指定
SPREADSHEET_ID = '1QtWsWnKMdC9882a-_9XWDsGyp4b-LPyK0aVZDlvcpfs'
SHEET_NAME = '駿河屋リサーチ'
ws = gc.open_by_key(SPREADSHEET_ID).worksheet(SHEET_NAME)

# A列キーワード取得
keywords = ws.col_values(1)[4:24]  # A5:A(最大20件まで)

def get_titles_and_urls_from_sales(keyword, limit=20):
    """駿河屋販売ページから商品タイトル＆URL取得"""
    base_url = 'https://www.suruga-ya.jp/search?category=&search_word={}&searchbox=1'
    url = base_url.format(requests.utils.quote(keyword))
    res = requests.get(url, timeout=10)
    soup = BeautifulSoup(res.content, 'html.parser')
    items = []
    # 販売ページの構造（class="product-name"）
    for a in soup.select('h3.product-name > a')[:limit]:
        title = a.get_text(strip=True)
        link = "https://www.suruga-ya.jp" + a['href']
        items.append((title, link))
    return items

def get_jan_from_kaitori(title):
    """買取ページからJAN取得"""
    url = 'https://www.suruga-ya.jp/kaitori/search_buy?category=&search_word={}&searchbox=1'.format(requests.utils.quote(title))
    try:
        res = requests.get(url, timeout=10)
        soup = BeautifulSoup(res.content, 'html.parser')
        tds = soup.select('table.result td')
        for td in tds:
            m = re.search(r'(\d{13})', td.text)
            if m:
                return m.group(1)
        return ''
    except Exception as e:
        return ''

# 実行メイン
all_titles, all_urls, all_jans = [], [], []
for i, kw in enumerate(keywords):
    if not kw.strip():
        continue
    print(f"{i+1}件目:「{kw}」で取得中…")
    sales_items = get_titles_and_urls_from_sales(kw)
    if not sales_items:
        all_titles.append(['該当商品なし'])
        all_urls.append([''])
        all_jans.append([''])
        continue
    for title, url in sales_items:
        all_titles.append([title])
        all_urls.append([url])
        jan = get_jan_from_kaitori(title)
        all_jans.append([jan])
        time.sleep(1.5)  # サーバー負荷配慮

# 書き込み（B列=タイトル, D列=URL, E列=JAN）
ws.update('B5:B{}'.format(4+len(all_titles)), all_titles)
ws.update('D5:D{}'.format(4+len(all_urls)), all_urls)
ws.update('E5:E{}'.format(4+len(all_jans)), all_jans)
print("全て完了！")
