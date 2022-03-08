import os
import sys
from datetime import datetime
import yahoo_fin.stock_info as si
from currency_scrapeYahoo import getBalanceSheetCurrency
from currency_scrapeYahoo import getListingCurrency
import currency_getExchangeRate
import scrape_sharesOutstanding
from helperMethods import getFromDF, getFromDFYearly, roundB

START_DATE = '3/1/2020'
# DIVIDEND_START_DATE = '1/1/2010'
PRICE_INTERVAL = '1d'


def fo(number):
    return str(f"{number:,}")


exchange_rate_dict = currency_getExchangeRate.getExchangeRateDict()

stockName = '2127.HK'
yearlyFlag = False
try:
    data = si.get_data(stockName, start_date=START_DATE, interval=PRICE_INTERVAL)
    try:
        info = si.get_company_info(stockName)
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
    totalCurrentLiab = getFromDF(bs, "totalCurrentLiabilities")
    totalAssets = getFromDF(bs, "totalAssets")
    totalLiab = getFromDF(bs, "totalLiab")
    intangibles = getFromDF(bs, 'intangibleAssets')
    goodWill = getFromDF(bs, 'goodWill')

    netAssets = totalAssets - totalLiab
    tangible_equity = totalAssets - totalLiab - goodWill - intangibles
    cash = getFromDF(bs, 'cash')
    receivables = getFromDF(bs, 'netReceivables')
    inventory = getFromDF(bs, 'inventory')

    print("goodwill is ", goodWill)

    incomeStatement = si.get_income_statement(stockName, yearly=yearlyFlag)
    print("income statement date:", incomeStatement.columns[0].strftime('%Y/%-m/%-d'))

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

    # print("cfo is ", round(cfo / 1000000000, 2), "B")

    marketPrice = si.get_live_price(stockName)

    sharesTotalXueqiu = scrape_sharesOutstanding.scrapeTotalSharesXueqiu(stockName)
    floatingSharesXueqiu = scrape_sharesOutstanding.scrapeFloatingSharesXueqiu(stockName)
    sharesFinviz = scrape_sharesOutstanding.scrapeSharesOutstandingFinviz(stockName)
    sharesYahoo = si.get_quote_data(stockName)['sharesOutstanding']
    print('xueqiu total shares', sharesTotalXueqiu)
    print('xueqiu floating shares', floatingSharesXueqiu)
    print('finviz shares', sharesFinviz)
    print("yahoo shares ", sharesYahoo)
    if stockName.lower().endswith('hk'):
        shares = sharesTotalXueqiu
        print(" using xueqiu shares ", shares)
    elif sharesYahoo != 0.0:
        shares = sharesYahoo
        print(" using yahoo shares ", shares)
    else:
        shares = sharesFinviz
        print(" using finviz shares ", shares)

    marketCap = marketPrice * shares
    currentRatio = totalCurrentAssets / totalCurrentLiab
    debtEquityRatio = totalLiab / tangible_equity
    retainedEarningsAssetRatio = retainedEarnings / totalAssets
    cfoAssetRatio = cfo / totalAssets
    ebitAssetRatio = ebit / totalAssets

    pCFO = marketCap / cfo
    pTangibleEquity = marketCap / (tangible_equity / exRate)
    tangibleRatio = tangible_equity / (totalAssets - totalLiab)
    divs = si.get_dividends(stockName, start_date=START_DATE)
    startToNow = (datetime.today() - data.index[0]).days / 365.25
    print(" start to now ", startToNow, 'starting date ', data.index[0])

    avgDollarVol = (data[-10:]['close'] * data[-10:]['volume']).sum() / 10

    percentile = 100.0 * (marketPrice - data['low'].min()) / (data['high'].max() - data['low'].min())

    divSum = divs['dividend'].sum() if not divs.empty else 0.0

    # PRINTING*****

    print("listing Currency:", listingCurr, "balance sheet currency", bsCurrency, "ExRate ", exRate)
    # print("total shares xueqiu", str(roundB(sharesTotalXueqiu, 2)) + "B")
    # print("shares finviz", sharesFinviz)
    print("cash", roundB(cash, 2), "rec", roundB(receivables, 2), "inv",
          roundB(inventory, 2))
    print("A", roundB(totalAssets / exRate, 1), "B", "(",
          roundB(totalCurrentAssets / exRate, 1)
          , roundB((totalAssets - totalCurrentAssets) / exRate, 1), ")")
    print("L", roundB(totalLiab / exRate, 1), "B", "(",
          roundB(totalCurrentLiab / exRate, 1),
          roundB((totalLiab - totalCurrentLiab) / exRate, 1), ")")
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
    print("CR", round(totalCurrentAssets / totalCurrentLiab, 2))
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
    print("div annual yield:", round(divSum / marketPrice * 100 / startToNow), "%")
    print("divsum marketprice:", round(divSum, 2), round(marketPrice, 2))
    # print('roa', roa)
    print("P/CFO", round(marketCap / (cfo / exRate), 2))
    print('cfo/A', cfoA)

    outputString = stockName + " " + country + " " + sector \
                   + " MV:" + str(round(marketCap / 1000000000.0, 1)) + 'B' \
                   + " NetAssets:" + str(round((totalAssets - totalLiab) / exRate / 1000000000.0, 1)) + 'B' \
                   + " pb:" + str(round(pTangibleEquity, 2)) \
                   + " CR:" + str(round(currentRatio, 2)) \
                   + " D/E:" + str(round(debtEquityRatio, 2)) \
                   + " RE/A:" + str(round(retainedEarningsAssetRatio, 2)) \
                   + " cfo/A:" + str(round(cfoAssetRatio, 2)) \
                   + " ebit/A:" + str(round(ebitAssetRatio, 2)) \
                   + " tangibleRatio:" + str(round(tangibleRatio, 2)) \
                   + " 52w_p%:" + str(round(percentile)) \
                   + " divYld%:" + str(round(divSum / marketPrice * 100 / startToNow, 1)) + "%" \
                   + " dai$Vol:" + str(round(avgDollarVol / 1000000, 2)) + "M"

    print(outputString)
except Exception as e:
    print(e)
    print(data[-10:])
    print(stockName, "exception", e)
    exc_type, exc_obj, exc_tb = sys.exc_info()
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    print(exc_type, fname, exc_tb.tb_lineno)
