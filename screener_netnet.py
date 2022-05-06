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

MARKET = Market.US
yearlyFlag = False


def increment():
    global COUNT
    COUNT = COUNT + 1
    return COUNT


exchange_rate_dict = currency_getExchangeRate.getExchangeRateDict()

fileOutput = open('list_netnet', 'w')

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

        if 'real estate' in sector.lower() or 'financial' in sector.lower():
            print(comp, " no real estate or financial ")
            continue

        marketPrice = si.get_live_price(comp)
        print(comp, 'market price', marketPrice)

        if math.isnan(marketPrice):
            print(comp, "market price is nan")
            continue

        bs = si.get_balance_sheet(comp, yearly=yearlyFlag)

        if bs.empty:
            print(comp, "balance sheet is empty")
            continue

        retainedEarnings = getFromDF(bs, "retainedEarnings")

        if retainedEarnings <= 0:
            print(comp, " retained earnings <= 0 ", retainedEarnings)
            continue

        cash = getFromDF(bs, 'cash')
        if cash == 0:
            print(comp, 'cash is 0 ')
            continue

        currA = getFromDF(bs, "totalCurrentAssets")
        totalL = getFromDF(bs, "totalLiab")

        if currA < totalL:
            print(comp, " current assets < total liab", roundB(currA, 2), roundB(totalL, 2))
            continue

        cf = si.get_cash_flow(comp, yearly=yearlyFlag)
        cfo = getFromDFYearly(cf, "totalCashFromOperatingActivities", yearlyFlag)

        if cfo <= 0:
            print(comp, "cfo <= 0 ", cfo)
            continue

        receivables = getFromDF(bs, 'netReceivables')
        inventory = getFromDF(bs, 'inventory')

        # shares = scrape_sharesOutstanding.scrapeTotalSharesXueqiu(comp)
        if MARKET == Market.US:
            shares = si.get_quote_data(comp)['sharesOutstanding']
        elif MARKET == Market.HK:
            shares = hk_shares[hk_shares['ticker'] == comp]['shares'].item()
            print(hk_shares[hk_shares['ticker'] == comp]['shares'].item())
        elif MARKET == Market.CHINA:
            shares = china_shares[china_shares['ticker'] == comp]['shares'].item()
            print('china shares', shares)
        else:
            raise Exception("market not found ", MARKET)

        # marketCap = marketPrice * shares
        marketCap = si.get_quote_data(comp)['marketCap']
        print('shares ', shares, 'market cap', roundB(marketCap, 2))

        listingCurr = getListingCurrency(comp)
        # bsCurr = getBalanceSheetCurrency(comp, listingCurr)
        bsCurr = si.get_quote_data(comp)['financialCurrency']
        exRate = currency_getExchangeRate.getExchangeRate(exchange_rate_dict, listingCurr, bsCurr)

        pCfo = marketCap / (cfo / exRate)
        print("MV, cfo", roundB(marketCap, 2), roundB(cfo, 2))

        # if pCfo > 10:
        #     print(comp, ' pcfo > 10')
        #     continue

        # if MARKET == Market.HK:
        #     if marketCap < 1000000000:
        #         print(comp, "HK market cap less than 1B", marketCap / 1000000000)
        #         continue

        if cash + receivables + inventory - totalL < exRate * marketCap:
            print(comp, listingCurr, bsCurr,
                  'cash + rec + inv - L < mv. cash rec inv Liab MV:',
                  roundB(cash, 2), roundB(receivables, 2),
                  roundB(inventory, 2), roundB(totalL, 2), roundB(marketCap, 2))
            continue

        data = si.get_data(comp, interval='1wk')
        medianDollarVol = statistics.median(data[-10:]['close'] * data[-10:]['volume']) / 5

        additionalComment = ""
        if cash > totalL + exRate * marketCap:
            profit = (cash + 0.8 * receivables + 0.5 * inventory) / (totalL + exRate * marketCap) - 1
            additionalComment = " CASH netnet, profit:" + str(round(profit * 100)) + '%'
        elif cash + 0.8 * receivables > totalL + exRate * marketCap:
            profit = (cash + 0.8 * receivables + 0.5 * inventory) / (totalL + exRate * marketCap) - 1
            # additionalComment = " receivable conversion rate:" \
            #                     + str(round((totalL + marketCap * exRate - cash) / receivables, 2))
            additionalComment = " RECEIVABLES netnet, profit:" + str(round(profit * 100)) + '%'
        elif cash + 0.8 * receivables + 0.5 * inventory > totalL + exRate * marketCap:
            profit = (cash + 0.8 * receivables + 0.5 * inventory) / (totalL + exRate * marketCap) - 1
            # additionalComment = " inventory conversion rate:" \
            #                     + str(round((totalL + marketCap * exRate - cash - 0.8 * receivables)
            #                                 / inventory, 2))
            additionalComment = " INVENTORY netnet, profit:" + str(round(profit * 100)) + '%'
        elif cash + receivables + inventory > totalL + exRate * marketCap:
            additionalComment = " 鸡肋:cash+rec+inv-L>MV"
        else:
            print('none')
            continue

        # .to_string(index=False, header=False)
        outputString = comp + " " + stock_df[stock_df['ticker'] == comp]['name'].item() \
                       + " day$Vol:" + str(round(medianDollarVol / 1000000, 1)) + "M " \
                       + listingCurr + bsCurr + " " + str(exRate) + " " \
                       + country.replace(" ", "_") + " " \
                       + sector.replace(" ", "_") + " " \
                       + " cash:" + str(roundB(cash, 2)) \
                       + " rec:" + str(roundB(receivables, 2)) \
                       + " inv:" + str(roundB(inventory, 2)) \
                       + " CA:" + str(roundB(currA, 2)) \
                       + " L:" + str(roundB(totalL, 2)) \
                       + " mv:" + str(roundB(marketCap, 2)) \
                       + additionalComment

        print(outputString)

        fileOutput.write(outputString + '\n')
        fileOutput.flush()


    except Exception as e:
        print(comp, "exception", e)
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
