from bs4 import BeautifulSoup
from urllib.request import Request, urlopen
import re
import json
# with open("usTickerAll", "r") as file:
#     lines = file.read().rstrip().splitlines()

fileOutput = open('tickerPB', 'w')

# for comp in lines:
comp = "PKX"

try:
    url = "https://xueqiu.com/S/" + comp
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    webpage = urlopen(req).read()
    soup = BeautifulSoup(webpage, "html.parser")
    res = soup.find_all('script')

    for a in soup.find_all('script'):
        if (a.getText().startswith('window.STOCK_PAGE')):
            searchText = (a.getText())
            pattern = re.compile(r"quote:\s+(\{.*?\})")
            dic = json.loads(pattern.search(searchText).group(1) + "}")
            print(dic['currency'])

except Exception as e:
    print('exception occurred', e)
