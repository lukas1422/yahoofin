from bs4 import BeautifulSoup
import urllib.error
from urllib.request import Request, urlopen
import concurrent.futures

fileOutput = open('testFile', 'w')

with open("list_usTickerAll", "r") as file:
    lines = file.read().rstrip().splitlines()

MAX_THREADS = 30

companyList = []

tickerPBDict = {}


def processFunction(comp):
    url = makeURL(comp)
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})

    try:
        webpage = urlopen(req).read()
        soup = BeautifulSoup(webpage, "html.parser")

        for a in soup.find_all('td'):
            if a.getText().startswith("市净率"):
                pb = a.find('span').getText()
                return pb

        return "pb_not_found"
    except urllib.error.HTTPError:
        print(comp, "urllib.error.HTTPerror")
        return "stock_not_found"
    except Exception as e:
        print(comp, e, "other errors")
        return "other errors"


def makeURL(compName):
    return "https://xueqiu.com/S/" + compName.replace("-", ".")


######### MAIN ############
for comp in lines:
    companyList.append(comp)

with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
    for comp, future in [(comp, executor.submit(processFunction, comp)) for comp in companyList]:
        print(comp)
        try:
            data = future.result(5)
            fileOutput.write(comp + " " + data + "\n")
            fileOutput.flush()
        except TimeoutError as te:
            print(comp, "time out ")
        except Exception as e:
            print("exception in futures ", e, comp)

        tickerPBDict[comp] = data

    print("we are here")