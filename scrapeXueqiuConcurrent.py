from bs4 import BeautifulSoup
from urllib.request import Request, urlopen
import concurrent.futures

with open("usTickerAll", "r") as file:
    lines = file.read().rstrip().splitlines()

MAX_THREADS = 30

companyList = []
# urlDict = {}
tickerPBDict = {}

fileOutput = open('test', 'w')

numberProcessed = 0


def increment():
    global numberProcessed
    numberProcessed = numberProcessed + 1


def processFunction(comp, url):
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    webpage = urlopen(req).read()
    soup = BeautifulSoup(webpage, "html.parser")

    for a in soup.find_all('td'):
        if a.getText().startswith("市净率"):
            increment()
            print(numberProcessed, " processed ", comp, a.find('span').getText())
            return a.find('span').getText()
            # return comp + " " + a.find('span').getText()

def makeURL(compName):
    return "https://xueqiu.com/S/" + compName


######### MAIN ############
for comp in lines:
    companyList.append(comp)
    # urlDict[comp] = "https://xueqiu.com/S/" + comp
    # urlList.append("https://xueqiu.com/S/" + comp)

# print("printing URLLIST",urlList)

with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
    compToPBFuture = {executor.submit(processFunction, comp, makeURL(comp)): comp for comp in companyList}

    for future in concurrent.futures.as_completed(compToPBFuture):
        try:
            comp = compToPBFuture[future]
            data = future.result()
        except Exception as e:
            print("exception ", comp, e)
        else:
            tickerPBDict[comp] = data
            # fileOutput.write(comp + " " + data + "\n")
            # fileOutput.flush()

for comp in tickerPBDict.keys():
    fileOutput.write(comp + " " + data + "\n")

fileOutput.flush()
