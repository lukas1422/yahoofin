import pandas as pd

stock_df = pd.read_csv('list_UScompanyInfo', sep="\t", index_col=False,
                       names=['ticker', 'name', 'sector', 'industry', 'country', 'mv', 'price'])

# dtype='str', converters={'mv': float, 'price': float})
# print(file_data)
# print(file_data.dtypes)
# print(file_data[file_data['country'] == 'China'])
# print(file_data[(file_data['price'] > 1)
#                 & (file_data['industry'].str.contains('Fund') == False)
#                 & (file_data['country'].str.lower() != 'china')][['ticker', 'sector', 'industry']])
listStocks = stock_df[(stock_df['price'] > 1)
                      & (stock_df['sector'] != 'Financial')
                      # & (stock_df['industry'].str.contains('fund|shell', regex=True, case=False))
                      & (stock_df['country'].str.lower() != 'china')]['ticker'].tolist()

print(len(listStocks))
