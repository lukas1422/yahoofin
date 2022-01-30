fileOutput = open('tickerList', 'w')

from bs4 import BeautifulSoup
from urllib.request import Request, urlopen

stockNum = 8700
# https://xueqiu.com/S/SKM
# url = "http://finviz.com/screener.ashx?v=121&f=sec_industrials&o=pb&r=" + str(stockNum)
# url = "https://finviz.com/screener.ashx?v=121&o=pb&r=" + str(stockNum)
# req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
# webpage = urlopen(req).read()
# soup = BeautifulSoup(webpage, "html.parser")

url = "https://xueqiu.com/S/SKM"
req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
webpage = urlopen(req).read()
soup = BeautifulSoup(webpage, "html.parser")

for a in soup.find_all('td'):
    if a.getText().startswith("市净率"):
        print(a.find('span').getText())

