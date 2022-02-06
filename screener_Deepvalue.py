import yahoo_fin.stock_info as si

from currency_scrapeYahoo import getBalanceSheetCurrency
from currency_scrapeYahoo import getListingCurrency
import currency_getExchangeRate
from helperMethods import getFromDF

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
fileOutput.write("\n")

import pandas as pd

stock_df = pd.read_csv('list_companyInfo', sep="\t", index_col=False,
                       names=['ticker', 'name', 'sector', 'industry', 'country', 'mv', 'price'])

listStocks = stock_df[(stock_df['price'] > 1)
                      & (stock_df['sector'].str
                         .contains('financial|healthcare', regex=True, case=False) == False)
                      & (stock_df['industry'].str.contains('reit', regex=True, case=False) == False)
                      & (stock_df['country'].str.lower() != 'china')]['ticker'].tolist()

print(listStocks.__len__(), listStocks)
# with open("list_usTickerAll", "r") as file:
#     lines = file.read().rstrip().splitlines()

for comp in listStocks:
    print(increment())
    try:
        marketPrice = si.get_live_price(comp)
        if marketPrice < 1:
            print(comp, 'market price < 1: ', marketPrice)
            continue

        info = si.get_company_info(comp)
        if info.loc["country"][0].lower() == "china":
            print(comp, "no china")
            continue

        bs = si.get_balance_sheet(comp)
        totalCurrentAssets = getFromDF(bs.loc["totalCurrentAssets"])
        totalCurrentLiab = getFromDF(bs.loc["totalCurrentLiabilities"])
        currentRatio = totalCurrentAssets / totalCurrentLiab

        if currentRatio < 1:
            print(comp, "current ratio < 1")
            continue

        retainedEarnings = getFromDF(bs.loc["retainedEarnings"])

        if retainedEarnings < 0:
            print(comp, " retained earnings < 0 ", retainedEarnings)
            continue

        totalAssets = getFromDF(bs.loc["totalAssets"])
        totalLiab = getFromDF(bs.loc["totalLiab"])
        debtEquityRatio = totalLiab / (totalAssets - totalLiab)

        if debtEquityRatio > 1:
            print(comp, " de ratio> 1. ", debtEquityRatio)
            continue

        incomeStatement = si.get_income_statement(comp, yearly=True)
        ebit = getFromDF(incomeStatement.loc["ebit"])
        netIncome = getFromDF(incomeStatement.loc['netIncome'])

        if ebit < 0 or netIncome < 0:
            print(comp, "ebit or net income < 0 ", ebit, " ", netIncome)
            continue

        cf = si.get_cash_flow(comp)
        cfo = getFromDF(cf.loc["totalCashFromOperatingActivities"])

        if cfo < 0:
            print(comp, "cfo < 0 ", cfo)
            continue

        equity = getFromDF(bs.loc["totalStockholderEquity"])
        shares = si.get_quote_data(comp)['sharesOutstanding']

        bsCurrency = getBalanceSheetCurrency(comp)
        listingCurrency = getListingCurrency(comp)
        exRate = currency_getExchangeRate.getExchangeRate(exchange_rate_dict,
                                                          listingCurrency, bsCurrency)

        marketCap = marketPrice * shares
        pb = marketCap / (equity / exRate)
        pe = marketCap / (netIncome / exRate)

        if pb > 1:
            print(comp, ' pb > 1', pb)
            continue

        if pe > 10 or pe < 0:
            print(comp, ' pe > 10 or < 0')
            continue

        revenue = getFromDF(incomeStatement.loc["totalRevenue"])

        retainedEarningsAssetRatio = retainedEarnings / totalAssets
        cfoAssetRatio = cfo / totalAssets
        ebitAssetRatio = ebit / totalAssets

        data = si.get_data(comp, start_date=START_DATE, interval=PRICE_INTERVAL)
        divs = si.get_dividends(comp, start_date=DIVIDEND_START_DATE)
        percentile = 100.0 * (data['adjclose'][-1] - data['adjclose'].min()) / (
                data['adjclose'].max() - data['adjclose'].min())
        divSum = divs['dividend'].sum() if not divs.empty else 0

        outputString = comp + " " + info.loc["country"][0].replace(" ", "_")[0:3] + " " \
                       + info.loc['sector'][0].replace(" ", "_")[0:3] + " " \
                       + listingCurrency + bsCurrency \
                       + " MV:" + str(round(marketCap / 1000000000.0, 1)) + 'B' \
                       + " PE " + str(round(pe, 1)) \
                       + " Eq:" + str(round((totalAssets - totalLiab) / exRate / 1000000000.0, 1)) + 'B' \
                       + " CR:" + str(round(currentRatio, 1)) \
                       + " D/E:" + str(round(debtEquityRatio, 1)) \
                       + " RE/A:" + str(round(retainedEarningsAssetRatio, 1)) \
                       + " cfo/A:" + str(round(cfoAssetRatio, 1)) \
                       + " ebit/A:" + str(round(ebitAssetRatio, 1)) \
                       + " S/A " + str(round(revenue / totalAssets)) \
                       + " pb:" + str(round(pb, 1)) \
                       + " 52w p%: " + str(round(percentile)) \
                       + " div10yr: " + str(round(divSum / marketPrice, 2))

        print(outputString)
        fileOutput.write(outputString + '\n')
        fileOutput.flush()

    except Exception as e:
        print(comp, "exception", e)
