from bs4 import BeautifulSoup
from urllib.request import Request, urlopen
import re


def getListingCurrency(ticker):
    pattern = re.compile(r"Currency in\s+([A-Z]{3})")
    try:
        url = "https://finance.yahoo.com/quote/" + ticker + "?p=" + ticker
        req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        webpage = urlopen(req).read()
        soup = BeautifulSoup(webpage, "html.parser")
        for a in soup.find_all('span'):
            if (a.getText().__contains__("Currency in")):
                return pattern.search(a.getText()).group(1)

        return ('not found')

    except Exception as e:
        print("getListingCurrency exception is  ", e)
        raise Exception(ticker, e)


def getBalanceSheetCurrency(ticker, default):
    pattern = re.compile(r"Currency in\s+([A-Z]{3})")
    try:
        type = "balance-sheet"
        req = Request(yahooBalanceSheetURLMaker(ticker, type), headers={'User-Agent': 'Mozilla/5.0'})
        webpage = urlopen(req).read()
        soup = BeautifulSoup(webpage, "html.parser")
        for a in soup.find_all('span'):
            if (a.getText().startswith("Currency in")):
                return pattern.search(a.getText()).group(1)

        return default

        # return "USD"

    except Exception as e:
        print("exception is  ", e)


def yahooBalanceSheetURLMaker(ticker, type):
    return "https://finance.yahoo.com/quote/" + ticker + "/" + type + "?p=" + ticker
