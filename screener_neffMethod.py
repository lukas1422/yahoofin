# highest dividend yield / PE ratio

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

fileOutput = open('list_neff', 'w')
fileOutput.write("\n")

stock_df = pd.read_csv('list_companyInfo', sep="\t", index_col=False,
                       names=['ticker', 'name', 'sector', 'industry', 'country', 'mv', 'price'])

listStocks = stock_df[(stock_df['price'] > 1)]['ticker'].tolist()

print(listStocks.__len__(), listStocks)

for comp in listStocks:
    print(increment())
    try:

        divs = si.get_dividends(comp, start_date=DIVIDEND_START_DATE)
        if divs.empty:
            print(comp, " no divs data ")
            continue

        divSum = divs['dividend'].sum()

        incomeStatement = si.get_income_statement(comp, yearly=True)
        netIncome = getFromDF(incomeStatement.loc['netIncome'])

        if netIncome < 0:
            print(comp, 'net income < 0', netIncome)
            continue

        bsCurrency = getBalanceSheetCurrency(comp)
        listingCurrency = getListingCurrency(comp)
        exRate = currency_getExchangeRate.getExchangeRate(exchange_rate_dict,
                                                          listingCurrency, bsCurrency)
        shares = si.get_quote_data(comp)['sharesOutstanding']

        marketPrice = si.get_live_price(comp)
        marketCap = marketPrice * shares

        pe = marketCap / (netIncome / exRate)

        divYield = divSum / marketPrice

        outputString = comp + " " \
                       + stock_df[stock_df['ticker'] == comp][['country', 'sector']] \
                           .to_string(index=False, header=False) + " " \
                       + listingCurrency + bsCurrency \
                       + " PE:" + str(round(pe, 1)) \
                       + " div10yr: " + str(round(divSum / marketPrice * 100, 2)) \
                       + " div/PE:" + str(round(divYield * 100 / pe, 2))

        print(outputString)
        fileOutput.write(outputString + '\n')
        fileOutput.flush()

    except Exception as e:
        print(comp, "exception", e)
