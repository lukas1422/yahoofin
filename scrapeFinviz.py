# #https://finviz.com/screener.ashx?v=121&f=sec_industrials&o=pb&r=381
#
#
# from bs4 import BeautifulSoup
# from urllib.request import urlopen
#

########

import pandas as pd
import numpy as np
from bs4 import BeautifulSoup as soup
from urllib.request import Request, urlopen

url = "http://finviz.com/screener.ashx?v=121&f=sec_industrials&o=pb&r=381"
req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
webpage = urlopen(req).read()
html = soup(webpage, "html.parser")
print(html.prettify())
#list(html.children)
#page = urlopen(url)
#html = page.read().decode("utf-8")
#soup = BeautifulSoup(html, "html.parser")

#
# pd.set_option('display.max_colwidth', 25)
#
# # Input
# symbol = input('Enter a ticker: ')
# print ('Getting data for ' + symbol + '...\n')
#
# # Set up scraper
# url = ("http://finviz.com/quote.ashx?t=" + symbol.lower())
# req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
# webpage = urlopen(req).read()
# html = soup(webpage, "html.parser")