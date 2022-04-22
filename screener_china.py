import statistics
from datetime import datetime, timedelta
import sys, os
import yahoo_fin.stock_info as si
import pandas as pd

import scrape_sharesOutstanding
from Market import Market
from currency_scrapeYahoo import getBalanceSheetCurrency
from currency_scrapeYahoo import getListingCurrency
import currency_getExchangeRate
from helperMethods import getFromDF, getFromDFYearly, roundB, boolToString, convertChinaForYahoo, \
    convertChinaForXueqiu

MARKET = Market.CHINA
yearlyFlag = False
INSIDER_OWN_MIN = 10

COUNT = 0
ONE_YEAR_AGO = datetime.today() - timedelta(weeks=53)


def increment():
    global COUNT
    COUNT = COUNT + 1
    return COUNT


# PRICE_START_DATE = datetime.today() - timedelta(weeks=53)
# PRICE_START_DATE = (datetime.today() - timedelta(weeks=52 * 2)).strftime('%-m/%-d/%Y')
START_DATE = (datetime.today() - timedelta(weeks=52 * 10)).strftime('%-m/%-d/%Y')
PRICE_INTERVAL = '1wk'

exchange_rate_dict = currency_getExchangeRate.getExchangeRateDict()

fileOutput = open('list_results_china', 'w')

stock_df = pd.read_csv('list_chinaTickers', dtype=object, sep=" ", index_col=False, names=['ticker', 'name'])
stock_df['ticker'] = stock_df['ticker'].astype(str)
stock_df['ticker'] = stock_df['ticker'].map(lambda x: convertChinaForYahoo(x))
china_shares = pd.read_csv('list_China_totalShares', sep=" ", index_col=False, names=['ticker', 'shares'])
china_shares['ticker'] = china_shares['ticker'].map(lambda x: convertChinaForYahoo(x))
listStocks = stock_df['ticker'].tolist()
# listStocks = ['600519.SS']

print(len(listStocks), listStocks)

for comp in listStocks:
    try:
        companyName = stock_df.loc[stock_df['ticker'] == comp]['name'].item()

        print(increment(), comp, companyName)

        try:
            info = si.get_company_info(comp)
        except Exception as e:
            print(comp, "exception", e)
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            info = ""

        country = getFromDF(info, "country")
        sector = getFromDF(info, 'sector')

        if 'real estate' in sector.lower() or 'financial' in sector.lower():
            print(comp, " no real estate or financial ", sector)
            continue
        print('country sector', country, sector)

        bs = si.get_balance_sheet(comp, yearly=yearlyFlag)

        if bs.empty:
            print(comp, "balance sheet is empty")
            continue

        retainedEarnings = getFromDF(bs, "retainedEarnings")

        if retainedEarnings <= 0:
            print(comp, " retained earnings < 0 ", retainedEarnings)
            continue

        currAssets = getFromDF(bs, "totalCurrentAssets")
        currLiab = getFromDF(bs, "totalCurrentLiabilities")

        cash = getFromDF(bs, "cash")
        receivables = getFromDF(bs, 'netReceivables')
        inventory = getFromDF(bs, 'inventory')

        currRatio = (cash + 0.8 * receivables + 0.5 * inventory) / currLiab

        if currRatio <= 1:
            print(comp, "curr ratio < 1", currRatio)
            continue

        totalAssets = getFromDF(bs, "totalAssets")
        totalLiab = getFromDF(bs, "totalLiab")
        goodWill = getFromDF(bs, 'goodWill')
        intangibles = getFromDF(bs, 'intangibleAssets')
        tangible_Equity = totalAssets - totalLiab - goodWill - intangibles
        debtEquityRatio = totalLiab / tangible_Equity

        if tangible_Equity < 0:
            print(comp, "tangible equity < 0 ", tangible_Equity)
            continue

        # if debtEquityRatio > 1 or tangible_Equity < 0:
        #     print(comp, "de ratio> 1 or tangible equity < 0 ", debtEquityRatio, tangible_Equity)
        #     continue

        incomeStatement = si.get_income_statement(comp, yearly=yearlyFlag)

        cf = si.get_cash_flow(comp, yearly=yearlyFlag)
        cfo = getFromDFYearly(cf, "totalCashFromOperatingActivities", yearlyFlag)
        dep = getFromDFYearly(cf, "depreciation", yearlyFlag)

        if cfo <= 0:
            print(comp, "cfo <= 0 ", cfo)
            continue

        shares = china_shares[china_shares['ticker'] == comp]['shares'].item()

        if shares == "error":
            shares = scrape_sharesOutstanding.scrapeTotalSharesXueqiu(convertChinaForXueqiu(comp[:6]))
            print(comp, 'share was error', shares)

        print(comp, 'shares', shares)

        listingCurrency = getListingCurrency(comp)
        bsCurrency = getBalanceSheetCurrency(comp, listingCurrency)
        print("listing currency, bs currency, ", listingCurrency, bsCurrency)
        exRate = currency_getExchangeRate.getExchangeRate(exchange_rate_dict, listingCurrency, bsCurrency)
        print('exrate', listingCurrency, bsCurrency, exRate)

        # shares = si.get_quote_data(comp)['sharesOutstanding']

        marketPrice = si.get_live_price(comp)

        marketCap = marketPrice * shares

        # if marketCap < 1000000000:
        #     print(comp, "market cap < 1B TOO SMALL", roundB(marketCap, 2))
        #     continue

        pb = marketCap / (tangible_Equity / exRate)
        fcf = cfo - dep
        pFCF = marketCap / (fcf / exRate)
        print("MV, cfo", 'fcf', roundB(marketCap, 2), roundB(cfo, 2), roundB(fcf, 2))

        if fcf <= 0:
            print(comp, 'fcf <= 0', fcf)
            continue

        revenue = getFromDFYearly(incomeStatement, "totalRevenue", yearlyFlag)
        retainedEarningsAssetRatio = retainedEarnings / totalAssets
        cfoAssetRatio = cfo / totalAssets
        # ebitAssetRatio = ebit / totalAssets

        priceData = si.get_data(comp, interval=PRICE_INTERVAL)
        print("start date ", priceData.index[0].strftime('%-m/%-d/%Y'))
        data52w = priceData.loc[priceData.index > ONE_YEAR_AGO]
        percentile = 100.0 * (marketPrice - data52w['low'].min()) / (data52w['high'].max() - data52w['low'].min())
        low_52wk = data52w['low'].min()
        medianDollarVol = statistics.median(priceData[-10:]['close'] * priceData[-10:]['volume']) / 5

        try:
            insiderPerc = float(si.get_holders(comp).get('Major Holders')[0][0].rstrip("%"))
            print(comp, MARKET, "insider percent", insiderPerc)
        except Exception as e:
            print(e)
            insiderPerc = 0

        divs = si.get_dividends(comp)
        # divSum = divs['dividend'].sum() if not divs.empty else 0
        # startToNow = (datetime.today() - priceData.index[0]).days / 365.25
        # # print(" start to now ", startToNow, 'starting date ', data.index[0])
        # divYield = divSum / marketPrice / startToNow
        # divsPastYear = divs.loc[divs.index > ONE_YEAR_AGO]
        # divSumPastYear = divsPastYear['dividend'].sum() if not divsPastYear.empty else 0
        # divLastYearYield = divSumPastYear / marketPrice

        yearSpan = 2021 - priceData[:1].index.item().year + 1
        divPrice = pd.merge(divs.groupby(by=lambda d: d.year)['dividend'].sum(),
                            priceData.groupby(by=lambda d: d.year)['close'].mean(), left_index=True, right_index=True)
        divPrice['yield'] = divPrice['dividend'] / divPrice['close']
        print('divprice', divPrice)

        divYieldAll = divPrice[divPrice.index != 2022]['yield'].sum() / yearSpan \
            if not divPrice[divPrice.index != 2022].empty else 0

        divYield2021 = divPrice.loc[2021]['yield'] if 2021 in divPrice.index else 0
        print('div yield all', divYieldAll, 'lastyear', divYield2021)

        schloss = pb < 0.6 and marketPrice < low_52wk * 1.1 and insiderPerc > INSIDER_OWN_MIN
        netnetRatio = (cash + receivables * 0.8 + inventory * 0.5 - totalLiab) / exRate / marketCap
        netnet = (cash + receivables * 0.8 + inventory * 0.5 - totalLiab) / exRate > marketCap
        magic6 = pFCF < 6 and (divYieldAll >= 0.06 or divYield2021 >= 0.06)

        if schloss or netnet or magic6:
            outputString = comp + " " + country.replace(" ", "_") + " " \
                           + " dai$Vol:" + str(round(medianDollarVol / 1000000, 2)) + "M " \
                           + sector.replace(" ", "_") + " " + listingCurrency + bsCurrency \
                           + boolToString(schloss, "schloss") + boolToString(netnet, "netnet") \
                           + boolToString(magic6, "magic6") \
                           + " MV:" + str(roundB(marketCap, 1)) + 'B' \
                           + " BV:" + str(roundB(tangible_Equity / exRate, 1)) + 'B' \
                           + " P/CFO:" + str(round(pFCF, 2)) \
                           + " P/B:" + str(round(pb, 1)) \
                           + " C/R:" + str(round(currRatio, 2)) \
                           + " D/E:" + str(round(debtEquityRatio, 2)) \
                           + " RetEarning/A:" + str(round(retainedEarningsAssetRatio, 2)) \
                           + " S/A:" + str(round(revenue / totalAssets, 2)) \
                           + " cfo/A:" + str(round(cfoAssetRatio, 2)) \
                           + " 52w_p%:" + str(round(percentile)) \
                           + " divYld:" + str(round(divSum / marketPrice * 100 / startToNow)) + "%" \
                           + " insider%:" + str(round(insiderPerc)) + "%"

            print(outputString)
            fileOutput.write(outputString + '\n')
            fileOutput.flush()
        # else:
        #     print("None " + companyName + ' nnRatio:' + str(round(netnetRatio, 2)) \
        #           + " dai$Vol:" + str(round(medianDollarVol / 1000000, 2)) + "M" \
        #           + " MV:" + str(roundB(marketCap, 1)) + 'B'
        #           + " BV:" + str(roundB(tangible_Equity / exRate, 1)) + 'B'
        #           + " P/CFO:" + str(round(pCfo, 2))
        #           + " P/B:" + str(round(pb, 1))
        #           + " C/R:" + str(round(currRatio, 2))
        #           + " D/E:" + str(round(debtEquityRatio, 2))
        #           + " RetEarning/A:" + str(round(retainedEarningsAssetRatio, 2))
        #           + " S/A:" + str(round(revenue / totalAssets, 2))
        #           + " cfo/A:" + str(round(cfoAssetRatio, 2))
        #           + " 52w_p%:" + str(round(percentile))
        #           + " divYld:" + str(round(divSum / marketPrice * 100 / startToNow)) + "%"
        #           + " insider%:" + str(round(insiderPerc)) + "%")

    except Exception as e:
        print(comp, "exception", e)
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)

        fileOutput.flush()
