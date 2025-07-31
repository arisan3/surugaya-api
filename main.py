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

keywords = ws.col_values(1)[4:]
keywords = [kw for kw in keywords if kw]

def normalize_surugaya_url(href):
    if href.startswith('http'):
        return href
    else:
        return "https://www.suruga-ya.jp" + href

titles = []
hyperlinks = []

for keyword in keywords:
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

ws.update(f'B5:B{4+len(titles)}', titles, value_input_option='USER_ENTERED')
ws.update(f'D5:D{4+len(hyperlinks)}', hyperlinks, value_input_option='USER_ENTERED')

import re

def get_jan_from_kaitori(title):
    if not title:
        return ""
    url = f"https://www.suruga-ya.jp/kaitori/search_buy?category=&search_word={requests.utils.quote(title)}&searchbox=1"
    res = requests.get(url)
    soup = BeautifulSoup(res.text, "html.parser")
    jan_cell = soup.select_one("td[width='200px']")
    if jan_cell:
        text = jan_cell.get_text(separator="\n")
        # 正規表現でJANコードだけ抽出（13桁数字）
        match = re.search(r"\b\d{13}\b", text)
        if match:
            return match.group()
    return ""

# forループ内
jan = get_jan_from_kaitori(title)   # ← jp_title → titleに修正
jans.append([jan])
