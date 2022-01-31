from bs4 import BeautifulSoup
import urllib
from urllib.request import Request, urlopen
import concurrent.futures
import atexit

with open("usTickerAll", "r") as file:
    lines = file.read().rstrip().splitlines()

MAX_THREADS = 30

companyList = []

doneDict = {}

tickerPBDict = {}

fileOutput = open('test', 'w')

NUMBER_PROCESSED = 0


def exit_handler():
    for comp in tickerPBDict.keys():
        fileOutput.write(comp + " " + data + "\n")

    print("not done: ", dict(filter(lambda e: e[1] == False, doneDict.items())))
    # fileOutput.flush()
    print('My application is ending!')


atexit.register(exit_handler)


def increment():
    global NUMBER_PROCESSED
    NUMBER_PROCESSED = NUMBER_PROCESSED + 1


def processFunction(comp):
    increment()
    url = makeURL(comp)
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})

    try:
        webpage = urlopen(req).read()
        soup = BeautifulSoup(webpage, "html.parser")

        for a in soup.find_all('td'):
            if a.getText().startswith("市净率"):
                pb = a.find('span').getText()
                # print(NUMBER_PROCESSED, " processed ", comp, pb)
                tickerPBDict[comp] = pb
                return pb
            else:
                return "pb not found"
    except urllib.error.HTTPError:
        return "stock not found"


def makeURL(compName):
    return "https://xueqiu.com/S/" + compName


######### MAIN ############
for comp in lines:
    companyList.append(comp)
    doneDict[comp] = False

with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    compToPBFuture = {executor.submit(processFunction, comp): comp for comp in companyList}

    for future in concurrent.futures.as_completed(compToPBFuture):
        try:
            comp = compToPBFuture[future]
            print("trying comp ", comp)
            data = future.result(timeout=10)
            doneDict[comp] = True
            print(NUMBER_PROCESSED, "comp completed ", comp, data)
            fileOutput.write(comp + " " + data + "\n")

        except Exception as e:
            print("exception ", comp, e)

for comp in tickerPBDict.keys():
    fileOutput.write(comp + " " + tickerPBDict[comp] + "\n")

fileOutput.flush()
