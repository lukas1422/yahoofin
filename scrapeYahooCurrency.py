from bs4 import BeautifulSoup
from urllib.request import Request, urlopen


def yahooBalanceSheetURLMaker(ticker, type):
    return "https://finance.yahoo.com/quote/" + ticker + "/" + type + "?p=" + ticker


try:
    comp = "PDD"
    type = "history"
    req = Request(yahooBalanceSheetURLMaker(comp, type), headers={'User-Agent': 'Mozilla/5.0'})
    webpage = urlopen(req).read()
    soup = BeautifulSoup(webpage, "html.parser")
    for a in soup.find_all('span'):
        if (a.getText().startswith("Currency in")):
            print(comp, type, a.getText())

    # print(soup)
except Exception as e:
    print("exception is  ", e)
