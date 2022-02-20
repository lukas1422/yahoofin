from bs4 import BeautifulSoup
from urllib.request import Request, urlopen
import re
import json
import pandas as pd

# this method does not return
from helperMethods import convertHK


def scrapeTotalSharesXueqiu(comp):
    if comp.endswith('HK'):
        comp = comp[:-3].zfill(5)
    comp = comp.replace('-', '.')

    # print('scrapeSharesOutstandingXueqiu', comp)
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
                if 'total_shares' in dic and dic['total_shares'] is not None and \
                        dic['total_shares'] != "null":
                    print("xueqiu total shares:", str(round(dic['total_shares'] / 1000000000, 2)) + "B")
                    return float(dic['total_shares'])
                    # return str(float(dic['total_shares']) / 1000000000) + "B"
    except Exception as e:
        print(comp, e)
        return 0
    else:
        return 0


def scrapeFloatingSharesXueqiu(comp):
    if comp.endswith('HK'):
        comp = comp[:-3].zfill(5)
    comp = comp.replace('-', '.')

    #print('scrapeSharesOutstandingXueqiu', comp)
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
                if 'float_shares' in dic and dic['float_shares'] is not None and \
                        dic['float_shares'] != "null":
                    return float(dic['float_shares'])
    except Exception as e:
        print(comp, e)
        # raise Exception(comp, "reraising", e)
        return "scrape xueqiu error"
    else:
        return "scrape xueqiu none"


def scrapeSharesOutstandingFinviz(comp):
    try:
        url = 'https://finviz.com/quote.ashx?t=' + comp + '&p=m&tas=0'
        req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        webpage = urlopen(req).read()
        soup = BeautifulSoup(webpage, "html.parser")

        for tb in soup.find_all('table', {"class": "snapshot-table2"}):
            for td in tb.find_all('td', text=re.compile('.*Shs Outstand.*')):
                return td.nextSibling.getText()
    except:
        return 0

#
# stock_df = pd.read_csv('list_redo', dtype=object, sep=" ", index_col=False, names=['ticker', 'name'])
# stock_df['ticker'] = stock_df['ticker'].astype(str)
# # HK Version ENDS
#
# listStocks = stock_df['ticker'].map(lambda x: convertHK(x)).tolist()
#
# print(len(listStocks), listStocks)
#
# for comp in listStocks:
#
#     try:
#         xueqiu = scrapeTotalSharesXueqiu(comp)
#         outputString = comp + " " + str(xueqiu)
#
#         print(outputString)
#         fileOutput.write(outputString + '\n')
#         fileOutput.flush()
#
#     except Exception as e:
#         print(comp, "exception", e)
