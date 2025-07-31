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

# 検索キーワード取得
keywords = ws.col_values(1)[4:]
keywords = [kw for kw in keywords if kw]

titles = []
eng_titles = []
urls = []
hyperlinks = []
jans = []

def get_surugaya_url_and_title(keyword):
    # 駿河屋で商品ページ検索→URLと日本語タイトル取得
    search_url = f"https://www.suruga-ya.jp/search?search_word={keyword}&category=0"
    res = requests.get(search_url)
    soup = BeautifulSoup(res.text, 'html.parser')
    link = soup.select_one('.title > a')
    url, title = "", ""
    if link:
        url = "https://www.suruga-ya.jp" + link['href']
        detail = requests.get(url)
        detail_soup = BeautifulSoup(detail.text, 'html.parser')
        title_elem = detail_soup.select_one('h3.product-name')
        if title_elem:
            title = title_elem.text.strip()
    return url, title

def get_jan_from_kaitori(title):
    # 日本語タイトルで買取ページ検索してJANを取得
    if not title:
        return ""
    search_url = f"https://www.suruga-ya.jp/kaitori_search?search_word={title}&category=0"
    res = requests.get(search_url)
    soup = BeautifulSoup(res.text, 'html.parser')
    # 検索結果から1件目の商品詳細ページ
    link = soup.select_one('.title > a')
    if link:
        url = "https://www.suruga-ya.jp" + link['href']
        detail = requests.get(url)
        detail_soup = BeautifulSoup(detail.text, 'html.parser')
        jan_span = detail_soup.find("span", string=lambda s: s and 'JAN：' in s)
        if jan_span:
            jan = jan_span.text.split("：")[1].strip()
            return jan
    return ""

for keyword in keywords:
    url, title = get_surugaya_url_and_title(keyword)
    titles.append([title])
    eng_titles.append([title])  # 本来は翻訳APIでOK
    urls.append([url])
    hyperlinks.append([url])
    jan = get_jan_from_kaitori(title)
    jans.append([jan])
    time.sleep(1)  # サーバー負荷対策

# 書き込み
ws.update(f'B5:B{4+len(titles)}', titles)
ws.update(f'C5:C{4+len(eng_titles)}', eng_titles)
ws.update(f'D5:D{4+len(hyperlinks)}', hyperlinks)
ws.update(f'E5:E{4+len(jans)}', jans)
