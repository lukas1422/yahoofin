from bs4 import BeautifulSoup
from urllib.request import Request, urlopen
import concurrent.futures
import atexit

with open("usTickerAll", "r") as file:
    lines = file.read().rstrip().splitlines()

MAX_THREADS = 30

companyList = []

tickerPBDict = {}

fileOutput = open('test', 'w')

NUMBER_PROCESSED = 0


def exit_handler():
    for comp in tickerPBDict.keys():
        fileOutput.write(comp + " " + data + "\n")
    fileOutput.flush()
    print('My application is ending!')


atexit.register(exit_handler)


def increment():
    global NUMBER_PROCESSED
    NUMBER_PROCESSED = NUMBER_PROCESSED + 1


def processFunction(comp):
    url = makeURL(comp)
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    webpage = urlopen(req).read()
    soup = BeautifulSoup(webpage, "html.parser")

    for a in soup.find_all('td'):
        if a.getText().startswith("市净率"):
            increment()
            pb = a.find('span').getText()
            print(NUMBER_PROCESSED, " processed ", comp, pb)
            tickerPBDict[comp] = pb
            return pb
            # return comp + " " + a.find('span').getText()


def makeURL(compName):
    return "https://xueqiu.com/S/" + compName


######### MAIN ############
for comp in lines:
    companyList.append(comp)

with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
    compToPBFuture = {executor.submit(processFunction, comp): comp for comp in companyList}

    for future in concurrent.futures.as_completed(compToPBFuture):
        try:
            comp = compToPBFuture[future]
            data = future.result(timeout=100)
        except Exception as e:
            print("exception ", comp, e)
        # else:
        #     tickerPBDict[comp] = data

for comp in tickerPBDict.keys():
    fileOutput.write(comp + " " + data + "\n")

fileOutput.flush()
