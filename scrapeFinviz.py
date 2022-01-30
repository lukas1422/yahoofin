fileOutput = open('tickerList', 'w')

from bs4 import BeautifulSoup
from urllib.request import Request, urlopen

stockNum = 700
url = "http://finviz.com/screener.ashx?v=121&f=sec_industrials&o=pb&r=" + str(stockNum)
req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
webpage = urlopen(req).read()
soup = BeautifulSoup(webpage, "html.parser")

last = 0

for i in range(1, stockNum, 20):
    url = "http://finviz.com/screener.ashx?v=121&f=sec_industrials&o=pb&r=" + str(i)
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    webpage = urlopen(req).read()
    soup = BeautifulSoup(webpage, "html.parser")
    tBody = soup.find('div', attrs={"id": "screener-content"})

    for tr in tBody.find_all('tr', attrs={'class': ["table-dark-row-cp", "table-light-row-cp"]}):
        index = tr.find_all('td')[0].get_text(strip=True)
        value = tr.find_all('td')[1].get_text(strip=True)
        pb = tr.find_all('td')[7].get_text(strip=True)
        print("index", index, "value", value, pb, "pb")
        if index == last:
            break
        else:
            print(index, value)
            last = index
            #print("last", last)
            fileOutput.write(str(value) + "\n")
            fileOutput.flush()
