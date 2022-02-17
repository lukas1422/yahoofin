from bs4 import BeautifulSoup
from urllib.request import Request, urlopen
import re
import json
import pandas as pd


def scrapeDivXueqiu(comp):
    try:
        url = "https://xueqiu.com/S/" + comp
        req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        webpage = urlopen(req, timeout=5).read()
        soup = BeautifulSoup(webpage, "html.parser")

        for a in soup.find_all('script'):
            if a.getText().startswith('window.STOCK_PAGE'):
                searchText = (a.getText())
                pattern = re.compile(r"quote:\s+({.*?})")
                dic = json.loads(pattern.search(searchText).group(1) + "}")
                if 'dividend_yield' in dic and dic['dividend_yield'] is not None and \
                        dic['dividend_yield'] != "null":
                    return dic['dividend_yield']
    except Exception as e:
        print(comp, e)
        return "error"
    else:
        return "none"


COUNT = 0


def increment():
    global COUNT
    COUNT = COUNT + 1
    return COUNT


fileOutput = open('list_divYieldXueqiuUS', 'w')

stock_df = pd.read_csv('list_UScompanyInfo', sep="\t", index_col=False,
                       names=['ticker', 'name', 'sector', 'industry', 'country', 'mv', 'price'])

listStocks = stock_df[(stock_df['price'] > 1)]['ticker'].tolist()

for comp in listStocks:
    print(increment())
    try:
        xueqiu = scrapeDivXueqiu(comp)
        outputString = comp + " " + str(xueqiu)

        print(outputString)
        fileOutput.write(outputString + '\n')
        fileOutput.flush()

    except Exception as e:
        print(comp, "exception", e)
