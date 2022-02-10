import yahoo_fin.stock_info as si
import pandas as pd
from currency_scrapeYahoo import getBalanceSheetCurrency
from currency_scrapeYahoo import getListingCurrency
import currency_getExchangeRate
from helperMethods import getFromDF
from helperMethods import getInsiderOwnership

COUNT = 0


def increment():
    global COUNT
    COUNT = COUNT + 1
    return COUNT


START_DATE = '3/1/2020'
DIVIDEND_START_DATE = '1/1/2010'
PRICE_INTERVAL = '1mo'

exchange_rate_dict = currency_getExchangeRate.getExchangeRateDict()

fileOutput = open('list_results', 'w')

stock_df = pd.read_csv('list_companyInfo', sep="\t", index_col=False,
                       names=['ticker', 'name', 'sector', 'industry', 'country', 'mv', 'price'])

listStocks = stock_df[(stock_df['price'] > 1)
                      & (stock_df['sector'].str
                         .contains('financial|healthcare', regex=True, case=False) == False)
                      & (stock_df['industry'].str.contains('reit', regex=True, case=False) == False)
                      & (stock_df['country'].str.lower() != 'china')]['ticker'].tolist()

print(len(listStocks), listStocks)

for comp in listStocks:
    print(increment())
    try:
        marketPrice = si.get_live_price(comp)
        # if marketPrice < 1:
        #     print(comp, 'market price < 1: ', marketPrice)
        #     continue

        bs = si.get_balance_sheet(comp)
        totalCurrentAssets = getFromDF(bs.loc["totalCurrentAssets"])
        totalCurrentLiab = getFromDF(bs.loc["totalCurrentLiabilities"])
        currentRatio = totalCurrentAssets / totalCurrentLiab

        if currentRatio < 1:
            print(comp, "current ratio < 1", currentRatio)
            continue

        retainedEarnings = getFromDF(bs.loc["retainedEarnings"])

        if retainedEarnings < 0:
            print(comp, "retained earnings < 0", retainedEarnings)
            continue

        totalAssets = getFromDF(bs.loc["totalAssets"])
        totalLiab = getFromDF(bs.loc["totalLiab"])
        debtEquityRatio = totalLiab / (totalAssets - totalLiab)

        if debtEquityRatio > 1 or totalAssets < totalLiab:
            print(comp, "de ratio> 1 or negative equity", debtEquityRatio, totalAssets - totalLiab)
            continue

        incomeStatement = si.get_income_statement(comp, yearly=True)
        ebit = getFromDF(incomeStatement.loc["ebit"])
        netIncome = getFromDF(incomeStatement.loc['netIncome'])

        if ebit < 0 or netIncome < 0:
            print(comp, "ebit or net income < 0", ebit, netIncome)
            continue

        cf = si.get_cash_flow(comp)
        cfo = getFromDF(cf.loc["totalCashFromOperatingActivities"])

        if cfo < 0:
            print(comp, "cfo < 0 ", cfo)
            continue

        shares = si.get_quote_data(comp)['sharesOutstanding']
        marketCap = marketPrice * shares

        pCfo = marketCap / cfo
        if marketCap / cfo > 10:
            print(comp, "p/cfo>10", pCfo)
            continue

        equity = getFromDF(bs.loc["totalStockholderEquity"])
        bsCurr = getBalanceSheetCurrency(comp)
        listingCurr = getListingCurrency(comp)
        exRate = currency_getExchangeRate.getExchangeRate(exchange_rate_dict, listingCurr, bsCurr)

        pb = marketCap / (equity / exRate)
        pe = marketCap / (netIncome / exRate)

        if pb > 0.6:
            print(comp, 'pb > 0.6', pb)
            continue

        #
        revenue = getFromDF(incomeStatement.loc["totalRevenue"])

        retainedEarningsAssetRatio = retainedEarnings / totalAssets
        cfoAssetRatio = cfo / totalAssets
        ebitAssetRatio = ebit / totalAssets

        data = si.get_data(comp, start_date=START_DATE, interval=PRICE_INTERVAL)
        low_52 = data['low'].min()
        high_52 = data['high'].max()
        divs = si.get_dividends(comp, start_date=DIVIDEND_START_DATE)
        percentile = 100.0 * (marketPrice - low_52) / (high_52 - low_52)
        divSum = divs['dividend'].sum() if not divs.empty else 0

        # greenblatt
        roa = netIncome / totalAssets
        roaPB = roa / pb

        # neff
        divYield = divSum / 10 / marketPrice * 100
        divPB = divYield / pb

        # schloss
        insiderDic = getInsiderOwnership()
        insider = insiderDic[comp]
        schloss = insider > 10 and marketPrice < data['adjclose'].min() * 1.1

        outputString = comp + " " \
                       + stock_df[stock_df['ticker'] == comp][['country', 'sector']] \
                           .to_string(index=False, header=False) + " " \
                       + listingCurr + bsCurr \
                       + " MV:" + str(round(marketCap / 1000000000.0, 1)) + 'B' \
                       + " pCFO:" + str(round(pCfo, 1)) \
                       + " pb:" + str(round(pb, 1)) \
                       + " PE:" + str(round(pe, 1)) \
                       + " CR:" + str(round(currentRatio, 1)) \
                       + " D/E:" + str(round(debtEquityRatio, 1)) \
                       + " roaPB:" + str(round(roaPB, 2)) \
                       + " divPB:" + str(round(divPB, 2)) \
                       + " insiderOwns:" + str(round(insider, 2)) \
                       + " p/52wk low:" + str(round(marketPrice / low_52, 2))

        print(outputString)
        fileOutput.write(outputString + '\n')
        fileOutput.flush()

    except Exception as e:
        print(comp, "exception", e)
