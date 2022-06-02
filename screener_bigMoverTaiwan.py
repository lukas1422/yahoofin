import math
import os
import statistics
import sys

import yahoo_fin.stock_info as si

from Market import Market
from currency_scrapeYahoo import getListingCurrency
import currency_getExchangeRate
from helperMethods import getFromDF, convertHK, roundB, convertChinaForYahoo, getFromDFYearly

COUNT = 0

MARKET = Market.TAIWAN
yearlyFlag = False
PRICE_INTERVAL = '1wk'


def increment():
    global COUNT
    COUNT = COUNT + 1
    return COUNT


exchange_rate_dict = currency_getExchangeRate.getExchangeRateDict()

fileOutput = open('list_bigMoveTW', 'w')

# US Version Starts

listStocks = [str(i).zfill(4) + '.TW' for i in range(1, 9999)]
# listStocks = ['2609.TW']

for comp in listStocks:

    print(increment())

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
        twoYearMin = min(priceData[-140:]['low'])

        # low_52wk = quoteData['fiftyTwoWeekLow'] if 'fiftyTwoWeekLow' in quoteData else 0
        medianDollarVol = statistics.median(priceData[-10:]['close'] * priceData[-10:]['volume']) / 5
        print(comp, 'vol is ', medianDollarVol)

        # if medianDollarVol < 500000:
        #     print(comp, 'vol too small', medianDollarVol)
        #     continue

        print(comp, marketPrice, 'twoyearlow', twoYearMin, 'price/52weeklow', marketPrice / twoYearMin)

        if marketPrice / twoYearMin < 5:
            print('did not rise 5 times')
            continue

        outputString = comp + " " \
                       + " day$Vol:" + str(round(medianDollarVol / 1000000, 1)) + "M " \
                       + country.replace(" ", "_") + " " \
                       + sector.replace(" ", "_") + " " \
                       + 'rose multiple:' + str(round(marketPrice / twoYearMin))

        print(outputString)

        fileOutput.write(outputString + '\n')
        fileOutput.flush()


    except Exception as e:
        print(comp, "exception", e)
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
