fileOutput = open('list_industrials', 'w')

from bs4 import BeautifulSoup
from urllib.request import Request, urlopen


def getUSTickers():
    numStocks = 8700
    lastIndex = 1

    resultDict = {}

    for i in range(1, numStocks, 20):

        # urlToScrape = 'https://finviz.com/screener.ashx?v=111&r=' + str(i)
        urlToScrape = 'https://finviz.com/screener.ashx?v=121&f=sec_industrials&o=pb&r=' + str(i)

        req = Request(urlToScrape, headers={'User-Agent': 'Mozilla/5.0'})
        webpage = urlopen(req).read()
        soup = BeautifulSoup(webpage, "html.parser")
        tBody = soup.find('div', {"id": "screener-content"})

        for tr in tBody.find_all('tr', {'valign': 'top'}):
            index = tr.find_all('a')[0].get_text(strip=True)
            ticker = tr.find_all('a')[1].get_text(strip=True)
            marketCap = tr.find_all('a')[2].get_text(strip=True)
            pe = tr.find_all('a')[3].get_text(strip=True)
            forwardPE = tr.find_all('a')[4].get_text(strip=True)
            peg = tr.find_all('a')[5].get_text(strip=True)
            ps = tr.find_all('a')[6].get_text(strip=True)
            pb = tr.find_all('a')[7].get_text(strip=True)
            pc = tr.find_all('a')[8].get_text(strip=True)

            # print('index:',index,'ticker', ticker,'cap', marketCap
            #       ,'pe', pe,'fwdPE', forwardPE,'peg', peg,'ps', ps,'pb', pb,'pc', pc)

            if ps == '-' or pb == '-':
                continue

            pspb = round(float(ps) * float(pb) * 10000)
            print('index:', index, 'ticker', ticker, 'ps', ps, 'pb', pb, 'pspb',
                  pspb)

            resultDict[ticker] = pspb

            if index == lastIndex:
                break


            # print(index, ticker, marketCap.replace(" ", "_"), pb.replace(" ", "_")
            #       , forwardPE.replace(" ", "_"), peg.replace(" ", "_"), ps, pb, pc)

            fileOutput.write(ticker + " " + str(pb) + " " + str(ps) + " " + str(pspb) + '\n')


            fileOutput.flush()
            lastIndex = index
        else:
            continue
        break


getUSTickers()
