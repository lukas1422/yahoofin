import yahoo_fin.stock_info as si
import pandas as pd


# comp ='RDBXW'
#
#
# START_DATE = '1/1/1970'
# PRICE_INTERVAL = '1d'
#
# data = si.get_data(comp, start_date=START_DATE, interval=PRICE_INTERVAL)
# outputString = comp + " " + data.index[0].strftime('%Y-%m-%d')
# print(outputString)
# print(data)

stock_df = pd.read_csv('list_US_companyInfo', sep=" ", index_col=False,
                       names=['ticker', 'name', 'sector', 'industry', 'country', 'mv', 'price','listingDate'])

stock_df['listingDate'] = pd.to_datetime(stock_df['listingDate'])

listStocks = stock_df[(stock_df['price'] > 1)
                      & (stock_df['sector'].str
                         .contains('financial|healthcare', regex=True, case=False) == False)
                      & (stock_df['listingDate'] < pd.to_datetime('2020-1-1'))
                      # & (stock_df['ticker'].str.lower() > 'w')
                      & (stock_df['industry'].str.contains('reit', regex=True, case=False) == False)
                      & (stock_df['country'].str.lower() != 'china')]['ticker'].tolist()
print(len(listStocks))