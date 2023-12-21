import statistics
from datetime import datetime, timedelta
import sys, os
import yahoo_fin.stock_info as si
import pandas as pd
from Market import Market
from currency_scrapeYahoo import getBalanceSheetCurrency
from currency_scrapeYahoo import getListingCurrency
import currency_getExchangeRate
from helperMethods import getFromDF, convertHK, getFromDFYearly, roundB, boolToString
import yfinance as yf

MARKET = Market.HK
yearlyFlag = False
INSIDER_OWN_MIN = 10

COUNT = 0


def increment():
    global COUNT
    COUNT = COUNT + 1
    return COUNT


ONE_YEAR_AGO = datetime.today() - timedelta(weeks=53)
PRICE_INTERVAL = '1wk'

exchange_rate_dict = currency_getExchangeRate.getExchangeRateDict()

fileOutput = open('list_results_hk', 'w')

stock_df = pd.read_csv('list_HK_Tickers', dtype=object, sep=" ", index_col=False,
                       names=['ticker', 'name'], error_bad_lines=False)

#
stock_df['ticker'] = stock_df['ticker'].astype(str)
stock_df['ticker'] = stock_df['ticker'].map(lambda x: convertHK(x))
hk_shares = pd.read_csv('list_HK_totalShares', sep=" ", index_col=False, names=['ticker', 'shares'])
listStocks = stock_df['ticker'].tolist()
print(listStocks)

# listStocks = ['2127.HK']

# print(listStocks)
# fileOutput = open('list_results_hk', 'w')

for s in listStocks:
    print(s)
    stock = yf.Ticker(s)
    # inc = stock.income_stmt
    try:
        bs = stock.balance_sheet
        cash = bs.loc['Cash And Cash Equivalents'][0]
        liab = bs.loc['Total Liabilities Net Minority Interest'][0]
        cap = stock.get_fast_info()['marketCap']

        if ((cash - liab) / cap > 1):
            outputString = (s + ' cash:' + str(roundB(cash, 2)) \
                            + ' liab:' + str(roundB(liab, 2)) + ' cap:' + str(roundB(cap, 2)) \
                            + ' ratio:' + str(round((cash - liab) / cap, 2)))
            print(outputString)
            fileOutput.write(outputString + '\n')
            fileOutput.flush()

    except Exception as e:
        print(s, e)
        continue
