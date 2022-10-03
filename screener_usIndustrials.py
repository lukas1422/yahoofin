import os
import statistics
import sys
from datetime import datetime, timedelta
import yahoo_fin.stock_info as si
import pandas as pd
from Market import Market
from currency_scrapeYahoo import getBalanceSheetCurrency
from currency_scrapeYahoo import getListingCurrency
import currency_getExchangeRate
from helperMethods import getFromDF, getFromDFYearly, roundB, boolToString, getInsiderOwnership

MARKET = Market.US
yearlyFlag = False
INSIDER_OWN_MIN = 10
ONE_YEAR_AGO = datetime.today() - timedelta(weeks=53)

COUNT = 0


def increment():
    global COUNT
    COUNT = COUNT + 1
    return COUNT


# yearAgo = datetime.today() - timedelta(weeks=53)
# START_DATE = (datetime.today() - timedelta(weeks=52 * 10)).strftime('%-m/%-d/%Y')
# PRICE_START_DATE = (datetime.today() - timedelta(weeks=52 * 2)).strftime('%-m/%-d/%Y')
# PRICE_START_DATE = (datetime.today() - timedelta(weeks=52 * 2)).strftime('%-m/%-d/%Y')
# DIVIDEND_START_DATE = (datetime.today() - timedelta(weeks=52 * 10)).strftime('%-m/%-d/%Y')
PRICE_INTERVAL = '1wk'

exchange_rate_dict = currency_getExchangeRate.getExchangeRateDict()

fileOutput = open('list_results_US', 'w')

stock_df = pd.read_csv('list_industrials', sep=" ", index_col=False, names=['ticker'])
print(stock_df)

listStocks = stock_df['ticker'].tolist()

print(len(listStocks), listStocks)

for comp in listStocks:
    try:
        # companyName = stock_df.loc[stock_df['ticker'] == comp]['name'].item()

        print(increment())
        # print(comp, companyName)
        print(comp)

        try:
            info = si.get_company_info(comp)
        except Exception as e:
            print(e)
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            info = ""

        country = getFromDF(info, "country")
        sector = getFromDF(info, 'sector')

        if 'china' in country.lower():
            print(comp, 'skip china')
            continue

        # if 'real estate' in sector.lower() or 'financial' in sector.lower():
        #     print(comp, " no real estate or financial ", sector)
        #     continue

        # if marketPrice <= 1:
        #     print(comp, 'market price < 1: ', marketPrice)
        #     continue

        bs = si.get_balance_sheet(comp, yearly=yearlyFlag)

        if bs.empty:
            print(comp, "balance sheet is empty")
            continue

        retainedEarnings = getFromDF(bs, "retainedEarnings")

        if retainedEarnings <= 0:
            print(comp, " retained earnings < 0 ", retainedEarnings)
            continue

        currL = getFromDF(bs, "totalCurrentLiabilities")

        cash = getFromDF(bs, "cash")
        receivables = getFromDF(bs, 'netReceivables')
        inventory = getFromDF(bs, 'inventory')

        currRatio = (cash + 0.8 * receivables + 0.5 * inventory) / currL

        if currRatio <= 0.5:
            print(comp, "current ratio < 0.5", currRatio)
            continue

        totalAssets = getFromDF(bs, "totalAssets")
        totalL = getFromDF(bs, "totalLiab")
        if totalL / totalAssets > 0.5:
            print('total liab more than half')
            continue

        fileOutput.write(comp + '\n')
        fileOutput.flush()

    except Exception as e:
        print(comp, "exception", e)
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
        fileOutput.flush()
