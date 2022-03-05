from bs4 import BeautifulSoup
from urllib.request import Request, urlopen
import re
import json
import pandas as pd

from Market import Market
from helperMethods import convertHK


def scrapeDivXueqiu(comp):
    try:
        comp1 = comp[:-3].zfill(5) if comp.endswith('HK') else comp
        # if comp.endswith('HK'):
        #     comp1 = comp[:-3].zfill(5)
        # #comp1 = comp.replace('-', '.')

        url = "https://xueqiu.com/S/" + comp1
        print(url)
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


# def scrapeDivFinviz(comp):
#     url = 'https://finviz.com/quote.ashx?t=' + comp + '&p=m&tas=0'
#     req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
#     webpage = urlopen(req).read()
#     soup = BeautifulSoup(webpage, "html.parser")
#
#     for tb in soup.find_all('table', {"class": "snapshot-table2"}):
#         for td in tb.find_all('td', text=re.compile('.*Dividend %.*')):
#             return td.nextSibling.getText()
#     return ""


COUNT = 0

MARKET = Market.HK


def increment():
    global COUNT
    COUNT = COUNT + 1
    return COUNT

def scrapeDivYieldsXueqiu(MARKET):

    if MARKET == Market.US:

        fileOutput = open('list_divYieldXueqiuUS', 'w')

        stock_df = pd.read_csv('list_US_Tickers', sep=" ", index_col=False,
                               names=['ticker', 'name', 'sector', 'industry', 'country', 'mv', 'price'])

        listStocks = stock_df[(stock_df['price'] > 1)]['ticker'].tolist()

    elif MARKET == Market.HK:
        fileOutput = open('list_divYieldXueqiuHK', 'w')
        stock_df = pd.read_csv('list_HK_Tickers', dtype=object, sep=" ", index_col=False, names=['ticker', 'name'])
        stock_df['ticker'] = stock_df['ticker'].astype(str)
        listStocks = stock_df['ticker'].map(lambda x: convertHK(x)).tolist()

    else:
        raise Exception("market not found")

    print(listStocks)

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
