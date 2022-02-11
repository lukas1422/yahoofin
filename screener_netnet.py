import yahoo_fin.stock_info as si
import pandas as pd
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

fileOutput = open('list_results_netnet', 'w')

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
        bs = si.get_balance_sheet(comp)
        currentAssets = getFromDF(bs.loc["totalCurrentAssets"]) \
            if 'totalCurrentAssets' in bs.index else 0.0

        totalLiab = getFromDF(bs.loc["totalLiab"]) \
            if 'totalLiab' in bs.index else 0.0

        if currentAssets < totalLiab:
            print(comp, " current assets < total liab",
                  round(currentAssets / 1000000000, 2), round(totalLiab / 1000000000, 2))
            continue

        cash = getFromDF(bs.loc['cash']) if 'cash' in bs.index else 0.0
        receivables = getFromDF(bs.loc['netReceivables']) if 'netReceivables' in bs.index else 0.0
        inventory = getFromDF(bs.loc['inventory']) if 'inventory' in bs.index else 0.0

        marketPrice = si.get_live_price(comp)
        shares = si.get_quote_data(comp)['sharesOutstanding']
        marketCap = marketPrice * shares

        bsCurr = getBalanceSheetCurrency(comp)
        listingCurr = getListingCurrency(comp)
        exRate = currency_getExchangeRate.getExchangeRate(exchange_rate_dict, listingCurr, bsCurr)

        if (currentAssets - totalLiab) / exRate < marketCap:
            print(comp, listingCurr, bsCurr,
                  'current assets - total liab < mv. CA L MV:',
                  round(currentAssets / 1000000000, 2),
                  round(totalLiab / 1000000000, 2),
                  round(marketCap / 1000000000, 2))
            continue

        outputString = ""

        if (cash - totalLiab) / exRate > marketCap:
            outputString = "cash netnet:" + comp + " " \
                           + listingCurr + bsCurr \
                           + " cash:" + str(round(cash / 1000000000, 2)) \
                           + " L:" + str(round(totalLiab / 1000000000, 2))

        elif (cash + receivables * 0.8 - totalLiab) / exRate > marketCap:
            outputString = "cash receivable netnet:" + comp + " "

        elif (cash + receivables * 0.8 + inventory * 0.5 - totalLiab) / exRate > marketCap:
            outputString = "cash rec inv netnet " + comp

        elif (currentAssets - totalLiab) / exRate > marketCap:
            outputString = 'currentAsset netnet ' + comp

        else:
            outputString = 'undefined net net, check' + comp

        outputString = outputString + " " + listingCurr + bsCurr \
                       + " cash:" + str(round(cash / 1000000000, 2)) \
                       + " rec:" + str(round(receivables / 1000000000, 2)) \
                       + " inv:" + str(round(inventory / 1000000000, 2)) \
                       + " CA:" + str(round(currentAssets / 1000000000, 2)) \
                       + " L:" + str(round(totalLiab / 1000000000, 2)) \
                       + " mv:" + str(round(marketCap / 1000000000, 2))

        print(outputString)

        fileOutput.write(outputString + "mv:" + str(round(marketCap / 1000000000, 2)) + '\n')
        fileOutput.flush()


    except Exception as e:
        print(comp, "exception", e)
