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

keywords = ws.col_values(1)[4:]  # A5:A

def surugaya_kaitori(keyword, max_count=20):
    url = f"https://www.suruga-ya.jp/kaitori/search_buy?category=&search_word={requests.utils.quote(keyword)}&searchbox=1"
    res = requests.get(url, timeout=10)
    soup = BeautifulSoup(res.content, "html.parser")
    trs = soup.select('table.result tr.lstap')
    results = []
    for tr in trs[:max_count]:
        tds = tr.select('td')
        if len(tds) < 3:
            continue
        # 商品タイトル（リンクがついてるテキスト）
        a = tds[2].select_one('a')
        title = a.text.strip() if a else tds[2].text.strip()
        # 商品URL
        url = 'https://www.suruga-ya.jp' + a['href'] if a else ''
        # JANコード
        jan_match = re.findall(r'\b\d{13}\b', tds[3].text)
        jan = jan_match[0] if jan_match else ''
        results.append((title, url, jan))
    return results

start_row = 5
for idx, keyword in enumerate(keywords):
    if not keyword.strip():
        continue
    print(f"{idx+1}件目:「{keyword}」で取得中…")
    items = surugaya_kaitori(keyword)
    # B, D, E列にそれぞれ書き込み
    b_values, d_values, e_values = [], [], []
    for t, u, j in items:
        b_values.append([t])
        d_values.append([u])
        e_values.append([j])
    end_row = start_row + len(b_values) - 1
    if b_values:
        ws.update(f'B{start_row}:B{end_row}', b_values)
        ws.update(f'D{start_row}:D{end_row}', d_values)
        ws.update(f'E{start_row}:E{end_row}', e_values)
    start_row += 20  # 次キーワード分を20行下から
    time.sleep(1.2)

print("完了！")
