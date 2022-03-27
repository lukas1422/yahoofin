stockName = 'BCC'
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

# yearAgo = datetime.today() - timedelta(weeks=53)
START_DATE = (datetime.today() - timedelta(weeks=52 * 10)).strftime('%-m/%-d/%Y')
PRICE_INTERVAL = '1wk'


# stockName = '600519.SS'
# stockName = '000815.SZ'

def getResults(stockName):
    exchange_rate_dict = currency_getExchangeRate.getExchangeRateDict()
    try:
        data = si.get_data(stockName, interval=PRICE_INTERVAL)
        print('last trading day', data[data['volume'] != 0].index[-1].strftime('%Y/%-m/%-d'))

        avgVolListingCurrency = (data[-10:]['close'] * data[-10:]['volume']).sum() / 10
        print(' avg vol ', str(round(avgVolListingCurrency / 1000000, 1)) + "M")

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

        print('goodwill', goodWill, round(goodWill / totalAssets * 100), "%", 'intangibles', intangibles,
              round(intangibles / totalAssets * 100), "%")

        netAssets = totalAssets - totalLiab
        tangible_equity = totalAssets - totalLiab - goodWill - intangibles
        cash = getFromDF(bs, 'cash')
        receivables = getFromDF(bs, 'netReceivables')
        inventory = getFromDF(bs, 'inventory')

        listingCurr = getListingCurrency(stockName)
        bsCurrency = getBalanceSheetCurrency(stockName, listingCurr)
        exRate = currency_getExchangeRate.getExchangeRate(exchange_rate_dict, listingCurr, bsCurrency)

        currRatio = (cash + receivables * 0.5 + inventory * 0.2) / currLiab

        incomeStatement = si.get_income_statement(stockName, yearly=yearlyFlag)
        print("income statement date:", incomeStatement.columns[0].strftime('%Y/%-m/%-d'))

        revenue = getFromDFYearly(incomeStatement, "totalRevenue", yearlyFlag)
        ebit = getFromDFYearly(incomeStatement, "ebit", yearlyFlag)
        netIncome = getFromDFYearly(incomeStatement, 'netIncome', yearlyFlag)

        cf = si.get_cash_flow(stockName, yearly=yearlyFlag)
        print("cash flow statement date:", cf.columns[0].strftime('%Y/%-m/%-d'))

        cfo = getFromDFYearly(cf, "totalCashFromOperatingActivities", yearlyFlag)
        cfi = getFromDFYearly(cf, "totalCashflowsFromInvestingActivities", yearlyFlag)
        cff = getFromDFYearly(cf, "totalCashFromFinancingActivities", yearlyFlag)

        cfoA = cfo / totalAssets

        marketPrice = si.get_live_price(stockName)
        shares = si.get_quote_data(stockName)['sharesOutstanding']
        print("yahoo shares ", roundB(shares, 1), "B")

        if bsCurrency == 'CNY':
            sharesTotalXueqiu = scrape_sharesOutstanding.scrapeTotalSharesXueqiu(stockName)
            floatingSharesXueqiu = scrape_sharesOutstanding.scrapeFloatingSharesXueqiu(stockName)
            sharesFinviz = scrape_sharesOutstanding.scrapeSharesOutstandingFinviz(stockName)
            print('xueqiu total shares', sharesTotalXueqiu)
            print('xueqiu floating shares', roundB(floatingSharesXueqiu, 1))
            print('finviz shares', roundB(sharesFinviz, 1))
            if stockName.lower().endswith('hk') and sharesTotalXueqiu != 0:
                shares = sharesTotalXueqiu
                print(" using xueqiu shares ", shares)
            else:
                shares = sharesFinviz
                print(" using finviz shares ", shares)

        marketCap = marketPrice * shares
        debtEquityRatio = totalLiab / tangible_equity
        retainedEarningsAssetRatio = retainedEarnings / totalAssets
        cfoAssetRatio = cfo / totalAssets
        ebitAssetRatio = ebit / totalAssets

        pCFO = marketCap / cfo
        pTangibleEquity = marketCap / (tangible_equity / exRate)
        tangibleRatio = tangible_equity / (totalAssets - totalLiab)

        divs = si.get_dividends(stockName)
        # print('div', divs)
        divsPastYear = divs.loc[divs.index > ONE_YEAR_AGO]
        divSumPastYear = divsPastYear['dividend'].sum() if not divsPastYear.empty else 0
        divLastYearYield = divSumPastYear / marketPrice
        print('div past year yield', divLastYearYield)

        divSumAll = divs['dividend'].sum() if not divs.empty else 0
        startToNow = (datetime.today() - data.index[0]).days / 365.25
        print("Years Since Listing:", round(startToNow), 'starting date ', data.index[0].strftime('%Y/%-m/%-d'))
        divAllTimeYld = divSumAll / startToNow / marketPrice
        print('div all time yld ', divAllTimeYld)

        data52w = data.loc[data.index > ONE_YEAR_AGO]

        percentile = 100.0 * (marketPrice - data52w['low'].min()) \
                     / (data52w['high'].max() - data52w['low'].min())

        # if not divs.empty:
        #     print('div history ', divs)
        # else:
        #     print('div is empty ')

        # PRINTING*****

        print("listing Currency:", listingCurr, "bs currency:", bsCurrency, "ExRate:", exRate)

        print("********* FINANCIALS *********")

        print("current ratio components cash", bsCurrency, roundB(cash, 1), 'rec', roundB(receivables, 1), 'inv',
              roundB(inventory, 1), 'currL', roundB(currLiab, 1))

        print("cash", listingCurr, roundB(cash / exRate, 1), "rec", roundB(receivables / exRate, 1), "inv",
              roundB(inventory / exRate, 1))

        print("A", roundB(totalAssets / exRate, 1), "B", "(",
              roundB(totalCurrentAssets / exRate, 1)
              , roundB((totalAssets - totalCurrentAssets) / exRate, 1), ")")
        print("L", roundB(totalLiab / exRate, 1), "B", "(",
              roundB(currLiab / exRate, 1),
              roundB((totalLiab - currLiab) / exRate, 1), ")")
        print("E", roundB((totalAssets - totalLiab) / exRate, 1), "B")
        print("Tangible Equity", roundB(tangible_equity, 1), "B", bsCurrency,
              roundB(tangible_equity / exRate, 1), 'B', listingCurr)
        print("Market Cap", str(roundB(marketPrice * shares, 0)) + "B", listingCurr)

        # print("PER SHARE:")
        print("Market price", round(marketPrice, 1), listingCurr)
        print("Tangible Equity per share", round(tangible_equity / exRate / shares, 1), listingCurr)

        print("P/NetAssets", round(marketPrice * shares / (netAssets / exRate), 1))
        print("P/Tangible Equity", round(marketPrice * shares / (tangible_equity / exRate), 1))
        print("P/E", round(marketPrice * shares / (netIncome / exRate), 1))
        print("P/CFO", round(marketPrice * shares / (cfo / exRate), 1))
        print("S/B", round(revenue / tangible_equity, 1))
        print("                         ")
        print("********ALTMAN**********")
        print("CR", round(currRatio, 1))
        print("tangible ratio", round(tangible_equity / (totalAssets - totalLiab), 1))
        print("D/E", round(totalLiab / tangible_equity, 1))
        print("EBIT", roundB(ebit / exRate, 1), "B")
        print("netIncome", roundB(netIncome / exRate, 1), "B")
        print("CFO", roundB(cfo / exRate, 1), "B")
        print("CFI", roundB(cfi / exRate, 1), "B")
        print("CFF", roundB(cff / exRate, 1), "B")
        print("RE", roundB(retainedEarnings / exRate, 1), "B")
        print("RE/A", round(retainedEarnings / totalAssets, 1))
        print("S/A", round(revenue / totalAssets, 1))
        print("div1YrYld:", round(divLastYearYield * 100), "%")
        print("divAllYld:", round(divAllTimeYld * 100), "%")
        print("divsum marketprice:", round(divSumPastYear, 1), round(marketPrice, 2))
        print("P/CFO", round(marketCap / (cfo / exRate), 1))
        print('cfo/A', cfoA)

        outputString = stockName + " " + country.replace(' ', '') + " " + sector.replace(' ', '') \
                       + " dai$Vol:" + str(round(avgVolListingCurrency / 1000000)) + "M" \
                       + " MV:" + str(roundB(marketCap, 1)) + 'B' \
                       + " Tangible_equity:" + str(roundB((tangible_equity) / exRate, 1)) + 'B' \
                       + " pb:" + str(round(pTangibleEquity, 1)) \
                       + " CR:" + str(round(currRatio, 1)) \
                       + " D/E:" + str(round(debtEquityRatio, 1)) \
                       + " RE/A:" + str(round(retainedEarningsAssetRatio, 1)) \
                       + " cfo/A:" + str(round(cfoAssetRatio, 1)) \
                       + " ebit/A:" + str(round(ebitAssetRatio, 1)) \
                       + " tangibleRatio:" + str(round(tangibleRatio, 1)) \
                       + " 52w_p%:" + str(round(percentile)) \
                       + " divYldAll:" + str(round(divAllTimeYld * 100)) + "%" \
                       + " divYldLastYr:" + str(round(divLastYearYield * 100)) + "%"

        print(outputString)
        return outputString
    except Exception as e:
        print(e)
        print(data[-10:])
        print(stockName, "exception", e)
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)


getResults(stockName)
