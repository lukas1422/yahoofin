from bs4 import BeautifulSoup
from urllib.request import Request, urlopen
import re
import json
import pandas as pd
from helperMethods import convertHK


def scrapeSharesXueqiu(comp):
    try:
        comp1 = comp[:-3].zfill(5) if comp.endswith('HK') else comp

        url = "https://xueqiu.com/S/" + comp1
        print(url)
        req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        webpage = urlopen(req, timeout=5).read()
        soup = BeautifulSoup(webpage, "html.parser")

        for a in soup.find_all('script'):
            if a.getText().startswith('window.STOCK_PAGE'):
                searchText = a.getText()
                pattern = re.compile(r"quote:\s+({.*?})")
                dic = json.loads(pattern.search(searchText).group(1) + "}")
                if 'total_shares' in dic and dic['total_shares'] is not None and \
                        dic['total_shares'] != "null":
                    return dic['total_shares']
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


def scrapeSharesXueqiuAll():
    fileOutput = open('list_HK_totalShares_test', 'w')
    stock_df = pd.read_csv('list_HK_Tickers', dtype=object, sep=" ", index_col=False, names=['ticker', 'name'])
    stock_df['ticker'] = stock_df['ticker'].astype(str)
    listStocks = stock_df['ticker'].map(lambda x: convertHK(x)).tolist()

    for comp in listStocks:
        print(increment())
        try:
            xueqiu = scrapeSharesXueqiu(comp)
            outputString = comp + " " + str(xueqiu)
            print(outputString)
            fileOutput.write(outputString + '\n')
            fileOutput.flush()
        except Exception as e:
            print(comp, "exception", e)


def scrapeSharesXueqiuLoopAgainCorrectErrors():
    stock_df = pd.read_csv('list_HK_totalShares_test',
                           dtype=object, sep=" ", index_col=False, names=['ticker', 'shares'])
    stock_df['ticker'] = stock_df['ticker'].astype(str)
    errorDF = stock_df.loc[stock_df['shares'] == 'error']
    errorDic = dict(zip(errorDF.ticker, errorDF.shares))
    print(len(errorDic), errorDic)

    for comp in errorDic.keys():
        try:
            xueqiuShares = scrapeSharesXueqiu(comp)
            print(comp, xueqiuShares)
            if xueqiuShares != 'error':
                stock_df.loc[stock_df['ticker'] == comp, 'shares'] = xueqiuShares
        except Exception as e:
            print(comp, "exception", e)

    stock_df.to_csv('list_hk_totalShares_test2', header=None, index=None, sep=' ')


scrapeSharesXueqiuAll()
# scrapeSharesXueqiuLoopAgainCorrectErrors()
