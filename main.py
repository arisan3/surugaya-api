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

titles = []
eng_titles = []
hyperlinks = []
jans = []

def get_surugaya_url_and_title(keyword):
    search_url = f"https://www.suruga-ya.jp/search?search_word={keyword}&category=0"
    res = requests.get(search_url)
    print("URL検索:", search_url, "status:", res.status_code)
    soup = BeautifulSoup(res.text, 'html.parser')
    link = soup.select_one('.title > a')
    url, title = "", ""
    if link:
        url = "https://www.suruga-ya.jp" + link['href']
        detail = requests.get(url)
        print("詳細ページ:", url, "status:", detail.status_code)
        detail_soup = BeautifulSoup(detail.text, 'html.parser')
        title_elem = detail_soup.select_one('h3.product-name')
        if title_elem:
            title = title_elem.text.strip()
    # デバッグ
    print("取得タイトル:", title, "| 取得URL:", url)
    return url, title

def get_jan_from_kaitori(title):
    if not title:
        return ""
    search_url = f"https://www.suruga-ya.jp/kaitori_search?search_word={title}&category=0"
    res = requests.get(search_url)
    print("JAN検索:", search_url, "status:", res.status_code)
    soup = BeautifulSoup(res.text, 'html.parser')
    link = soup.select_one('.title > a')
    if link:
        url = "https://www.suruga-ya.jp" + link['href']
        detail = requests.get(url)
        print("買取詳細ページ:", url, "status:", detail.status_code)
        detail_soup = BeautifulSoup(detail.text, 'html.parser')
        jan_span = detail_soup.find("span", string=lambda s: s and 'JAN：' in s)
        if jan_span:
            jan = jan_span.text.split("：")[1].strip()
            print("取得JAN:", jan)
            return jan
    print("JANなし")
    return ""

for idx, keyword in enumerate(keywords):
    print(f"==={idx+1}件目: {keyword}===")
    url, title = get_surugaya_url_and_title(keyword)
    # タイトルが空ならキーワードで補完
    titles.append([title if title else keyword])
    eng_titles.append([title if title else keyword])
    hyperlinks.append([f'=HYPERLINK("{url}", "リンク")' if url else ""])
    jan = get_jan_from_kaitori(title if title else keyword)
    jans.append([jan])
    time.sleep(1.2)

# スプレッドシート書き込み
ws.update('B5', titles)
ws.update('C5', eng_titles)
ws.update('D5', hyperlinks)
ws.update('E5', jans)
