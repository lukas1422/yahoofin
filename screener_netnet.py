import os
import sys

import yahoo_fin.stock_info as si
import pandas as pd

from Market import Market
from currency_scrapeYahoo import getBalanceSheetCurrency
from currency_scrapeYahoo import getListingCurrency
import currency_getExchangeRate
from helperMethods import getFromDF, convertHK, roundB

COUNT = 0

MARKET = Market.HK
yearlyFlag = False


def increment():
    global COUNT
    COUNT = COUNT + 1
    return COUNT


# PRICE_INTERVAL = '1mo'

exchange_rate_dict = currency_getExchangeRate.getExchangeRateDict()

fileOutput = open('list_netnet', 'w')

# US Version Starts
if MARKET == Market.US:
    stock_df = pd.read_csv('list_US_Tickers', sep=" ", index_col=False,
                           names=['ticker', 'name', 'sector', 'industry', 'country', 'mv', 'price'])

    # stock_df['listingDate'] = pd.to_datetime(stock_df['listingDate'])

    listStocks = stock_df[(stock_df['price'] > 1)
                          & (stock_df['sector'].str
                             .contains('financial|healthcare', regex=True, case=False) == False)
                          # & (stock_df['listingDate'] < pd.to_datetime('2020-1-1'))
                          & (stock_df['industry'].str.contains('reit', regex=True, case=False) == False)
                          & (stock_df['country'].str.lower() != 'china')]['ticker'].tolist()

    # listStocks=['APWC']

elif MARKET == Market.HK:
    stock_df = pd.read_csv('list_HK_Tickers', dtype=object, sep=" ", index_col=False, names=['ticker', 'name'])
    stock_df['ticker'] = stock_df['ticker'].astype(str)
    stock_df['ticker'] = stock_df['ticker'].map(lambda x: convertHK(x))
    listStocks = stock_df['ticker'].tolist()
    hk_shares = pd.read_csv('list_HK_totalShares', sep=" ", index_col=False, names=['ticker', 'shares'])

    #listStocks = ['2127.HK']
    # listStocks = ["2698.HK", "0743.HK", "0321.HK", "0819.HK",
    #               "1361.HK", "0057.HK", "0420.HK", "1085.HK", "1133.HK", "2131.HK",
    #               "3393.HK", "2355.HK", "0517.HK", "3636.HK", "0116.HK", "1099.HK", "2386.HK", "6188.HK"]

    # listStocks = ['0155.HK']
else:
    raise Exception("market not found")

print(MARKET, len(listStocks), listStocks)

for comp in listStocks:

    print(increment(), comp, stock_df[stock_df['ticker'] == comp]['name'].item())

    try:
        info = si.get_company_info(comp)
        country = getFromDF(info, 'country')
        sector = getFromDF(info, 'sector')

        if 'real estate' in sector.lower() or 'financial' in sector.lower():
            print(comp, " no real estate or financial ")
            continue

        marketPrice = si.get_live_price(comp)

        # if marketPrice < 1:
        #     print(comp, "cent stock", marketPrice)
        #     continue

        bs = si.get_balance_sheet(comp, yearly=yearlyFlag)

        if bs.empty:
            print(comp, "balance sheet is empty")
            continue

        retainedEarnings = getFromDF(bs, "retainedEarnings")

        # RE>0 ensures that the stock is not a chronic cash burner
        if retainedEarnings <= 0:
            print(comp, " retained earnings <= 0 ", retainedEarnings)
            continue

        cash = getFromDF(bs, 'cash')
        if cash == 0:
            print(comp, 'cash is 0 ')
            continue

        currentAssets = getFromDF(bs, "totalCurrentAssets")
        totalLiab = getFromDF(bs, "totalLiab")

        if currentAssets < totalLiab:
            print(comp, " current assets < total liab", roundB(currentAssets, 2), roundB(totalLiab, 2))
            continue

        receivables = getFromDF(bs, 'netReceivables')
        inventory = getFromDF(bs, 'inventory')

        # shares = scrape_sharesOutstanding.scrapeTotalSharesXueqiu(comp)
        if MARKET == Market.US:
            shares = si.get_quote_data(comp)['sharesOutstanding']
        elif MARKET == Market.HK:
            shares = hk_shares[hk_shares['ticker'] == comp]['shares'].values[0]
        else:
            raise Exception("market not found ", MARKET)

        marketCap = marketPrice * shares

        if MARKET == Market.HK:
            if marketCap < 1000000000:
                print(comp, "HK market cap less than 1B", marketCap / 1000000000)
                continue

        listingCurr = getListingCurrency(comp)
        bsCurr = getBalanceSheetCurrency(comp, listingCurr)
        exRate = currency_getExchangeRate.getExchangeRate(exchange_rate_dict, listingCurr, bsCurr)

        if (cash + receivables + inventory - totalLiab) / exRate < marketCap:
            print(comp, listingCurr, bsCurr,
                  'cash + rec + inv - L < mv. cash rec inv Liab MV:',
                  roundB(cash, 2), roundB(receivables, 2),
                  roundB(inventory, 2), roundB(totalLiab, 2), roundB(marketCap, 2))
            continue

        additionalComment = ""
        if (cash - totalLiab) / exRate - marketCap > 0:
            profit = (cash - totalLiab) / exRate - marketCap
            additionalComment = " CASH netnet, profit:" + str(round(profit, 2))
        elif (cash + receivables - totalLiab) / exRate - marketCap > 0:
            additionalComment = " receivable conversion rate:" \
                                + str(round((totalLiab + marketCap * exRate - cash) / receivables, 2))
        elif (cash + 0.5 * receivables + inventory - totalLiab) / exRate - marketCap > 0:
            additionalComment = " inventory conversion rate:" \
                                + str(round((totalLiab + marketCap * exRate - cash - 0.5 * receivables)
                                            / inventory, 2))
        elif (cash + receivables + inventory - totalLiab) / exRate - marketCap > 0:
            additionalComment = " 鸡肋:CA-L>MV"

        # .to_string(index=False, header=False)
        outputString = comp + " " + stock_df[stock_df['ticker'] == comp]['name'].item() + ' ' \
                       + listingCurr + bsCurr + " " + str(exRate) + " " \
                       + country.replace(" ", "_") + " " \
                       + sector.replace(" ", "_") + " " \
                       + " cash:" + str(roundB(cash, 2)) \
                       + " rec:" + str(roundB(receivables, 2)) \
                       + " inv:" + str(roundB(inventory, 2)) \
                       + " CA:" + str(roundB(currentAssets, 2)) \
                       + " L:" + str(roundB(totalLiab, 2)) \
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
