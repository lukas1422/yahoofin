from bs4 import BeautifulSoup
from urllib.request import Request, urlopen
import re


def scrapeSharesOutstandingXueqiu(comp):
    url = "https://xueqiu.com/S/" + comp
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    webpage = urlopen(req).read()
    soup = BeautifulSoup(webpage, "html.parser")

    for a in soup.find_all('td'):
        if a.getText().startswith("总股本"):
            print(comp, a.getText(), a.find('span').getText())
            # fileOutput.write(comp + " " + a.find('span').getText() + '\n')
            # fileOutput.flush()


def scrapeSharesOutstandingFinviz(comp):
    url = 'https://finviz.com/quote.ashx?t=' + comp + '&p=m&tas=0'
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    webpage = urlopen(req).read()
    soup = BeautifulSoup(webpage, "html.parser")

    for tb in soup.find_all('table', {"class": "snapshot-table2"}):
        for td in tb.find_all('td', text=re.compile('.*Shs Outstand.*')):
            return td.nextSibling


# scrapeSharesOutstandingXueqiu('sndr')
# scrapeSharesOutstandingFinviz('sndr')
