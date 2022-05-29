import statistics
from datetime import datetime, timedelta
import sys, os
import yahoo_fin.stock_info as si
import pandas as pd
from Market import Market
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
# listStocks = ['2127.HK']
# stock_df_torun = pd.read_csv('list_special', dtype=object, sep=" ", index_col=False, names=['ticker'])
# stock_df_torun['ticker'] = stock_df_torun['ticker'].map(lambda x: convertHK(x))
# listStocks = stock_df_torun['ticker'].tolist()

print(len(listStocks), listStocks)

for comp in listStocks:
    print("_____________________________")
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

        if 'real estate' in sector.lower() or 'financial' in sector.lower() or 'technology' in sector.lower():
            print(comp, " no real estate or financial or tech ", sector)
            continue

        quoteData = si.get_quote_data(comp)
        yahooPE = quoteData["trailingPE"] if 'trailingPE' in quoteData else 1000

        # if yahooPE > 6:
        #     print(comp, 'yahoo trailing PE > 6')
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

        if currRatio <= 0.5:
            print(comp, "curr ratio < 0.5", currRatio)
            continue

        totalAssets = getFromDF(bs, "totalAssets")
        totalLiab = getFromDF(bs, "totalLiab")
        goodWill = getFromDF(bs, 'goodWill')
        intangibles = getFromDF(bs, 'intangibleAssets')
        tangible_Equity = totalAssets - totalLiab - goodWill - intangibles

        # if tangible_Equity < 0:
        #     print(comp, " tangible equity < 0 ", tangible_Equity)
        #     continue

        debtEquityRatio = totalLiab / tangible_Equity
        # if debtEquityRatio > 1:
        #     print(comp, "de ratio> 1 ", debtEquityRatio)
        #     continue

        incomeStatement = si.get_income_statement(comp, yearly=yearlyFlag)
        netIncome = getFromDFYearly(incomeStatement, "netIncome", yearlyFlag)

        cf = si.get_cash_flow(comp, yearly=yearlyFlag)
        cfo = getFromDFYearly(cf, "totalCashFromOperatingActivities", yearlyFlag)
        dep = getFromDFYearly(cf, "depreciation", yearlyFlag)
        capex = getFromDFYearly(cf, "capitalExpenditures", yearlyFlag)

        print(comp, 'cfo, dep', cfo, dep)

        # if cfo <= 0 or cfo < dep:
        #     print(comp, "cfo <= 0 or cfo < dep ", cfo, dep)
        #     continue

        if cfo <= 0:
            print(comp, "cfo <= 0", cfo, dep)
            continue

        shares = hk_shares[hk_shares['ticker'] == comp]['shares'].item()

        listingCurrency = 'HKD'
        bsCurrency = si.get_quote_data(comp)['financialCurrency']
        # print("listing currency, bs currency, ", listingCurrency, bsCurrency)
        exRate = currency_getExchangeRate.getExchangeRate(exchange_rate_dict, listingCurrency, bsCurrency)

        marketCap = si.get_quote_data(comp)['marketCap']
        marketPrice = si.get_live_price(comp)
        marketCap2 = marketPrice * shares

        netnetRatio = (cash + receivables * 0.8 + inventory * 0.5) / (totalLiab + exRate * marketCap)

        manualPE = marketCap * exRate / netIncome
        print('marketcap 1 2 ', marketCap, marketCap2, 'ratio', marketCap / marketCap2)

        print(comp, 'manual pe', manualPE, 'yahoo PE', yahooPE)

        if manualPE > 20 or manualPE < 0:
            print(comp, "manual pe > 10", manualPE)
            continue
        # if marketCap < 1000000000:
        #     print(comp, "market cap < 1B TOO SMALL", roundB(marketCap, 2))
        #     continue

        fcf = cfo - dep
        pb1 = marketCap * exRate / tangible_Equity
        pFcf = marketCap * exRate / fcf
        print('mc, exrate, cfo, dep fcf', marketCap, exRate, cfo, dep, cfo - dep)

        pb = quoteData['priceToBook'] if 'priceToBook' in quoteData else 1000

        if pb1 > 1:
            print(comp, 'pb > 1', pb)
            continue

        print("MV, cfo", roundB(marketCap, 2), roundB(cfo, 2))

        if pFcf > 5 or pFcf < 0:
            print(comp, 'p/fcf > 5', pFcf)
            continue

        revenue = getFromDFYearly(incomeStatement, "totalRevenue", yearlyFlag)
        retainedEarningsAssetRatio = retainedEarnings / totalAssets
        fcfAssetRatio = fcf / totalAssets

        priceData = si.get_data(comp, interval=PRICE_INTERVAL)
        print("date start date ", priceData.index[0].strftime('%-m/%-d/%Y'))
        print('last active day', priceData[priceData['volume'] != 0].index[-1].strftime('%-m/%-d/%Y'))

        # data52w = priceData.loc[priceData.index > ONE_YEAR_AGO]
        # percentile = 100.0 * (marketPrice - data52w['low'].min()) / (data52w['high'].max() - data52w['low'].min())
        low_52wk = quoteData['fiftyTwoWeekLow'] if 'fiftyTwoWeekLow' in quoteData else 0
        medianDollarVol = statistics.median(priceData[-10:]['close'] * priceData[-10:]['volume']) / 5
        print(comp, 'vol is ', medianDollarVol)

        if medianDollarVol < 500000:
            print(comp, 'vol too small', medianDollarVol)
            continue

        print(comp, 'low52week', low_52wk, 'price/52weeklow', marketPrice / low_52wk)

        divRateYahoo = quoteData['trailingAnnualDividendYield'] \
            if 'trailingAnnualDividendRate' in quoteData else 0

        try:
            insiderPerc = float(si.get_holders(comp).get('Major Holders')[0][0].rstrip("%"))
            print("insider percent", insiderPerc)
        except Exception as e:
            print(e)
            insiderPerc = 0

        divs = si.get_dividends(comp)

        yearSpan = 2021 - priceData[:1].index.item().year + 1
        divPrice = pd.merge(divs.groupby(by=lambda d: d.year)['dividend'].sum(),
                            priceData.groupby(by=lambda d: d.year)['close'].mean(),
                            left_index=True, right_index=True)
        divPrice['yield'] = divPrice['dividend'] / divPrice['close']
        divYieldAll = divPrice[divPrice.index != 2022]['yield'].sum() / yearSpan \
            if not divPrice[divPrice.index != 2022].empty else 0
        divLastYearYield = divPrice.loc[2021]['yield'] if 2021 in divPrice.index else 0
        print('yield all', divYieldAll, 'lastyear', divLastYearYield)

        schloss = pb < 1 and marketPrice < low_52wk * 1.1 and insiderPerc > INSIDER_OWN_MIN
        netnetRatio = (cash + receivables * 0.8 + inventory * 0.5) / (totalLiab + exRate * marketCap)
        netnet = (cash + receivables * 0.8 + inventory * 0.5 - totalLiab) / exRate > marketCap
        magic6 = manualPE < 6 and divRateYahoo >= 0.06 and pb < 0.6
        peDiv = manualPE < 6 and divRateYahoo >= 0.06
        pureHighYield = divRateYahoo >= 0.06

        # if (netnetRatio < 0.5):
        #     print('netnet ratio < 0.5', netnetRatio)
        #     continue

        print('pb, pfcf, divyield', pb, pFcf, divYieldAll, magic6)
        print('netnet ratio', round(netnetRatio, 2))

        if schloss or netnet or magic6 or peDiv or pureHighYield:
            outputString = comp[:4] + " " + " " + companyName[:4] + ' ' \
                           + " dai$Vol:" + str(round(medianDollarVol / 1000000, 1)) + "M " \
                           + country.replace(" ", "_") + " " \
                           + sector.replace(" ", "_") + " " + listingCurrency + bsCurrency \
                           + boolToString(schloss, "schloss") + boolToString(netnet, "netnet") \
                           + boolToString(magic6, "magic6") + boolToString(peDiv, "PE+DIV") \
                           + boolToString(pureHighYield, 'pureHighYield') \
                           + " netnetRatio:" + str(round(netnetRatio, 1)) \
                           + " MV:" + str(roundB(marketCap, 1)) + 'B' \
                           + " BV:" + str(roundB(tangible_Equity / exRate, 1)) + 'B' \
                           + " P/FCF:" + str(round(pFcf, 1)) \
                           + " DEP/CFO:" + str(round(dep / cfo, 2)) \
                           + " CAPEX/CFO:" + str(round(capex / cfo, 2)) \
                           + " P/B:" + str(round(pb, 1)) \
                           + " C/R:" + str(round(currRatio, 2)) \
                           + " D/E:" + str(round(debtEquityRatio, 2)) \
                           + " RetEarning/A:" + str(round(retainedEarningsAssetRatio, 2)) \
                           + " S/A:" + str(round(revenue / totalAssets, 2)) \
                           + " fcf/A:" + str(round(fcfAssetRatio, 2)) \
                           + " P/52wLow:" + str(round(marketPrice / low_52wk, 2)) \
                           + " divYldLastYr:" + str(round(divLastYearYield * 100)) + "%" \
                           + " divYldAll:" + str(round(divYieldAll * 100)) + "%" \
                           + " insider%:" + str(round(insiderPerc)) + "%" \
                           + " yahooPE:" + str(round(yahooPE, 2)) \
                           + " manual PE:" + str(round(manualPE, 2)) + ' PB:' \
                           + str(round(pb, 2)) + " div:" + str(round(divRateYahoo * 100, 2)) + '%'

            # else:
            #     outputString = "nothing:" + comp[:4] + " " + " " + companyName[:4] + ' ' \
            #                    + " yahoo pe:" + str(round(yahooPE, 2)) \
            #                    + " manual pe:" + str(round(manualPE, 2)) \
            #                    + ' pb:' + str(round(pb, 2)) \
            #                    + ' netnetRatio:' + str(round(netnetRatio, 2)) \
            #                    + " div:" + str(round(divRateYahoo * 100, 2)) + '%'

            print(outputString)
            fileOutput.write(outputString + '\n')
            fileOutput.flush()

    except Exception as e:
        print(comp, "exception", e)
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)

        fileOutput.flush()
