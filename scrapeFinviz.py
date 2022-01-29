# #https://finviz.com/screener.ashx?v=121&f=sec_industrials&o=pb&r=381
#
#
# from bs4 import BeautifulSoup
# from urllib.request import urlopen
#

########

import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
from urllib.request import Request, urlopen

stockNum = 700
url = "http://finviz.com/screener.ashx?v=121&f=sec_industrials&o=pb&r=" + str(stockNum)
req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
webpage = urlopen(req).read()
soup = BeautifulSoup(webpage, "html.parser")
# print(soup.prettify())
# ab = soup.find_all('a',attrs={"class":"screener-link-primary"})
# for link in ab:
#     print(link.get_text(strip=True))


for i in range(1, stockNum, 20):
   url = "http://finviz.com/screener.ashx?v=121&f=sec_industrials&o=pb&r=" + str(i)
   req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
   webpage = urlopen(req).read()
   soup = BeautifulSoup(webpage, "html.parser")
   tBody = soup.find('div', attrs={"id": "screener-content"})
   for tr in tBody.find_all('tr', attrs={'class': ["table-dark-row-cp", "table-light-row-cp"]}):
       print(tr.find_all('td')[0].get_text(strip=True), tr.find_all('td')[1].get_text(strip=True))
