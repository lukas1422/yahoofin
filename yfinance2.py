import yfinance as yf

stock = yf.Ticker('2127.HK')
inc = stock.income_stmt
bs = stock.balance_sheet
cash = bs.loc['Cash And Cash Equivalents'][0]
liab = bs.loc['Total Liabilities Net Minority Interest'][0]
cap = stock.get_fast_info()['marketCap']
print(bs.to_string())
print('cash',cash)
print('liab',liab)
print('cap', cap)

print((cash-liab)/cap)

