from bs4 import BeautifulSoup
from urllib.request import Request, urlopen
import re
import pandas as pd

fileOutput = open('list_HK_Tickers', 'w')

for i in range(1, 11):
    url = 'https://stock360.hkej.com/stockList/all/20220211?&p=' + str(i)
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    webpage = urlopen(req).read()
    soup = BeautifulSoup(webpage, "html.parser")

    for td in soup.find_all('td', {"align": "center"}):
        outputString = td.getText() + " " + td.nextSibling.getText()
        try:
            print(outputString)
            fileOutput.write(outputString + '\n')
            fileOutput.flush()

        except Exception as e:
            print("exception", e)
