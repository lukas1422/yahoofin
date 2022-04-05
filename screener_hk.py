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

stock_df = pd.read_csv('list_HK_Tickers', dtype=object, sep=" ", index_col=False, names=['ticker', 'name'])
stock_df['ticker'] = stock_df['ticker'].astype(str)
stock_df['ticker'] = stock_df['ticker'].map(lambda x: convertHK(x))
hk_shares = pd.read_csv('list_HK_totalShares', sep=" ", index_col=False, names=['ticker', 'shares'])
listStocks = stock_df['ticker'].tolist()
# listStocks = ['2698.HK']
# stock_df_torun = pd.read_csv('list_special', dtype=object, sep=" ", index_col=False, names=['ticker'])
# stock_df_torun['ticker'] = stock_df_torun['ticker'].map(lambda x: convertHK(x))
# listStocks = stock_df_torun['ticker'].tolist()

print(len(listStocks), listStocks)

for comp in listStocks:
    print("_____________________________")
    try:
        companyName = stock_df.loc[stock_df['ticker'] == comp]['name'].item()

        print(increment(), comp, companyName)

        data = si.get_data(comp, interval=PRICE_INTERVAL)
        print("date start date ", data.index[0].strftime('%-m/%-d/%Y'))
        print('last active day', data[data['volume'] != 0].index[-1].strftime('%-m/%-d/%Y'))

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
        # print('country sector', country, sector)

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

        currA = getFromDF(bs, "totalCurrentAssets")
        currL = getFromDF(bs, "totalCurrentLiabilities")

        cash = getFromDF(bs, "cash")
        receivables = getFromDF(bs, 'netReceivables')
        inventory = getFromDF(bs, 'inventory')

        currRatio = (cash + 0.8 * receivables + 0.5 * inventory) / currL

        if currRatio <= 1:
            print(comp, "curr ratio < 1", currRatio)
            continue

        totalAssets = getFromDF(bs, "totalAssets")
        totalLiab = getFromDF(bs, "totalLiab")
        goodWill = getFromDF(bs, 'goodWill')
        intangibles = getFromDF(bs, 'intangibleAssets')
        tangible_Equity = totalAssets - totalLiab - goodWill - intangibles

        if tangible_Equity < 0:
            print(comp, " tangible equity < 0 ", tangible_Equity)
            continue

        debtEquityRatio = totalLiab / tangible_Equity

        if debtEquityRatio > 1:
            print(comp, "de ratio> 1 ", debtEquityRatio)
            continue

        incomeStatement = si.get_income_statement(comp, yearly=yearlyFlag)

        cf = si.get_cash_flow(comp, yearly=yearlyFlag)
        cfo = getFromDFYearly(cf, "totalCashFromOperatingActivities", yearlyFlag)

        if cfo <= 0:
            print(comp, "cfo <= 0 ", cfo)
            continue

        shares = hk_shares[hk_shares['ticker'] == comp]['shares'].item()

        listingCurrency = getListingCurrency(comp)
        bsCurrency = getBalanceSheetCurrency(comp, listingCurrency)
        # print("listing currency, bs currency, ", listingCurrency, bsCurrency)
        exRate = currency_getExchangeRate.getExchangeRate(exchange_rate_dict, listingCurrency, bsCurrency)

        marketPrice = si.get_live_price(comp)
        marketCap = marketPrice * shares
        if marketCap < 1000000000:
            print(comp, "market cap < 1B TOO SMALL", roundB(marketCap, 2))
            continue

        pb = marketCap / (tangible_Equity / exRate)
        pCfo = marketCap / (cfo / exRate)
        print("MV, cfo", roundB(marketCap, 2), roundB(cfo, 2))

        if pCfo > 6:
            print(comp, 'p/cfo > 6', pCfo)
            continue

        revenue = getFromDFYearly(incomeStatement, "totalRevenue", yearlyFlag)
        retainedEarningsAssetRatio = retainedEarnings / totalAssets
        cfoAssetRatio = cfo / totalAssets

        data52w = data.loc[data.index > ONE_YEAR_AGO]
        percentile = 100.0 * (marketPrice - data52w['low'].min()) / (data52w['high'].max() - data52w['low'].min())
        low_52wk = data52w['low'].min()
        medianDollarVol = statistics.median(data[-10:]['close'] * data[-10:]['volume']) / 5

        try:
            insiderPerc = float(si.get_holders(comp).get('Major Holders')[0][0].rstrip("%"))
            print("insider percent", insiderPerc)
        except Exception as e:
            print(e)
            insiderPerc = 0

        divs = si.get_dividends(comp)

        divSum = divs['dividend'].sum() if not divs.empty else 0
        startToNow = (datetime.today() - data.index[0]).days / 365.25
        divYieldAll = (divSum / startToNow) / marketPrice

        divsPastYear = divs.loc[divs.index > ONE_YEAR_AGO]
        divSumPastYear = divsPastYear['dividend'].sum() if not divsPastYear.empty else 0
        divLastYearYield = divSumPastYear / marketPrice

        if divSumPastYear == 0:
            print(comp, "div is 0 ")
            continue

        schloss = pb < 1 and marketPrice < low_52wk * 1.1 and insiderPerc > INSIDER_OWN_MIN
        netnetRatio = (cash + receivables * 0.8 + inventory * 0.5) / (totalLiab + exRate * marketCap)
        netnet = (cash + receivables * 0.8 + inventory * 0.5 - totalLiab) / exRate > marketCap
        magic6 = pCfo < 6 and (divYieldAll >= 0.06 or divLastYearYield >= 0.06)
        pureHighYield = (divYieldAll >= 0.06 or divLastYearYield >= 0.06)

        print('pb, pcfo, divyield', pb, pCfo, divYieldAll, magic6)
        print('netnet ratio',
              round((cash + receivables * 0.8 + inventory * 0.5 - totalLiab) / exRate / marketCap, 2))

        if schloss or netnet or magic6 or pureHighYield:
            outputString = comp[:4] + " " + " " + companyName[:4] + ' ' \
                           + " day$Vol:" + str(round(medianDollarVol / 1000000, 1)) + "M " \
                           + country.replace(" ", "_") + " " \
                           + sector.replace(" ", "_") + " " + listingCurrency + bsCurrency \
                           + boolToString(schloss, "schloss") + boolToString(netnet, "netnet") \
                           + boolToString(magic6, "magic6") + boolToString(pureHighYield, 'pureHighYield') \
                           + " MV:" + str(roundB(marketCap, 1)) + 'B' \
                           + " BV:" + str(roundB(tangible_Equity / exRate, 1)) + 'B' \
                           + " P/CFO:" + str(round(pCfo, 2)) \
                           + " P/B:" + str(round(pb, 1)) \
                           + " C/R:" + str(round(currRatio, 2)) \
                           + " D/E:" + str(round(debtEquityRatio, 2)) \
                           + " RetEarning/A:" + str(round(retainedEarningsAssetRatio, 2)) \
                           + " S/A:" + str(round(revenue / totalAssets, 2)) \
                           + " cfo/A:" + str(round(cfoAssetRatio, 2)) \
                           + " P/52wLow:" + str(round(marketPrice / low_52wk, 2)) \
                           + " divYldLastYr:" + str(round(divLastYearYield * 100)) + "%" \
                           + " divYldAll:" + str(round(divYieldAll * 100)) + "%" \
                           + " insider%:" + str(round(insiderPerc)) + "%"

            print(outputString)
            fileOutput.write(outputString + '\n')
            fileOutput.flush()
        # else:
        #     print("None " + companyName + ' nnRatio:' + str(round(netnetRatio, 2)) +
        #           " MV:" + str(roundB(marketCap, 1)) + 'B'
        #           + " BV:" + str(roundB(tangible_Equity / exRate, 1)) + 'B'
        #           + " P/CFO:" + str(round(pCfo, 2))
        #           + " P/B:" + str(round(pb, 1))
        #           + " C/R:" + str(round(currRatio, 2))
        #           + " D/E:" + str(round(debtEquityRatio, 2))
        #           + " RetEarning/A:" + str(round(retainedEarningsAssetRatio, 2))
        #           + " S/A:" + str(round(revenue / totalAssets, 2))
        #           + " cfo/A:" + str(round(cfoAssetRatio, 2))
        #           + " 52w_p%:" + str(round(percentile))
        #           + " divYld:" + str(round(divLastYearYield * 100)) + "%"
        #           + " divAll:" + str(round(divYieldAll * 100)) + "%"
        #           + " insider%:" + str(round(insiderPerc)) + "%"
        #           + " dai$Vol:" + str(round(avgDollarVol / 1000000, 2)) + "M")

    except Exception as e:
        print(comp, "exception", e)
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)

        fileOutput.flush()
