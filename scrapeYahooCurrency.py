from bs4 import BeautifulSoup
from urllib.request import Request, urlopen

url = "https://finance.yahoo.com/quote/0743.HK/financials?p=0743.HK"
url2 = "https://finance.yahoo.com/quote/baba/financials?p=baba"


def yahooFinancialURLMaker(ticker):
    return "https://finance.yahoo.com/quote/" + ticker + "/financials?p=" + ticker


# try:
# url = "https://xueqiu.com/S/" + comp
try:
    comp = "1024.HK"
    req = Request(yahooFinancialURLMaker(comp), headers={'User-Agent': 'Mozilla/5.0'})
    webpage = urlopen(req).read()
    soup = BeautifulSoup(webpage, "html.parser")
    for a in soup.find_all('span'):
        if (a.getText().startswith("Currency in")):
            print(comp, a.getText())

    # print(soup)
except Exception as e:
    print("exception is  ", e)
