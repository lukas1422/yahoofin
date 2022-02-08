from bs4 import BeautifulSoup
from urllib.request import Request, urlopen
import re
import pandas as pd


def scrapeDivFinviz(comp):
    url = 'https://finviz.com/quote.ashx?t=' + comp + '&p=m&tas=0'
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    webpage = urlopen(req).read()
    soup = BeautifulSoup(webpage, "html.parser")

    for tb in soup.find_all('table', {"class": "snapshot-table2"}):
        for td in tb.find_all('td', text=re.compile('.*Insider Own.*')):
            return td.nextSibling.getText()
    return ""


COUNT = 0


def increment():
    global COUNT
    COUNT = COUNT + 1
    return COUNT


fileOutput = open('list_insiderOwnership_finviz', 'w')

stock_df = pd.read_csv('list_companyInfo', sep="\t", index_col=False,
                       names=['ticker', 'name', 'sector', 'industry', 'country', 'mv', 'price'])

listStocks = stock_df[(stock_df['price'] > 1)]['ticker'].tolist()

for comp in listStocks:
    print(increment())
    try:
        finviz = scrapeDivFinviz(comp)

        outputString = comp + " " + str(finviz)

        print(outputString)
        fileOutput.write(outputString + '\n')
        fileOutput.flush()

    except Exception as e:
        print(comp, "exception", e)
