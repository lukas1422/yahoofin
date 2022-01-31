from bs4 import BeautifulSoup
from urllib.request import Request, urlopen
import concurrent.futures

with open("usTickerAll", "r") as file:
    lines = file.read().rstrip().splitlines()

MAX_THREADS = 30

urlList = []
urlDict = {}
tickerPBDict = {}

fileOutput = open('test', 'w')


def processFunction(url):
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    webpage = urlopen(req).read()
    soup = BeautifulSoup(webpage, "html.parser")

    for a in soup.find_all('td'):
        if a.getText().startswith("市净率"):
            # print(" processed ", comp, a.find('span').getText())
            return comp + " " + a.find('span').getText()


######### MAIN ############
for comp in lines:
    # urlDict[comp] = "https://xueqiu.com/S/" + comp
    urlList.append("https://xueqiu.com/S/" + comp)

with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
    future_to_pb = [executor.submit(processFunction, url) for url in urlList]

    for future in concurrent.futures.as_completed(future_to_pb):
        try:
            data = future.result()
        except Exception as e:
            print("exception ", e)
        else:
            fileOutput.write(data + "\n")
            fileOutput.flush()
