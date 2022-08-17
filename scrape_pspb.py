fileOutput = open('list_us_pspb', 'w')

from bs4 import BeautifulSoup
from urllib.request import Request, urlopen

numStocks = 8700
lastIndex = 1

for i in range(1, numStocks, 20):
    urlToScrape = 'https://finviz.com/screener.ashx?v=121&o=pb&r=' + str(i)
    print(urlToScrape)

    req = Request(urlToScrape, headers={'User-Agent': 'Mozilla/5.0'})
    webpage = urlopen(req).read()
    soup = BeautifulSoup(webpage, "html.parser")
    tBody = soup.find('div', {"id": "screener-content"})

    for tr in tBody.find_all('tr', {'valign': 'top'}):
        index = tr.find_all('a')[0].get_text(strip=True)
        ticker = tr.find_all('a')[1].get_text(strip=True)
        # s2 = tr.find_all('a')[2].get_text(strip=True)
        # s3 = tr.find_all('a')[3].get_text(strip=True)
        # s4 = tr.find_all('a')[4].get_text(strip=True)
        # s5 = tr.find_all('a')[5].get_text(strip=True)
        s6 = tr.find_all('a')[6].get_text(strip=True)
        s7 = tr.find_all('a')[7].get_text(strip=True)

        res = 0
        if s6 != '-' and s7 != '-':
            res = float(s6) * float(s7) * 10000

        print(index, ticker, int(res))

        if index == lastIndex:
            break

        fileOutput.write(index + " " + ticker + " " + str(res) + '\n')
        fileOutput.flush()
        lastIndex = index

    else:
        continue
    break
