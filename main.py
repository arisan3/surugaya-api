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

# 商品リスト（A6以降だけ取得 ※A5はラベルなので除外！）
keywords = ws.col_values(1)[5:]
keywords = [kw for kw in keywords if kw]  # 空欄除外

def get_surugaya_url(title):
    search_url = f"https://www.suruga-ya.jp/search?search_word={title}&category=0"
    res = requests.get(search_url)
    soup = BeautifulSoup(res.text, 'html.parser')
    link = soup.select_one('.title > a')
    if link:
        url = "https://www.suruga-ya.jp" + link['href']
        return url
    return ""

def get_jan_from_kaitori(title):
    search_url = f"https://www.suruga-ya.jp/kaitori_search?search_word={title}&category=0"
    res = requests.get(search_url)
    soup = BeautifulSoup(res.text, 'html.parser')
    jan_span = soup.find("span", string=lambda s: s and 'JAN：' in s)
    if jan_span:
        jan = jan_span.text.split("：")[1].strip()
        return jan
    return ""

titles = []
hyperlinks = []
jans = []

for keyword in keywords:
    url = get_surugaya_url(keyword)
    # 商品タイトル取得
    if url:
        res = requests.get(url)
        soup = BeautifulSoup(res.text, 'html.parser')
        jp_title = soup.select_one('h3.product-name')
        title = jp_title.text.strip() if jp_title else ""
    else:
        title = ""
    titles.append([title])
    hyperlinks.append([f'=HYPERLINK("{url}", "リンク")' if url else ""])
    jan = get_jan_from_kaitori(title)  # 必ずB列タイトルでJAN検索
    jans.append([jan])
    time.sleep(1)

# 書き込み
ws.update(f'B6:B{5+len(titles)}', titles)       # B6から
ws.update(f'D6:D{5+len(hyperlinks)}', hyperlinks)  # D6から
ws.update(f'E6:E{5+len(jans)}', jans)          # E6から
