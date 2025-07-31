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

# スプレッドシート設定
SPREADSHEET_ID = '1QtWsWnKMdC9882a-_9XWDsGyp4b-LPyK0aVZDlvcpfs'
SHEET_NAME = '駿河屋リサーチ'
ws = gc.open_by_key(SPREADSHEET_ID).worksheet(SHEET_NAME)

# A列（キーワード）取得
keywords = ws.col_values(1)[4:]  # A5以降

def get_surugaya_items(keyword, max_count=20):
    # 駿河屋で検索
    search_url = f'https://www.suruga-ya.jp/kaitori/search_buy?category=&search_word={requests.utils.quote(keyword)}&searchbox=1'
    res = requests.get(search_url, timeout=10)
    soup = BeautifulSoup(res.content, 'html.parser')
    rows = soup.select('table.result tr.l1stap')[:max_count]
    items = []
    for row in rows:
        # タイトルと商品詳細ページURL
        a_tag = row.find('a', href=True)
        if not a_tag:
            continue
        title = a_tag.text.strip()
        link = 'https://www.suruga-ya.jp' + a_tag['href']
        # 商品詳細ページからJANコード取得
        jan = ''
        try:
            detail_res = requests.get(link, timeout=10)
            detail_soup = BeautifulSoup(detail_res.content, 'html.parser')
            text = detail_soup.get_text()
            m = re.search(r'\b(\d{13})\b', text)
            if m:
                jan = m.group(1)
        except Exception as e:
            pass
        items.append((title, link, jan))
        time.sleep(1)  # アクセス負荷軽減
    return items

# データ格納用
all_titles = []
all_urls = []
all_jans = []

for kw in keywords:
    if not kw.strip():
        all_titles.append([''])
        all_urls.append([''])
        all_jans.append([''])
        continue
    items = get_surugaya_items(kw, max_count=20)
    if not items:
        all_titles.append(['該当商品なし'])
        all_urls.append([''])
        all_jans.append([''])
        continue
    # 1セルに1行ずつ（タイトル・URL・JAN）を改行区切りでまとめて入れる
    titles = [x[0] for x in items]
    urls = [x[1] for x in items]
    jans = [x[2] for x in items]
    all_titles.append(["\n".join(titles)])
    all_urls.append(["\n".join(urls)])
    all_jans.append(["\n".join(jans)])

# B列、D列、E列に一括書き込み
if all_titles:
    ws.update(f'B5:B{4+len(all_titles)}', all_titles)
if all_urls:
    ws.update(f'D5:D{4+len(all_urls)}', all_urls)
if all_jans:
    ws.update(f'E5:E{4+len(all_jans)}', all_jans)

print('全て完了！')
