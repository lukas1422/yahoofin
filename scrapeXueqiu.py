from bs4 import BeautifulSoup
from urllib.request import Request, urlopen

url = "https://xueqiu.com/S/PDD"
req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
webpage = urlopen(req).read()
soup = BeautifulSoup(webpage, "html.parser")

for a in soup.find_all('td'):
    if a.getText().startswith("市净率"):
        print(a.find('span').getText())
