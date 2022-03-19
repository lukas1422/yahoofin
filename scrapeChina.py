from bs4 import BeautifulSoup
from urllib.request import Request, urlopen
import re
import pandas as pd

fileOutput = open('list_chinaTickers2', 'w')

# url = 'https://app.finance.ifeng.com/list/stock.php?t=hs&f=chg_pct&o=desc&p=93'
# req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
# webpage = urlopen(req).read()
# soup = BeautifulSoup(webpage, "html.parser")

PAGES = 94

# for a in soup.find_all('a', {'href':re.compile('.*finance.*')}):
#      print(a)

for i in range(1, PAGES):
    print(i)
    url = "https://app.finance.ifeng.com/list/stock.php?t=hs&f=chg_pct&o=desc&p=" + str(i)

    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    webpage = urlopen(req).read()
    soup = BeautifulSoup(webpage, "html.parser")
    tBody = soup.find('div', {"id": "screener-content"})
    for tr in soup.find_all('tr'):
        tdList = tr.findAll('td')
        if len(tdList) > 1:
            ticker = tdList[0].getText()
            name = tdList[1].getText()
            print(ticker, name)
            fileOutput.write(ticker + " " + name.replace(' ','') + '\n')
            fileOutput.flush()
    #
    # for tr in soup.find_all('tr'):
    #     a = tr.find('a', {'target': '_blank'})
    #     if a is not None:
    #         print(a.text)
