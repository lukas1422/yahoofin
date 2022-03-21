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
# PRICE_START_DATE = (datetime.today() - timedelta(weeks=52 * 2)).strftime('%-m/%-d/%Y')
TEN_YEAR_AGO = (datetime.today() - timedelta(weeks=52 * 10)).strftime('%-m/%-d/%Y')
# DIV_START_DATE =
PRICE_INTERVAL = '1wk'

exchange_rate_dict = currency_getExchangeRate.getExchangeRateDict()

fileOutput = open('list_results_hk', 'w')

stock_df = pd.read_csv('list_HK_Tickers', dtype=object, sep=" ", index_col=False, names=['ticker', 'name'])
stock_df['ticker'] = stock_df['ticker'].astype(str)
stock_df['ticker'] = stock_df['ticker'].map(lambda x: convertHK(x))
hk_shares = pd.read_csv('list_HK_totalShares', sep=" ", index_col=False, names=['ticker', 'shares'])
listStocks = stock_df['ticker'].tolist()


# stock_df_torun = pd.read_csv('list_special', dtype=object, sep=" ", index_col=False, names=['ticker'])
# stock_df_torun['ticker'] = stock_df_torun['ticker'].map(lambda x: convertHK(x))
# listStocks = ['0321.HK']

print(len(listStocks), listStocks)

for comp in listStocks:

    try:
        companyName = stock_df.loc[stock_df['ticker'] == comp]['name'].item()

        print(increment(), comp, companyName)

        data = si.get_data(comp, start_date=TEN_YEAR_AGO, interval=PRICE_INTERVAL)
        print("start date ", data.index[0].strftime('%-m/%-d/%Y'))
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

        # if 'real estate' in sector.lower() or 'financial' in sector.lower():
        #     print(comp, " no real estate or financial ", sector)
        #     continue

        marketPrice = si.get_live_price(comp)
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

        currAssets = getFromDF(bs, "totalCurrentAssets")
        currLiab = getFromDF(bs, "totalCurrentLiabilities")

        cash = getFromDF(bs, "cash")
        receivables = getFromDF(bs, 'netReceivables')
        inventory = getFromDF(bs, 'inventory')

        currRatio = (cash + 0.5 * receivables + 0.2 * inventory) / currLiab

        # if currRatio <= 1:
        #     print(comp, "curr ratio < 1", currRatio)
        #     continue

        totalAssets = getFromDF(bs, "totalAssets")
        totalLiab = getFromDF(bs, "totalLiab")
        goodWill = getFromDF(bs, 'goodWill')
        intangibles = getFromDF(bs, 'intangibleAssets')
        tangible_Equity = totalAssets - totalLiab - goodWill - intangibles
        debtEquityRatio = totalLiab / tangible_Equity

        # if debtEquityRatio > 1:
        #     print(comp, "de ratio> 1. ", debtEquityRatio)
        #     continue

        incomeStatement = si.get_income_statement(comp, yearly=yearlyFlag)

        cf = si.get_cash_flow(comp, yearly=yearlyFlag)
        cfo = getFromDFYearly(cf, "totalCashFromOperatingActivities", yearlyFlag)

        if cfo <= 0:
            print(comp, "cfo <= 0 ", cfo)
            continue

        shares = hk_shares[hk_shares['ticker'] == comp]['shares'].item()

        listingCurrency = getListingCurrency(comp)
        bsCurrency = getBalanceSheetCurrency(comp, listingCurrency)
        print("listing currency, bs currency, ", listingCurrency, bsCurrency)
        exRate = currency_getExchangeRate.getExchangeRate(exchange_rate_dict, listingCurrency, bsCurrency)

        marketCap = marketPrice * shares
        if marketCap < 1000000000:
            print(comp, "market cap < 1B TOO SMALL", roundB(marketCap, 2))
            continue

        pb = marketCap / (tangible_Equity / exRate)
        pCfo = marketCap / (cfo / exRate)
        print("MV, cfo", roundB(marketCap, 2), roundB(cfo, 2))

        # if pb >= 0.6 or pb <= 0:
        #     print(comp, 'pb > 0.6 or pb <= 0', pb)
        #     continue
        #
        # if pCfo > 6 or pCfo <= 0:
        #     print(comp, 'pcfo > 6 or <= 0', pCfo)
        #     continue

        revenue = getFromDFYearly(incomeStatement, "totalRevenue", yearlyFlag)
        retainedEarningsAssetRatio = retainedEarnings / totalAssets
        cfoAssetRatio = cfo / totalAssets
        # ebitAssetRatio = ebit / totalAssets

        # data = si.get_data(comp, start_date=START_DATE, interval=PRICE_INTERVAL)
        data52w = data.loc[data.index > ONE_YEAR_AGO]
        percentile = 100.0 * (marketPrice - data52w['low'].min()) / (data52w['high'].max() - data52w['low'].min())
        low_52wk = data52w['low'].min()
        avgDollarVol = (data[-10:]['close'] * data[-10:]['volume']).sum() / 10

        try:
            insiderPerc = float(si.get_holders(comp).get('Major Holders')[0][0].rstrip("%"))
            print("insider percent", insiderPerc)
        except Exception as e:
            print(e)
            insiderPerc = 0

        # divs = si.get_dividends(comp, start_date=START_DATE)
        divs = si.get_dividends(comp)

        divsPastYear = divs.loc[divs.index > ONE_YEAR_AGO]
        divSumPastYear = divsPastYear['dividend'].sum() if not divsPastYear.empty else 0
        divLastYearYield = divSumPastYear / marketPrice

        div10Yr = divs.loc[divs.index > TEN_YEAR_AGO]
        div10YrSum = div10Yr['dividend'].sum() if not div10Yr.empty else 0
        startToNow = (datetime.today() - data.index[0]).days / 365.25
        div10YearYield = (div10YrSum / startToNow) / marketPrice

        if divSumPastYear == 0:
            print(comp, "div is 0 ")
            continue

        schloss = pb < 0.6 and marketPrice < low_52wk * 1.1 and insiderPerc > INSIDER_OWN_MIN
        netnetRatio = (cash + receivables * 0.5 + inventory * 0.2 - totalLiab) / exRate / marketCap
        netnet = (cash + receivables * 0.5 + inventory * 0.2 - totalLiab) / exRate - marketCap > 0
        magic6 = pb < 0.6 and pCfo < 6 and div10YearYield >= 0.06
        print('pb, pcfo, divyield', pb, pCfo, div10YearYield, magic6)

        if schloss or netnet or magic6:
            outputString = comp[:4] + " " + " " + companyName[:4] + ' ' \
                           + country.replace(" ", "_") + " " \
                           + sector.replace(" ", "_") + " " + listingCurrency + bsCurrency \
                           + boolToString(schloss, "schloss") + boolToString(netnet, "netnet") \
                           + boolToString(magic6, "magic6") \
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
                           + " divYld:" + str(round(divLastYearYield * 100)) + "%" \
                           + " divYld10yr:" + str(round(div10YearYield * 100)) + "%" \
                           + " insider%:" + str(round(insiderPerc)) + "%" \
                           + " dai$Vol:" + str(round(avgDollarVol / 1000000, 2)) + "M"

            print(outputString)
            fileOutput.write(outputString + '\n')
            fileOutput.flush()
        else:
            # print(" not a schloss, netnet or magic6")
            print("None " + companyName + ' nnRatio:' + str(round(netnetRatio, 2)) +
                  " MV:" + str(roundB(marketCap, 1)) + 'B'
                  + " BV:" + str(roundB(tangible_Equity / exRate, 1)) + 'B'
                  + " P/CFO:" + str(round(pCfo, 2))
                  + " P/B:" + str(round(pb, 1))
                  + " C/R:" + str(round(currRatio, 2))
                  + " D/E:" + str(round(debtEquityRatio, 2))
                  + " RetEarning/A:" + str(round(retainedEarningsAssetRatio, 2))
                  + " S/A:" + str(round(revenue / totalAssets, 2))
                  + " cfo/A:" + str(round(cfoAssetRatio, 2))
                  + " 52w_p%:" + str(round(percentile))
                  + " divYld:" + str(round(divSumPastYear / marketPrice * 100)) + "%"
                  + " insider%:" + str(round(insiderPerc)) + "%"
                  + " dai$Vol:" + str(round(avgDollarVol / 1000000, 2)) + "M")

    except Exception as e:
        print(comp, "exception", e)
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)

        fileOutput.flush()
