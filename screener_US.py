import os
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


yearAgo = datetime.today() - timedelta(weeks=53)
# START_DATE = (datetime.today() - timedelta(weeks=52 * 10)).strftime('%-m/%-d/%Y')
# PRICE_START_DATE = (datetime.today() - timedelta(weeks=52 * 2)).strftime('%-m/%-d/%Y')
# PRICE_START_DATE = (datetime.today() - timedelta(weeks=52 * 2)).strftime('%-m/%-d/%Y')
# DIVIDEND_START_DATE = (datetime.today() - timedelta(weeks=52 * 10)).strftime('%-m/%-d/%Y')
PRICE_INTERVAL = '1wk'

exchange_rate_dict = currency_getExchangeRate.getExchangeRateDict()

fileOutput = open('list_results_US', 'w')

# ownershipDic = getInsiderOwnership()

stock_df = pd.read_csv('list_US_Tickers', sep=" ", index_col=False,
                       names=['ticker', 'name', 'sector', 'industry', 'country', 'mv', 'price'])
print(stock_df)

# listStocks = stock_df[(stock_df['price'] > 1)
#                       & (stock_df['sector'].str
#                          .contains('financial|healthcare', regex=True, case=False) == False)
#                       & (stock_df['industry'].str.contains('reit', regex=True, case=False) == False)
#                       & (stock_df['country'].str.lower() != 'china')]['ticker'].tolist()

listStocks = stock_df['ticker'].tolist()

# listStocks = ['APWC']
print(len(listStocks), listStocks)

for comp in listStocks:
    try:
        companyName = stock_df.loc[stock_df['ticker'] == comp]['name'].item()

        print(increment(), comp, companyName)
        data = si.get_data(comp, interval=PRICE_INTERVAL)
        print("start date ", data.index[0].strftime('%-m/%-d/%Y'))

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

        if currRatio <= 1:
            print(comp, "current ratio < 1", currRatio)
            continue

        totalAssets = getFromDF(bs, "totalAssets")
        totalL = getFromDF(bs, "totalLiab")
        goodWill = getFromDF(bs, 'goodWill')
        intangibles = getFromDF(bs, 'intangibleAssets')
        tangible_Equity = totalAssets - totalL - goodWill - intangibles

        if tangible_Equity < 0:
            print(comp, "de ratio> 1. or tangible equity < 0 ", tangible_Equity)
            continue

        debtEquityRatio = totalL / tangible_Equity
        if debtEquityRatio > 1:
            print(comp, "de ratio > 1 ", debtEquityRatio)
            continue

        incomeStatement = si.get_income_statement(comp, yearly=yearlyFlag)

        cf = si.get_cash_flow(comp, yearly=yearlyFlag)
        cfo = getFromDFYearly(cf, "totalCashFromOperatingActivities", yearlyFlag)

        if cfo <= 0:
            print(comp, "cfo <= 0 ", cfo)
            continue

        shares = si.get_quote_data(comp)['sharesOutstanding']

        listingCurrency = getListingCurrency(comp)
        bsCurrency = getBalanceSheetCurrency(comp, listingCurrency)
        # print("listing currency, bs currency, ", listingCurrency, bsCurrency)
        exRate = currency_getExchangeRate.getExchangeRate(exchange_rate_dict, listingCurrency, bsCurrency)

        marketPrice = si.get_live_price(comp)
        marketCap = marketPrice * shares

        pb = marketCap / (tangible_Equity / exRate)
        pCfo = marketCap / (cfo / exRate)
        print("MV, cfo", roundB(marketCap, 2), roundB(cfo, 2))

        # if pb >= 0.6 or pb <= 0:
        #     print(comp, 'pb > 0.6 or pb <= 0', pb)
        #     continue
        #
        if pCfo > 10:
            print(comp, 'pcfo > 10', pCfo)
            continue

        revenue = getFromDFYearly(incomeStatement, "totalRevenue", yearlyFlag)

        retainedEarningsAssetRatio = retainedEarnings / totalAssets
        cfoAssetRatio = cfo / totalAssets
        # ebitAssetRatio = ebit / totalAssets

        data52wk = data.loc[data.index > yearAgo]
        percentile = 100.0 * (marketPrice - data52wk['low'].min()) / (data52wk['high'].max() - data52wk['low'].min())
        low_52wk = data52wk['low'].min()
        avgDollarVol = (data[-10:]['close'] * data[-10:]['volume']).sum() / 10

        # insiderPerc = ownershipDic[comp]
        insiderPerc = float(si.get_holders(comp).get('Major Holders')[0][0].rstrip("%"))
        print(comp, "insider percent", insiderPerc)

        divs = si.get_dividends(comp)

        divSum = divs['dividend'].sum() if not divs.empty else 0
        startToNow = (datetime.today() - data.index[0]).days / 365.25
        print(" start to now ", startToNow, 'starting date ', data.index[0])
        divYield = divSum / marketPrice / startToNow

        divsPastYear = divs.loc[divs.index > ONE_YEAR_AGO]
        divSumPastYear = divsPastYear['dividend'].sum() if not divsPastYear.empty else 0
        divLastYearYield = divSumPastYear / marketPrice

        schloss = pb < 1 and marketPrice < low_52wk * 1.1 and insiderPerc > INSIDER_OWN_MIN
        netnet = (cash + receivables * 0.8 + inventory * 0.5 - totalL) / exRate - marketCap > 0
        magic6 = pCfo < 6 and (divYield >= 0.06 or divLastYearYield >= 0.06)
        pureHighYield = (divYield >= 0.06 or divLastYearYield >= 0.06)

        if schloss or netnet or magic6 or pureHighYield:
            outputString = comp + " " + " " + companyName + ' ' \
                           + " dai$Vol:" + str(round(avgDollarVol / 1000000)) + "M " \
                           + country.replace(" ", "_") + " " \
                           + sector.replace(" ", "_") + " " + listingCurrency + bsCurrency \
                           + boolToString(schloss, "schloss") + boolToString(netnet, "netnet") \
                           + boolToString(magic6, "magic6") + boolToString(pureHighYield, 'highYield') \
                           + " MV:" + str(roundB(marketCap, 1)) + 'B' \
                           + " B:" + str(roundB(tangible_Equity / exRate, 1)) + 'B' \
                           + " P/CFO:" + str(round(pCfo, 2)) \
                           + " P/B:" + str(round(pb, 1)) \
                           + " C/R:" + str(round(currRatio, 2)) \
                           + " D/E:" + str(round(debtEquityRatio, 2)) \
                           + " RetEarning/A:" + str(round(retainedEarningsAssetRatio, 2)) \
                           + " S/A:" + str(round(revenue / totalAssets, 2)) \
                           + " cfo/A:" + str(round(cfoAssetRatio, 2)) \
                           + " 52w_p%:" + str(round(percentile)) \
                           + " divYldAll:" + str(round(divYield * 100)) + "%" \
                           + " divYldLastYear:" + str(round(divLastYearYield * 100)) + "%" \
                           + " insider%: " + str(round(insiderPerc)) + "%"

            print(outputString)
            fileOutput.write(outputString + '\n')
            fileOutput.flush()

    except Exception as e:
        print(comp, "exception", e)
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
        fileOutput.flush()
