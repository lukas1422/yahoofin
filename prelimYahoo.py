import pandas as pd

stockName = '1317.HK'
# yearlyFlag = False
yearlyFlag = 'yearly'

import statistics
import os
import sys
from datetime import datetime, timedelta
# import yahoo_fin.stock_info as si
from currency_scrapeYahoo import getBalanceSheetCurrency
from currency_scrapeYahoo import getListingCurrency
import currency_getExchangeRate
import scrape_sharesOutstanding
from helperMethods import getFromDF, getFromDFYearly, roundB
import yfinance as yf

ONE_YEAR_AGO = datetime.today() - timedelta(weeks=53)
# ONE_YEAR_AGO = pd.to_datetime('today').floor('D') - pd.Timedelta(53, unit='W')
print(ONE_YEAR_AGO)
# yearAgo = datetime.today() - timedelta(weeks=53)
# START_DATE = (datetime.today() - timedelta(weeks=52 * 10)).strftime('%-m/%-d/%Y')
PRICE_INTERVAL = '1wk'


def getResults(stockName):
    exchange_rate_dict = currency_getExchangeRate.getExchangeRateDict()
    try:
        stockYF = yf.Ticker(stockName)
        # priceData = si.get_data(stockName, interval=PRICE_INTERVAL)
        priceData = stockYF.history(period='max', interval=PRICE_INTERVAL)
        priceData = priceData.set_index(priceData.index.map(lambda x: x.replace(tzinfo=None).to_pydatetime()))
        #priceData['Date']=priceData.index
        #priceData = priceData.set_index(priceData['Date'].dt.date)
        #priceData = priceData.set_index(pd.to_datetime(priceData.index))

        print('last trading day', priceData[priceData['Volume'] != 0].index[-1].strftime('%Y/%-m/%-d'))

        # avgVolListingCurrency = (priceData[-10:]['close'] * priceData[-10:]['volume']).sum() / 10
        medianVol = statistics.median(priceData[-10:]['Close'] * priceData[-10:]['Volume']) / 5

        # print('data', data[-10:])
        # print('mean median', avgVolListingCurrency, medianVol)
        # print(' avg vol ', str(round(avgVolListingCurrency / 1000000, 1)) + "M")

        try:
            # info = si.get_company_info(stockName)
            info = stockYF.info
            # insiderPerc = float(si.get_holders(stockName).get('Major Holders')[0][0].rstrip("%"))
            insiderPerc = float(stockYF.get_major_holders()[0][0].rstrip("%"))

            print(stockName, "insider percent", insiderPerc)
        except Exception as e:
            print(e)
            print(priceData[-10:])
            info = ""
            print(stockName, "exception", e)
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)

        # country = getFromDF(info, "country")
        # sector = getFromDF(info, 'sector')
        # industry = getFromDF(info, 'industry')
        # longName = getFromDF(info, 'longBusinessSummary')
        #
        country = info["country"]
        sector = info['sector']
        industry = info['industry']
        longName = info['longBusinessSummary']

        # insiderPerc = float(si.get_holders(stockName).get('Major Holders')[0][0].rstrip("%"))
        # print(stockName, country, sector, industry, insiderPerc)

        print(longName)

        # bs = si.get_balance_sheet(stockName, yearly=yearlyFlag)
        # bs = stockYF.get_balance_sheet(freq=yearlyFlag)
        bs = stockYF.balance_sheet
        print("balance sheet date:", bs.columns[0].strftime('%Y/%-m/%-d'))
        # print("bs cols", bs.columns)

        # retainedEarnings = getFromDF(bs, "retainedEarnings")
        # total_CA = getFromDF(bs, "totalCurrentAssets")
        # currLiab = getFromDF(bs, "totalCurrentLiabilities")
        #
        # totalAssets = getFromDF(bs, "totalAssets")
        # totalLiab = getFromDF(bs, "totalLiab")
        # intangibles = getFromDF(bs, 'intangibleAssets')
        # goodWill = getFromDF(bs, 'goodWill')

        retainedEarnings = getFromDF(bs, "Retained Earnings")
        total_CA = getFromDF(bs, "Current Assets")
        currLiab = getFromDF(bs, "Current Liabilities")

        totalAssets = getFromDF(bs, "Total Assets")
        totalLiab = getFromDF(bs, "Total Liabilities Net Minority Interest")
        intangibles = getFromDF(bs, 'Other Intangible Assets')
        goodWill = getFromDF(bs, 'Goodwill')

        print('goodwill', goodWill, round(goodWill / totalAssets * 100), "%", 'intangibles', intangibles,
              round(intangibles / totalAssets * 100), "%")

        netAssets = totalAssets - totalLiab
        tangible_equity = totalAssets - totalLiab - goodWill - intangibles
        cash = getFromDF(bs, 'Cash And Cash Equivalents')
        receivables = getFromDF(bs, 'Accounts Receivable')
        inventory = getFromDF(bs, 'Inventory')

        listingCurr = getListingCurrency(stockName)
        bsCurrency = getBalanceSheetCurrency(stockName, listingCurr)
        exRate = currency_getExchangeRate.getExchangeRate(exchange_rate_dict, listingCurr, bsCurrency)

        currRatio = (cash + receivables * 0.8 + inventory * 0.5) / currLiab

        # incomeStatement = si.get_income_statement(stockName, yearly=yearlyFlag)
        incomeStatement = stockYF.income_stmt
        print("income statement date:", incomeStatement.columns[0].strftime('%Y/%-m/%-d'))

        revenue = getFromDFYearly(incomeStatement, "Total Revenue", True)
        ebit = getFromDFYearly(incomeStatement, "Operating Income", True)
        netIncome = getFromDFYearly(incomeStatement, 'Net Income', True)

        # cf = si.get_cash_flow(stockName, yearly=yearlyFlag)
        cf = stockYF.cashflow
        print("cash flow statement date:", cf.columns[0].strftime('%Y/%-m/%-d'))

        cfo = getFromDFYearly(cf, "Operating Cash Flow", True)
        cfi = getFromDFYearly(cf, "Investing Cash Flow", True)
        cff = getFromDFYearly(cf, "Financing Cash Flow", True)
        dep = getFromDFYearly(cf, "Depreciation And Amortization", yearlyFlag)
        capex = getFromDFYearly(cf, "Capital Expenditure", yearlyFlag)

        print('cfo', roundB(cfo, 1), 'B')

        cfoA = cfo / totalAssets

        marketCapLast = stockYF.info['marketCap']
        marketPrice = stockYF.info['currentPrice']
        shares = stockYF.info['sharesOutstanding']
        print("yahoo shares ", shares)
        impliedShares = marketCapLast / marketPrice
        print("implied shares ", impliedShares)
        print("share diff", shares / impliedShares)

        if bsCurrency == 'CNY' and listingCurr != 'USD':
            sharesTotalXueqiu = scrape_sharesOutstanding.scrapeTotalSharesXueqiu(stockName)
            floatingSharesXueqiu = scrape_sharesOutstanding.scrapeFloatingSharesXueqiu(stockName)
            print('floating shares xiuqiu', floatingSharesXueqiu)
            sharesFinviz = scrape_sharesOutstanding.scrapeSharesOutstandingFinviz(stockName)
            print('xueqiu total shares', sharesTotalXueqiu)
            # print('xueqiu floating shares', roundB(floatingSharesXueqiu, 1))
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

        divs = stockYF.dividends.to_frame()
        # print('div', divs)
        # divsPastYear = divs.loc[divs.index > ONE_YEAR_AGO]
        # divSumPastYear = divsPastYear['dividend'].sum() if not divsPastYear.empty else 0
        # divLastYearYield = divSumPastYear / marketPrice
        # print('div past year yield', divLastYearYield)
        #
        # divSumAll = divs['dividend'].sum() if not divs.empty else 0
        # startToNow = (datetime.today() - data.index[0]).days / 365.25
        # print("Years Since Listing:", round(startToNow), 'starting date ', data.index[0].strftime('%Y/%-m/%-d'))
        # divAllTimeYld = divSumAll / startToNow / marketPrice
        # print('div all time yld ', divAllTimeYld)

        divYieldAll = 0
        div2021Yld = 0
        if not divs.empty:
            yearSpan = 2021 - priceData[:1].index.item().year + 1
            divPrice = pd.merge(divs.groupby(by=lambda d: d.year)['Dividends'].sum(),
                                priceData.groupby(by=lambda d: d.year)['Close'].mean(),
                                left_index=True, right_index=True)
            divPrice['yield'] = divPrice['Dividends'] / divPrice['Close']
            divYieldAll = divPrice[divPrice.index != 2022]['yield'].sum() / yearSpan \
                if not divPrice[divPrice.index != 2022].empty else 0
            div2021Yld = divPrice.loc[2021]['yield'] if 2021 in divPrice.index else 0
            # print('yield all', divYieldAll, 'lastyear', div2021Yld)
        # priceData.index = pd.to_datetime(priceData.index)
        data52w = priceData.loc[priceData.index > ONE_YEAR_AGO]
        percentile = 100.0 * (marketPrice - data52w['Low'].min()) / (data52w['High'].max() - data52w['Low'].min())
        # print('div history ', divs) if not divs.empty else print('div is empty ')

        # PRINTING*****
        print("listing Currency:", listingCurr, "bs currency:", bsCurrency, "ExRate:", exRate)

        print("********* FINANCIALS *********")

        print("current ratio components cash", bsCurrency, roundB(cash, 1), 'rec', roundB(receivables, 1), 'inv',
              roundB(inventory, 1), 'currL', roundB(currLiab, 1))

        print("cash", listingCurr, roundB(cash / exRate, 1), "rec", roundB(receivables / exRate, 1), "inv",
              roundB(inventory / exRate, 1))

        print("A", roundB(totalAssets / exRate, 1), "B", "(",
              roundB(total_CA / exRate, 1)
              , roundB((totalAssets - total_CA) / exRate, 1), ")")
        print("L", roundB(totalLiab / exRate, 1), "B", "(",
              roundB(currLiab / exRate, 1),
              roundB((totalLiab - currLiab) / exRate, 1), ")")
        print("E", roundB((totalAssets - totalLiab) / exRate, 1), "B")
        print("Tangible Equity", roundB(tangible_equity, 1), "B", bsCurrency,
              roundB(tangible_equity / exRate, 1), 'B', listingCurr)
        print("Market Cap", str(roundB(marketPrice * shares, 2)) + "B", listingCurr)

        # print("PER SHARE:")
        print("Market price", round(marketPrice, 2), listingCurr)
        print("Tangible Equity per share", round(tangible_equity / exRate / shares, 1), listingCurr)

        print("P/NetAssets", round(marketPrice * shares / (netAssets / exRate), 1))
        print("P/Tangible Equity", round(marketPrice * shares / (tangible_equity / exRate), 1))
        print("P/E", round(marketCapLast * exRate / netIncome, 1))
        print("P/FCF", round(marketCapLast * exRate / (cfo - dep), 1))
        print('marketcap, exrate, cfo, dep', marketCapLast, exRate, cfo, dep)
        print("Dep/CFO", round(dep / cfo, 1))
        print("Capex/CFO", round(capex / cfo, 1))
        print("S/B", round(revenue / tangible_equity, 1))
        print("                         ")
        print("********ALTMAN**********")
        print("CR", round(currRatio, 1))
        print("tangible ratio", round(tangible_equity / (totalAssets - totalLiab), 1))
        print("D/E", round(totalLiab / tangible_equity, 1))
        print("EBIT", roundB(ebit / exRate, 1), "B")
        print("netIncome", roundB(netIncome / exRate, 1), "B")
        print("CFO", roundB(cfo / exRate, 1), "B")
        print("DEP", roundB(dep / exRate, 1), "B")
        print("CAPEX", roundB(capex / exRate, 1), "B")
        print("CFI", roundB(cfi / exRate, 1), "B")
        print("CFF", roundB(cff / exRate, 1), "B")
        print("RE", roundB(retainedEarnings / exRate, 1), "B")
        print("RE/A", round(retainedEarnings / totalAssets, 1))
        print("S/A", round(revenue / totalAssets, 1))
        print("divYld2021:", round(div2021Yld * 100), "%")
        print("divYldAll:", round(divYieldAll * 100), "%")
        # print("divsum marketprice:", round(divSumPastYear, 1), round(marketPrice, 2))
        print('cfo/A', cfoA)

        outputString = stockName + " " + country.replace(' ', '') + " " + sector.replace(' ', '') \
                       + " dai$Vol:" + str(round(medianVol / 1000000)) + "M" \
                       + " MV:" + str(roundB(marketCapLast, 1)) + 'B' \
                       + " Tangible_equity:" + str(roundB((tangible_equity) / exRate, 1)) + 'B' \
                       + " P/FCF:" + str(round(marketCapLast * exRate / (cfo - dep), 1)) \
                       + " pb:" + str(round(pTangibleEquity, 1)) \
                       + " CR:" + str(round(currRatio, 1)) \
                       + " D/E:" + str(round(debtEquityRatio, 1)) \
                       + " RE/A:" + str(round(retainedEarningsAssetRatio, 1)) \
                       + " cfo/A:" + str(round(cfoAssetRatio, 1)) \
                       + " ebit/A:" + str(round(ebitAssetRatio, 1)) \
                       + " tangibleRatio:" + str(round(tangibleRatio, 1)) \
                       + " 52w_p%:" + str(round(percentile)) \
                       + " divYldAll:" + str(round(divYieldAll * 100)) + "%" \
                       + " divYld2021:" + str(round(div2021Yld * 100)) + "%"

        print(outputString)
        return outputString
    except Exception as e:
        print(e)
        # print(data[-10:])
        print(stockName, "exception", e)
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)


getResults(stockName)
