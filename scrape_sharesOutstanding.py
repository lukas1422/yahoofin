from bs4 import BeautifulSoup
from urllib.request import Request, urlopen
import re
import json


# this method does not return
def scrapeSharesOutstandingXueqiu(comp):
    if comp.endswith('HK'):
        comp = comp[:-3].zfill(5)
    comp = comp.replace('-', '.')

    print('scrapeSharesOutstandingXueqiu', comp)
    url = "https://xueqiu.com/S/" + comp
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    webpage = urlopen(req).read()
    soup = BeautifulSoup(webpage, "html.parser")

    for a in soup.find_all('td'):
        if a.getText().startswith("总股本"):
            return a.find('span').getText()


def scrapeSharesOutstandingXueqiu2(comp):
    if comp.endswith('HK'):
        comp = comp[:-3].zfill(5)
    comp = comp.replace('-', '.')

    print('scrapeSharesOutstandingXueqiu', comp)
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
                    return str(float(dic['float_shares']) / 1000000000) + "B"
    except Exception as e:
        print(comp, e)
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
