# maximize roe/pe

import yahoo_fin.stock_info as si
import pandas as pd
from currency_scrapeYahoo import getBalanceSheetCurrency
from currency_scrapeYahoo import getListingCurrency
import currency_getExchangeRate
from helperMethods import getFromDF

COUNT = 0


def increment():
    global COUNT
    COUNT = COUNT + 1
    return COUNT


START_DATE = '3/1/2020'
DIVIDEND_START_DATE = '1/1/2010'
PRICE_INTERVAL = '1mo'

exchange_rate_dict = currency_getExchangeRate.getExchangeRateDict()

fileOutput = open('list_greenblatt', 'w')

stock_df = pd.read_csv('list_companyInfo', sep="\t", index_col=False,
                       names=['ticker', 'name', 'sector', 'industry', 'country', 'mv', 'price'])

listStocks = stock_df[(stock_df['price'] > 1) & (stock_df['country'].str.lower() != 'china')]['ticker'].tolist()

print(len(listStocks), listStocks)

for comp in listStocks:
    print(increment())
    try:
        incomeStatement = si.get_income_statement(comp, yearly=True)
        netIncome = getFromDF(incomeStatement.loc['netIncome'])

        if netIncome < 0:
            print(comp, "net income < 0")
            continue

        bs = si.get_balance_sheet(comp)
        totalAssets = getFromDF(bs.loc["totalAssets"])

        roa = netIncome / totalAssets

        shares = si.get_quote_data(comp)['sharesOutstanding']

        bsCurrency = getBalanceSheetCurrency(comp)
        listingCurrency = getListingCurrency(comp)
        exRate = currency_getExchangeRate.getExchangeRate(exchange_rate_dict, listingCurrency, bsCurrency)

        marketPrice = si.get_live_price(comp)
        marketCap = marketPrice * shares
        pe = marketCap / (netIncome / exRate)

        outputString = comp + " " \
                       + stock_df[stock_df['ticker'] == 'M'][['country', 'sector']] \
                           .to_string(index=False, header=False) + " " \
                       + listingCurrency + bsCurrency \
                       + " ROA:" + str(round(roa * 100, 2)) \
                       + " PE:" + str(round(pe, 1)) \
                       + " ROA/PE:" + str(round(roa * 100 / pe, 2))

        print(outputString)
        fileOutput.write(outputString + '\n')
        fileOutput.flush()

    except Exception as e:
        print(comp, "exception", e)
