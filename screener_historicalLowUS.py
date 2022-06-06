# return the lowest percentile on a historical basis

import math
import os
import statistics
import sys

from datetime import datetime, timedelta

import yahoo_fin.stock_info as si
import pandas as pd

from Market import Market
from currency_scrapeYahoo import getListingCurrency
import currency_getExchangeRate
from helperMethods import getFromDF, convertHK, roundB, convertChinaForYahoo, getFromDFYearly

COUNT = 0

MARKET = Market.HK
yearlyFlag = False
PRICE_INTERVAL = '1wk'
N_YEAR_LOW = 3
N_YEAR_AGO = datetime.today() - timedelta(weeks=53 * N_YEAR_LOW)


def increment():
    global COUNT
    COUNT = COUNT + 1
    return COUNT


exchange_rate_dict = currency_getExchangeRate.getExchangeRateDict()

fileOutput = open('list_historicalLowUS', 'w')

stock_df = pd.read_csv('list_US_Tickers', sep=" ", index_col=False,
                       names=['ticker', 'name', 'sector', 'industry', 'country', 'mv', 'price'])
print(stock_df)

listStocks = stock_df['ticker'].tolist()

print(len(listStocks), listStocks)

print(datetime.now(), MARKET, len(listStocks), listStocks)

for comp in listStocks:

    print(increment())
    print(comp)

    # data = si.get_data(comp, start_date=TEN_YEAR_AGO, interval=PRICE_INTERVAL)
    # print("start date ", data.index[0].strftime('%-m/%-d/%Y'))
    # print('last active day', data[data['volume'] != 0].index[-1].strftime('%-m/%-d/%Y'))

    try:
        info = si.get_company_info(comp)
        country = getFromDF(info, 'country')
        sector = getFromDF(info, 'sector')
        print('sector', sector)

        if 'real estate' in sector.lower() or 'financial' in sector.lower() or 'healthcare' in sector.lower():
            print(comp, " no real estate or financial or healthcare", sector)
            continue

        marketPrice = si.get_live_price(comp)
        print(comp, 'market price', marketPrice)

        if math.isnan(marketPrice):
            print(comp, "market price is nan")
            continue

        # check RE
        bs = si.get_balance_sheet(comp, yearly=yearlyFlag)
        if bs.empty:
            print(comp, "balance sheet is empty")
            continue
        retainedEarnings = getFromDF(bs, "retainedEarnings")
        if retainedEarnings <= 0:
            print(comp, " retained earnings < 0 ", retainedEarnings)
            continue

        priceData = si.get_data(comp, interval=PRICE_INTERVAL)
        quoteData = si.get_quote_data(comp)

        N_YEAR_DATA = priceData.loc[priceData.index > N_YEAR_AGO]
        hi = max(N_YEAR_DATA['adjclose'])
        lo = min(N_YEAR_DATA['adjclose'])
        percentile = (marketPrice - lo) / (hi - lo)
        if percentile > 0.1:
            print(comp, 'percentile > 0.1 ', percentile)
            continue

        maxT = N_YEAR_DATA['adjclose'].idxmax().date()
        minT = N_YEAR_DATA['adjclose'].idxmin().date()

        medianDollarVol = statistics.median(priceData[-10:]['close'] * priceData[-10:]['volume']) / 5
        print(comp, 'vol is ', medianDollarVol)
        if medianDollarVol < 100000:
            print(comp, 'vol too small')
            continue

        print(comp, marketPrice, 'max', hi, 'min', lo, 'percentile', percentile)

        outputString = comp + " " \
                       + " day$Vol:" + str(round(medianDollarVol / 1000000, 1)) + "M " \
                       + country.replace(" ", "_") + " " \
                       + sector.replace(" ", "_") + " " \
                       + 'percentile:' + str(round(percentile * 100)) \
                       + ' maxT:' + str(maxT) \
                       + ' max:' + str(round(hi, 2)) \
                       + ' minT:' + str(minT) \
                       + ' min:' + str(round(lo, 2))

        print(outputString)

        fileOutput.write(outputString + '\n')
        fileOutput.flush()


    except Exception as e:
        print(comp, "exception", e)
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
