# return the lowest percentile on a historical basis

import math
import os
import statistics
import sys

from datetime import datetime

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


def increment():
    global COUNT
    COUNT = COUNT + 1
    return COUNT


exchange_rate_dict = currency_getExchangeRate.getExchangeRateDict()

fileOutput = open('list_biggestMover', 'w')

# US Version Starts
if MARKET == Market.US:
    stock_df = pd.read_csv('list_US_Tickers', sep=" ", index_col=False,
                           names=['ticker', 'name', 'sector', 'industry', 'country', 'mv', 'price'])

    # stock_df['listingDate'] = pd.to_datetime(stock_df['listingDate'])

    listStocks = stock_df['ticker'].tolist()
    # listStocks = stock_df[(stock_df['price'] > 1)
    #                       & (stock_df['sector'].str.contains('financial|healthcare', regex=True, case=False) == False)
    #                       # & (stock_df['listingDate'] < pd.to_datetime('2020-1-1'))
    #                       & (stock_df['industry'].str.contains('reit', regex=True, case=False) == False)
    #                       & (stock_df['country'].str.lower() != 'china')]['ticker'].tolist()

    # listStocks=['APWC']

elif MARKET == Market.HK:

    stock_df = pd.read_csv('list_HK_Tickers', dtype=object, sep=" ", index_col=False, names=['ticker', 'name'])
    stock_df['ticker'] = stock_df['ticker'].astype(str)
    stock_df['ticker'] = stock_df['ticker'].map(lambda x: convertHK(x))
    listStocks = stock_df['ticker'].tolist()
    hk_shares = pd.read_csv('list_HK_totalShares', sep=" ", index_col=False, names=['ticker', 'shares'])
    # print(hk_shares)
    # listStocks = ['0539.HK']
    # listStocks = ["2698.HK", "0743.HK", "0321.HK", "0819.HK",
    #               "1361.HK", "0057.HK", "0420.HK", "1085.HK", "1133.HK", "2131.HK",
    #               "3393.HK", "2355.HK", "0517.HK", "3636.HK", "0116.HK", "1099.HK", "2386.HK", "6188.HK"]
    # listStocks = ['2127.HK']

elif MARKET == Market.CHINA:
    stock_df = pd.read_csv('list_chinaTickers', dtype=object, sep=" ", index_col=False, names=['ticker', 'name'])
    stock_df['ticker'] = stock_df['ticker'].astype(str)
    stock_df['ticker'] = stock_df['ticker'].map(lambda x: convertChinaForYahoo(x))
    china_shares = pd.read_csv('list_China_totalShares', sep=" ", index_col=False, names=['ticker', 'shares'])
    china_shares['ticker'] = china_shares['ticker'].map(lambda x: convertChinaForYahoo(x))
    listStocks = stock_df['ticker'].tolist()

else:
    raise Exception("market not found")

print(datetime.now(), MARKET, len(listStocks), listStocks)

for comp in listStocks:

    print(increment())
    print(comp, stock_df[stock_df['ticker'] == comp]['name'].item())

    # data = si.get_data(comp, start_date=TEN_YEAR_AGO, interval=PRICE_INTERVAL)
    # print("start date ", data.index[0].strftime('%-m/%-d/%Y'))
    # print('last active day', data[data['volume'] != 0].index[-1].strftime('%-m/%-d/%Y'))

    try:
        info = si.get_company_info(comp)
        country = getFromDF(info, 'country')
        sector = getFromDF(info, 'sector')
        print('sector', sector)

        marketPrice = si.get_live_price(comp)
        print(comp, 'market price', marketPrice)

        if math.isnan(marketPrice):
            print(comp, "market price is nan")
            continue

        priceData = si.get_data(comp, interval=PRICE_INTERVAL)
        quoteData = si.get_quote_data(comp)
        hi = max(priceData['high'])
        lo = min(priceData['low'])
        percentile = (marketPrice - lo) / (hi - lo)
        if percentile > 0.1:
            print(comp, 'percentile > 0.1 ', percentile)
            continue

        maxT = priceData['high'].idxmax().date()
        minT = priceData['low'].idxmin().date()

        medianDollarVol = statistics.median(priceData[-10:]['close'] * priceData[-10:]['volume']) / 5
        print(comp, 'vol is ', medianDollarVol)
        if medianDollarVol < 1000000:
            print(comp, 'vol too small')
            continue

        print(comp, marketPrice, 'max', hi, 'min', lo, 'percentile', percentile)

        outputString = comp + " " + stock_df[stock_df['ticker'] == comp]['name'].item() \
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
