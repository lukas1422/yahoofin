fileOutput = open('list_finvizTickerPB', 'w')

from bs4 import BeautifulSoup
from urllib.request import Request, urlopen

stockNum = 8700

for i in range(1, stockNum, 20):
    url = "https://finviz.com/screener.ashx?v=111&o=pb&r=" + str(i)

    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    webpage = urlopen(req).read()
    soup = BeautifulSoup(webpage, "html.parser")
    tBody = soup.find('div', {"id": "screener-content"})

    for tr in tBody.find_all('tr', {'valign': 'top'}):
        index = tr.find_all('a')[0].get_text(strip=True)
        price = tr.find_all('a')[8].get_text(strip=True)
        ticker = tr.find_all('a', {'class': 'screener-link-primary'})[0].get_text(strip=True)

        print(index, ticker, price)
        if float(price) > 1:
            fileOutput.write(str(ticker) + "\n")
            fileOutput.flush()
        else:
            print('price < 1', ticker, price)
