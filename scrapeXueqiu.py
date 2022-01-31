from bs4 import BeautifulSoup
from urllib.request import Request, urlopen

with open("usTickerAll", "r") as file:
    lines = file.read().rstrip().splitlines()

fileOutput = open('tickerPB', 'w')

for comp in lines:
    try:
        url = "https://xueqiu.com/S/" + comp
        req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        webpage = urlopen(req).read()
        soup = BeautifulSoup(webpage, "html.parser")

        for a in soup.find_all('td'):
            if a.getText().startswith("市净率"):
                print(comp, a.getText(), a.find('span').getText())
                fileOutput.write(comp + " " + a.find('span').getText() + '\n')
                fileOutput.flush()
    except Exception as e:
        print('exception occurred', e)
