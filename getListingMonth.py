import yahoo_fin.stock_info as si
import pandas as pd

COUNT = 0


def increment():
    global COUNT
    COUNT = COUNT + 1
    return COUNT


START_DATE = '1/1/1970'
PRICE_INTERVAL = '1mo'

fileOutput = open('list_listingDate', 'w')

stock_df = pd.read_csv('list_UScompanyInfo', sep="\t", index_col=False,
                       names=['ticker', 'name', 'sector', 'industry', 'country', 'mv', 'price'])

listStocks = stock_df['ticker'].tolist()

print(len(listStocks), listStocks)

for comp in listStocks:
    print(increment())
    try:
        data = si.get_data(comp, start_date='3/1/1970', interval='1mo')
        outputString = comp + " " + data.index[0].strftime('%Y-%m-%d')
        print(outputString)
        fileOutput.write(outputString + '\n')
        fileOutput.flush()
    except Exception as e:
        print(comp, "exception", e)
