fileOutput = open('newLowTopLoserList', 'w')

from bs4 import BeautifulSoup
from urllib.request import Request, urlopen


def finvizToFile(urlBase, numStocks):
    # last = 0
    for i in range(1, numStocks, 20):
        urlToScrape = urlBase + str(i)
        print("i url ", i, urlToScrape)

        req = Request(urlToScrape, headers={'User-Agent': 'Mozilla/5.0'})
        webpage = urlopen(req).read()
        soup = BeautifulSoup(webpage, "html.parser")
        tBody = soup.find('div', attrs={"id": "screener-content"})

        for tr in tBody.find_all('tr', attrs={'class': ["table-dark-row-cp", "table-light-row-cp"]}):
            index = tr.find_all('td')[0].get_text(strip=True)
            value = tr.find_all('td')[1].get_text(strip=True)
            # pb = tr.find_all('td')[7].get_text(strip=True)
            print("index", index, "value", value)
            # if index == last:
            #     break
            # else:
            print(index, value)
            # last = index
            fileOutput.write(str(value) + "\n")
            fileOutput.flush()


finvizToFile('https://finviz.com/screener.ashx?v=171&o=low52w&r=', 200)
finvizToFile('https://finviz.com/screener.ashx?v=111&o=change&r=', 200)
