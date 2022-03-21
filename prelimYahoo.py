stockName = 'PDD'
yearlyFlag = False

import os
import sys
from datetime import datetime, timedelta
import yahoo_fin.stock_info as si
from currency_scrapeYahoo import getBalanceSheetCurrency
from currency_scrapeYahoo import getListingCurrency
import currency_getExchangeRate
import scrape_sharesOutstanding
from helperMethods import getFromDF, getFromDFYearly, roundB

ONE_YEAR_AGO = datetime.today() - timedelta(weeks=53)
# PRICE_START_DATE = (datetime.today() - timedelta(weeks=52 * 2)).strftime('%-m/%-d/%Y')
TEN_YEAR_AGO = (datetime.today() - timedelta(weeks=52 * 10)).strftime('%-m/%-d/%Y')

# yearAgo = datetime.today() - timedelta(weeks=53)
START_DATE = (datetime.today() - timedelta(weeks=52 * 10)).strftime('%-m/%-d/%Y')
# START_DATE = '3/1/2020'
# DIVIDEND_START_DATE = '1/1/2010'
PRICE_INTERVAL = '1wk'


def fo(number):
    return str(f"{number:,}")


exchange_rate_dict = currency_getExchangeRate.getExchangeRateDict()

# stockName = '600519.SS'
# stockName = '000815.SZ'


try:
    data = si.get_data(stockName, start_date=START_DATE, interval=PRICE_INTERVAL)
    print('last trading day', data[data['volume'] != 0].index[-1])

    try:
        info = si.get_company_info(stockName)
        insiderPerc = float(si.get_holders(stockName).get('Major Holders')[0][0].rstrip("%"))
        print(stockName, "insider percent", insiderPerc)
    except Exception as e:
        print(e)
        print(data[-10:])
        info = ""
        print(stockName, "exception", e)
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)

    country = getFromDF(info, "country")
    sector = getFromDF(info, 'sector')
    industry = getFromDF(info, 'industry')
    longName = getFromDF(info, 'longBusinessSummary')

    # insiderPerc = float(si.get_holders(stockName).get('Major Holders')[0][0].rstrip("%"))
    # print(stockName, country, sector, industry, insiderPerc)

    print(longName)

    bs = si.get_balance_sheet(stockName, yearly=yearlyFlag)
    print("balance sheet date:", bs.columns[0].strftime('%Y/%-m/%-d'))
    print("bs cols", bs.columns)

    retainedEarnings = getFromDF(bs, "retainedEarnings")
    totalCurrentAssets = getFromDF(bs, "totalCurrentAssets")
    currLiab = getFromDF(bs, "totalCurrentLiabilities")
    totalAssets = getFromDF(bs, "totalAssets")
    totalLiab = getFromDF(bs, "totalLiab")
    intangibles = getFromDF(bs, 'intangibleAssets')
    goodWill = getFromDF(bs, 'goodWill')

    netAssets = totalAssets - totalLiab
    tangible_equity = totalAssets - totalLiab - goodWill - intangibles
    cash = getFromDF(bs, 'cash')
    receivables = getFromDF(bs, 'netReceivables')
    inventory = getFromDF(bs, 'inventory')

    currRatio = (cash + receivables * 0.5 + inventory * 0.2) / currLiab
    print("current ratio components cash", roundB(cash, 2), 'rec', roundB(receivables, 2), 'inv', roundB(inventory, 2),
          'currL', roundB(currLiab, 2))

    incomeStatement = si.get_income_statement(stockName, yearly=yearlyFlag)
    print("income statement date:", incomeStatement.columns[0].strftime('%Y/%-m/%-d'))

    print("goodwill is ", goodWill)

    listingCurr = getListingCurrency(stockName)
    bsCurrency = getBalanceSheetCurrency(stockName, listingCurr)
    exRate = currency_getExchangeRate.getExchangeRate(exchange_rate_dict, listingCurr, bsCurrency)

    revenue = getFromDFYearly(incomeStatement, "totalRevenue", yearlyFlag)
    ebit = getFromDFYearly(incomeStatement, "ebit", yearlyFlag)
    netIncome = getFromDFYearly(incomeStatement, 'netIncome', yearlyFlag)

    # roa = netIncome / totalAssets

    # CF
    cf = si.get_cash_flow(stockName, yearly=yearlyFlag)
    print("cash flow statement date:", cf.columns[0].strftime('%Y/%-m/%-d'))
    # print("CF cols", cf.loc['totalCashFromOperatingActivities'])

    cfo = getFromDFYearly(cf, "totalCashFromOperatingActivities", yearlyFlag)
    cfi = getFromDFYearly(cf, "totalCashflowsFromInvestingActivities", yearlyFlag)
    cff = getFromDFYearly(cf, "totalCashFromFinancingActivities", yearlyFlag)

    cfoA = cfo / totalAssets

    print("cfo is ", round(cfo / 1000000000, 2), "B")

    marketPrice = si.get_live_price(stockName)

    sharesTotalXueqiu = scrape_sharesOutstanding.scrapeTotalSharesXueqiu(stockName)
    floatingSharesXueqiu = scrape_sharesOutstanding.scrapeFloatingSharesXueqiu(stockName)
    sharesFinviz = scrape_sharesOutstanding.scrapeSharesOutstandingFinviz(stockName)
    sharesYahoo = si.get_quote_data(stockName)['sharesOutstanding']
    print('xueqiu total shares', sharesTotalXueqiu)
    print('xueqiu floating shares', floatingSharesXueqiu)
    print('finviz shares', sharesFinviz)
    print("yahoo shares ", sharesYahoo)
    if stockName.lower().endswith('hk') and sharesTotalXueqiu != 0:
        shares = sharesTotalXueqiu
        print(" using xueqiu shares ", shares)
    elif sharesYahoo != 0.0:
        shares = sharesYahoo
        print(" using yahoo shares ", shares)
    else:
        shares = sharesFinviz
        print(" using finviz shares ", shares)

    marketCap = marketPrice * shares
    # currentRatio = totalCurrentAssets / totalCurrentLiab
    debtEquityRatio = totalLiab / tangible_equity
    retainedEarningsAssetRatio = retainedEarnings / totalAssets
    cfoAssetRatio = cfo / totalAssets
    ebitAssetRatio = ebit / totalAssets

    pCFO = marketCap / cfo
    pTangibleEquity = marketCap / (tangible_equity / exRate)
    tangibleRatio = tangible_equity / (totalAssets - totalLiab)

    divs = si.get_dividends(stockName)
    divsPastYear = divs.loc[divs.index > ONE_YEAR_AGO]
    divSumPastYear = divsPastYear['dividend'].sum() if not divsPastYear.empty else 0
    divLastYearYield = divSumPastYear / marketPrice

    div10Yr = divs.loc[divs.index > TEN_YEAR_AGO]
    div10YrSum = div10Yr['dividend'].sum() if not div10Yr.empty else 0
    startToNow = (datetime.today() - data.index[0]).days / 365.25
    div10YearYield = (div10YrSum / startToNow) / marketPrice
    # startToNow = (datetime.today() - data.index[0]).days / 365.25
    # print(" start to now ", startToNow, 'starting date ', data.index[0].strftime('%Y/%-m/%-d'))

    avgDollarVol = (data[-10:]['close'] * data[-10:]['volume']).sum() / 10

    data52w = data.loc[data.index > ONE_YEAR_AGO]

    percentile = 100.0 * (marketPrice - data52w['low'].min()) \
                 / (data52w['high'].max() - data52w['low'].min())

    divsPastYear = divs.loc[divs.index > ONE_YEAR_AGO]
    divSumPastYear = divsPastYear['dividend'].sum() if not divsPastYear.empty else 0
    print('divsum marketPrice', divSumPastYear, marketPrice)

    # divSum = divs['dividend'].sum() if not divs.empty else 0.0
    if not divs.empty:
        print('div history ', divs)
    else:
        print('div is empty ')

    # PRINTING*****

    print("listing Currency:", listingCurr, "bs currency:", bsCurrency, "ExRate:", exRate)
    # print("total shares xueqiu", str(roundB(sharesTotalXueqiu, 2)) + "B")
    # print("shares finviz", sharesFinviz)
    print("cash", roundB(cash / exRate, 2), "rec", roundB(receivables / exRate, 2), "inv",
          roundB(inventory / exRate, 2))
    print("A", roundB(totalAssets / exRate, 1), "B", "(",
          roundB(totalCurrentAssets / exRate, 1)
          , roundB((totalAssets - totalCurrentAssets) / exRate, 1), ")")
    print("L", roundB(totalLiab / exRate, 1), "B", "(",
          roundB(currLiab / exRate, 1),
          roundB((totalLiab - currLiab) / exRate, 1), ")")
    print("E", round((totalAssets - totalLiab) / exRate / 1000000000.0, 1), "B")
    print("Market Cap", str(round(marketPrice * shares / 1000000000.0, 1)) + "B")

    print("PER SHARE:")
    print("Market price", round(marketPrice, 2), listingCurr)
    print("Tangible Equity per share", round(tangible_equity / exRate / shares, 2), listingCurr)

    # print("Eq USD", round((equity / exRate) / 1000000000.0), "B")

    print("P/NetAssets", round(marketPrice * shares / (netAssets / exRate), 2))
    print("P/Tangible Equity", round(marketPrice * shares / (tangible_equity / exRate), 2))
    print("P/E", round(marketPrice * shares / (netIncome / exRate), 2))
    print("P/CFO", round(marketPrice * shares / (cfo / exRate), 2))
    print("S/B", round(revenue / tangible_equity, 2))
    print("                         ")
    print("********ALTMAN**********")
    print("CR", round(currRatio, 2))
    print("tangible ratio", round(tangible_equity / (totalAssets - totalLiab), 2))
    print("D/E", round(totalLiab / tangible_equity, 2))
    print("EBIT", round(ebit / exRate / 1000000000, 2), "B")
    print("netIncome", round(netIncome / exRate / 1000000000, 2), "B")
    print("CFO", round(cfo / exRate / 1000000000, 2), "B")
    print("CFI", round(cfi / exRate / 1000000000, 2), "B")
    print("CFF", round(cff / 1000000000 / exRate, 2), "B")
    print("RE", round(retainedEarnings / 1000000000 / exRate, 2), "B")
    print("RE/A", round(retainedEarnings / totalAssets, 2))
    print("S/A", round(revenue / totalAssets, 2))
    print("div1YrYld:", round(divLastYearYield * 100), "%")
    print("div10YrYld:", round(div10YearYield * 100), "%")
    print("divsum marketprice:", round(divSumPastYear, 2), round(marketPrice, 2))
    # print('roa', roa)
    print("P/CFO", round(marketCap / (cfo / exRate), 2))
    print('cfo/A', cfoA)

    outputString = stockName + " " + country + " " + sector \
                   + " MV:" + str(round(marketCap / 1000000000.0, 1)) + 'B' \
                   + " NetAssets:" + str(round((totalAssets - totalLiab) / exRate / 1000000000.0, 1)) + 'B' \
                   + " pb:" + str(round(pTangibleEquity, 2)) \
                   + " CR:" + str(round(currRatio, 2)) \
                   + " D/E:" + str(round(debtEquityRatio, 2)) \
                   + " RE/A:" + str(round(retainedEarningsAssetRatio, 2)) \
                   + " cfo/A:" + str(round(cfoAssetRatio, 2)) \
                   + " ebit/A:" + str(round(ebitAssetRatio, 2)) \
                   + " tangibleRatio:" + str(round(tangibleRatio, 2)) \
                   + " 52w_p%:" + str(round(percentile)) \
                   + " divYld%:" + str(round(divSumPastYear / marketPrice * 100 / startToNow, 1)) + "%" \
                   + " dai$Vol:" + str(round(avgDollarVol / 1000000, 2)) + "M"

    print(outputString)
except Exception as e:
    print(e)
    print(data[-10:])
    print(stockName, "exception", e)
    exc_type, exc_obj, exc_tb = sys.exc_info()
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    print(exc_type, fname, exc_tb.tb_lineno)
