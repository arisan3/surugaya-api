import gspread
from google.oauth2.service_account import Credentials
import requests
from bs4 import BeautifulSoup
import time

# 認証情報
JSON_PATH = 'totemic-creek-306512-640467f70542.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
creds = Credentials.from_service_account_file(JSON_PATH, scopes=SCOPES)
gc = gspread.authorize(creds)

# スプレッドシート情報
SPREADSHEET_ID = '1QtWsWnKMdC9882a-_9XWDsGyp4b-LPyK0aVZDlvcpfs'
SHEET_NAME = '駿河屋リサーチ'
ws = gc.open_by_key(SPREADSHEET_ID).worksheet(SHEET_NAME)

# キーワード取得（A列）
keywords = ws.col_values(1)[4:]  # A5:A

all_titles = []
all_urls = []
all_jans = []

def get_search_results(keyword, max_count=20):
    url = f'https://www.suruga-ya.jp/search?category=&search_word={requests.utils.quote(keyword)}&searchbox=1'
    res = requests.get(url, timeout=10)
    soup = BeautifulSoup(res.content, 'html.parser')
    results = []

    # 商品ブロック取得
    items = soup.select('div.item_detail')[:max_count]
    for item in items:
        title_ja = item.select_one('h3.product-name')
        if title_ja:
            title_ja = title_ja.get_text(strip=True)
        else:
            continue
        a_tag = item.select_one('a[href*="/product/detail/"]')
        url = f'https://www.suruga-ya.jp{a_tag["href"]}' if a_tag else ''
        results.append((title_ja, url))
    return results

def get_jan_code(product_url):
    try:
        res = requests.get(product_url, timeout=10)
        soup = BeautifulSoup(res.content, 'html.parser')
        tds = soup.select('td')
        for td in tds:
            jan = td.get_text(strip=True)
            if len(jan) == 13 and jan.isdigit():
                return jan
        return ''
    except:
        return ''

for i, keyword in enumerate(keywords):
    if not keyword.strip():
        continue
    print(f"{i+1}件目:「{keyword}」検索中…")
    results = get_search_results(keyword, max_count=20)
    if not results:
        all_titles.append(['該当商品なし'])
        all_urls.append([''])
        all_jans.append([''])
        continue
    for title, url in results:
        all_titles.append([title])
        all_urls.append([f'=HYPERLINK("{url}", "{url}")'])
        jan = get_jan_code(url)
        all_jans.append([jan])
        time.sleep(1.2)
print("全て完了！")

# 書き込み
ws.update('B5:B{}'.format(4+len(all_titles)), all_titles)
ws.update('D5:D{}'.format(4+len(all_urls)), all_urls)
ws.update('E5:E{}'.format(4+len(all_jans)), all_jans)
