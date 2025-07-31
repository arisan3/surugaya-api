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

# 検索キーワード取得
keywords = ws.col_values(1)[4:]
keywords = [kw for kw in keywords if kw]

def get_surugaya_url(title):
    # 検索結果から1番目の商品URLを取得
    search_url = f"https://www.suruga-ya.jp/search?search_word={title}&category=0"
    res = requests.get(search_url)
    soup = BeautifulSoup(res.text, 'html.parser')
    link = soup.select_one('.title > a')
    if link:
        url = "https://www.suruga-ya.jp" + link['href']
        return url
    return ""

def get_jan_from_kaitori(title):
    # 買取ページのJAN取得
    search_url = f"https://www.suruga-ya.jp/kaitori_search?search_word={title}&category=0"
    res = requests.get(search_url)
    soup = BeautifulSoup(res.text, 'html.parser')
    jan_span = soup.find("span", string=lambda s: s and 'JAN：' in s)
    if jan_span:
        jan = jan_span.text.split("：")[1].strip()
        return jan
    return ""

titles = []
eng_titles = []
urls = []
hyperlinks = []
jans = []

for keyword in keywords:
    # 販売ページのタイトルとURL取得
    url = get_surugaya_url(keyword)
    urls.append([url])  # 2次元リスト
    if url:
        # スクレイピングで商品タイトル取得
        res = requests.get(url)
        soup = BeautifulSoup(res.text, 'html.parser')
        jp_title = soup.select_one('h3.product-name')
        if jp_title:
            title = jp_title.text.strip()
        else:
            title = ""
    else:
        title = ""
    titles.append([title])
    eng_titles.append([title])  # 本来は翻訳API推奨
    # HYPERLINK用
    hyperlinks.append([f'=HYPERLINK("{url}", "リンク")' if url else ""])
    # JAN
    jan = get_jan_from_kaitori(title)
    jans.append([jan])
    time.sleep(1)  # 負荷対策

# 書き込み（2次元リスト形式！）
ws.update(f'B5:B{4+len(titles)}', titles)
ws.update(f'C5:C{4+len(eng_titles)}', eng_titles)
ws.update(f'D5:D{4+len(hyperlinks)}', hyperlinks)
ws.update(f'E5:E{4+len(jans)}', jans)
