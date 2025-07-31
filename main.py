import gspread
from google.oauth2.service_account import Credentials
import requests
from bs4 import BeautifulSoup
import time

JSON_PATH = 'totemic-creek-306512-640467f70542.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID = '1QtWsWnKMdC9882a-_9XWDsGyp4b-LPyK0aVZDlvcpfs'

creds = Credentials.from_service_account_file(JSON_PATH, scopes=SCOPES)
gc = gspread.authorize(creds)
sh = gc.open_by_key(SPREADSHEET_ID)
ws = sh.worksheet('駿河屋リサーチ')

# A列5行目以降のキーワード取得
keywords = ws.col_values(1)[4:]
keywords = [kw for kw in keywords if kw]

all_titles = []
all_links = []

for keyword in keywords:
    print(f"検索: {keyword}")
    search_url = f"https://www.suruga-ya.jp/search?search_word={keyword}&category=0"
    res = requests.get(search_url)
    soup = BeautifulSoup(res.text, 'html.parser')
    items = soup.select('.title > a')
    count = 0

    for item in items:
        if count >= 20:
            break
        url = "https://www.suruga-ya.jp" + item['href']
        title = item.text.strip()
        all_titles.append([title])
        all_links.append([f'=HYPERLINK("{url}", "リンク")'])
        count += 1
    time.sleep(1)

# B5/D5から書き込み
ws.update(f'B5:B{4+len(all_titles)}', all_titles)
ws.update(f'D5:D{4+len(all_links)}', all_links, value_input_option="USER_ENTERED")
