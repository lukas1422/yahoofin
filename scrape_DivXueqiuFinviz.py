import concurrent.futures

from bs4 import BeautifulSoup
from urllib.request import Request, urlopen
import re
import json
from concurrent.futures import ProcessPoolExecutor, as_completed
import pandas as pd


def scrapeDivXueqiu(comp):
    url = "https://xueqiu.com/S/" + comp
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    webpage = urlopen(req).read()
    soup = BeautifulSoup(webpage, "html.parser")

    for a in soup.find_all('script'):
        if a.getText().startswith('window.STOCK_PAGE'):
            searchText = (a.getText())
            pattern = re.compile(r"quote:\s+({.*?})")
            dic = json.loads(pattern.search(searchText).group(1) + "}")
            # print(comp, 'dividend_yield' in dic, dic)
            # print(comp, dic)
            if 'dividend_yield' in dic and dic['dividend_yield'] is not None and \
                    dic['dividend_yield'] != "null":
                return dic['dividend_yield']
    return "0"


def scrapeDivFinviz(comp):
    url = 'https://finviz.com/quote.ashx?t=' + comp + '&p=m&tas=0'
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    webpage = urlopen(req).read()
    soup = BeautifulSoup(webpage, "html.parser")

    for tb in soup.find_all('table', {"class": "snapshot-table2"}):
        for td in tb.find_all('td', text=re.compile('.*Dividend %.*')):
            return td.nextSibling.getText()
    return ""


COUNT = 0


def increment():
    global COUNT
    COUNT = COUNT + 1
    return COUNT


START_DATE = '3/1/2020'
DIVIDEND_START_DATE = '1/1/2010'
PRICE_INTERVAL = '1mo'

fileOutput = open('list_divYieldXueqiu', 'w')

stock_df = pd.read_csv('list_companyInfo', sep="\t", index_col=False,
                       names=['ticker', 'name', 'sector', 'industry', 'country', 'mv', 'price'])

listStocks = stock_df[(stock_df['price'] > 1)]['ticker'].tolist()

# print(listStocks.__len__(), listStocks)

with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
    for comp, futures in [(comp, executor.submit(scrapeDivXueqiu, comp)) for comp in listStocks]:
        try:
            data = futures.result(5)
        except Exception as e:
            print(e)
        else:
            print(comp, data)
            fileOutput.write(comp + " " + data + '\n')
            fileOutput.flush()

# for comp in listStocks:
#     print(increment())
#     try:
#         xueqiu = scrapeDivXueqiu(comp)
#         finviz = scrapeDivFinviz(comp)
#
#         outputString = comp + " " \
#                        + stock_df[stock_df['ticker'] == 'M'][['country', 'sector']] \
#                            .to_string(index=False, header=False) + " " \
#                        + " xueqiu:" + str(xueqiu) \
#                        + " finviz:" + str(finviz)
#
#         print(outputString)
#         fileOutput.write(outputString + '\n')
#         fileOutput.flush()
#
#     except Exception as e:
#         print(comp, "exception", e)
