
# 必要なライブラリのインストール（初回のみ）
import gspread
from google.oauth2.service_account import Credentials

JSON_PATH = '/content/drive/MyDrive/totemic-creek-306512-640467f70542.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

creds = Credentials.from_service_account_file(JSON_PATH, scopes=SCOPES)
gc = gspread.authorize(creds)

SPREADSHEET_ID = '1QtWsWnKMdC9882a-_9XWDsGyp4b-LPyK0aVZDlvcpfs'
SHEET_NAME = '駿河屋リサーチ'
ws = gc.open_by_key(SPREADSHEET_ID).worksheet(SHEET_NAME)

# B列の商品タイトルを取得
titles = ws.col_values(2)[4:]  # B5:B

import requests
from bs4 import BeautifulSoup
import re
import time

def get_jan_from_kaitori(title):
    url = f'https://www.suruga-ya.jp/kaitori/search_buy?category=&search_word={requests.utils.quote(title)}&searchbox=1'
    try:
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
    except Exception as e:
        return ''

jan_list = []
for i, title in enumerate(titles):
    if title.strip() == '' or title.startswith('該当商品なし'):
        jan_list.append('')
        continue
    jan = get_jan_from_kaitori(title)
    jan_list.append(jan)
    print(f'{i+1}: {title} -> {jan}')
    time.sleep(1.2)  # サーバー負荷対策

# E列に一括書き込み
if len(jan_list) > 0:
    cell_range = f'E5:E{4+len(jan_list)}'
    cells = [[j] for j in jan_list]
    ws.update(cell_range, cells)
    print(f'JANコードを{len(jan_list)}件、E列に一括書き込み完了！')
else:
    print('JANコード書き込み対象がありません')
