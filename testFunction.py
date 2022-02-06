import pandas as pd

file_data = pd.read_csv('list_companyInfo', sep="\t", index_col=False,
                        names=['ticker', 'name', 'sector', 'industry', 'country', 'mv', 'price'])

# dtype='str', converters={'mv': float, 'price': float})
# print(file_data)
# print(file_data.dtypes)
# print(file_data[file_data['country'] == 'China'])
print(file_data[(file_data['price'] > 1) & (file_data['country'].str.lower() == 'china')]
      [['ticker', 'name', 'country', 'price']])
