import gspread
from google.oauth2.service_account import Credentials
import requests
from bs4 import BeautifulSoup
import time

# サービスアカウントJSONパス
JSON_PATH = 'totemic-creek-306512-640467f70542.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID = '1QtWsWnKMdC9882a-_9XWDsGyp4b-LPyK0aVZDlvcpfs'

creds = Credentials.from_service_account_file(JSON_PATH, scopes=SCOPES)
gc = gspread.authorize(creds)
sh = gc.open_by_key(SPREADSHEET_ID)
ws = sh.worksheet('駿河屋リサーチ')

# 検索キーワード（A列 5行目以降）
keywords = ws.col_values(1)[4:]
keywords = [kw for kw in keywords if kw]

def normalize_surugaya_url(href):
    if href.startswith('http'):
        return href
    else:
        return "https://www.suruga-ya.jp" + href

# 取得用リスト
titles = []
hyperlinks = []

for keyword in keywords:
    # 1キーワードにつき最大20件取得
    search_url = f"https://www.suruga-ya.jp/search?search_word={keyword}&category=0"
    res = requests.get(search_url)
    soup = BeautifulSoup(res.text, 'html.parser')
    items = soup.select('.title > a')[:20]

    for item in items:
        jp_title = item.get_text(strip=True)
        href = item.get('href')
        url = normalize_surugaya_url(href)
        titles.append([jp_title])
        hyperlinks.append([f'=HYPERLINK("{url}", "リンク")'])
    time.sleep(1)

# 書き込み
ws.update(f'B5:B{4+len(titles)}', titles)
ws.update(f'D5:D{4+len(hyperlinks)}', hyperlinks)
